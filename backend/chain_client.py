"""
chain_client.py — Portaldot chain READ operations via substrate-interface.

All WRITE operations (extrinsic signing + submission) are handled in the
frontend using @polkadot/api + the user's wallet extension. This module
only performs read-only queries and constructs call parameters for the
frontend to use.

POT precision: 14 decimals (1 POT = 10^14 planck).
"""

import os
import logging
from typing import Optional
import requests as _http
from substrateinterface import SubstrateInterface
from substrateinterface.utils.ss58 import ss58_encode

logger = logging.getLogger(__name__)

# POT token has 14 decimal places (not the usual 18)
POT_DECIMALS = 14
PLANCK_PER_POT = 10 ** POT_DECIMALS

# Maximum block range for transaction history scan.
# Each block requires one RPC call; keep this small for local demo nodes.
TX_HISTORY_BLOCK_RANGE = 200


# Substrate 2.x (Portaldot) requires explicit type definitions
# because the chain uses Metadata V13 with old type names
PORTALDOT_TYPES = {
    # Portaldot AccountInfo: nonce(4) + consumers(4) + providers(4) + sufficients(4) + data(64) = 80 bytes
    "AccountInfo": {
        "type": "struct",
        "type_mapping": [
            ["nonce", "u32"],
            ["consumers", "u32"],
            ["providers", "u32"],
            ["sufficients", "u32"],
            ["data", "AccountData"],
        ],
    },
    "AccountData": {
        "type": "struct",
        "type_mapping": [
            ["free", "u128"],
            ["reserved", "u128"],
            ["miscFrozen", "u128"],
            ["feeFrozen", "u128"],
        ],
    },
    "Weight": "u64",
    # Address types used in extrinsic parameters (Substrate 2.x)
    "LookupSource": "AccountId",
    "Address": "AccountId",
    "ValidatorId": "AccountId",
    "AuthorityId": "AccountId",
    "DispatchResult": {
        "type": "enum",
        "value_list": {"Ok": "Null", "Err": "DispatchError"},
    },
    # Event-scanning types required by SubstrateNodeExtension
    "Phase": {
        "type": "enum",
        "type_mapping": [
            ["ApplyExtrinsic", "u32"],
            ["Finalization", "Null"],
            ["Initialization", "Null"],
        ],
    },
    "EventRecord": {
        "type": "struct",
        "type_mapping": [
            ["phase", "Phase"],
            ["event", "Event"],
            ["topics", "Vec<Hash>"],
        ],
    },
    "EventIndex": "u32",
    "RefCount": "u32",
    "ExtrinsicMetadata": {
        "type": "struct",
        "type_mapping": [
            ["version", "u8"],
            ["signed_extensions", "Vec<Text>"],
        ],
    },
}


def _get_substrate() -> SubstrateInterface:
    """Create a new SubstrateInterface connection with Portaldot V13 type definitions."""
    url = os.getenv("PORTALDOT_WS_URL", "wss://mainnet.portaldot.io")
    substrate = SubstrateInterface(
        url=url,
        ss58_format=42,
        type_registry={"types": PORTALDOT_TYPES},
    )
    return substrate


def planck_to_pot(planck: int) -> float:
    """Convert planck (smallest unit) to POT. 1 POT = 10^14 planck."""
    return planck / PLANCK_PER_POT


def pot_to_planck(pot: float) -> int:
    """Convert POT to planck. 1 POT = 10^14 planck."""
    return int(pot * PLANCK_PER_POT)


def query_balance(address: str) -> dict:
    """
    Query free, reserved, and total POT balance for an address.

    Returns:
        {
            "address": str,
            "free_pot": float,
            "reserved_pot": float,
            "total_pot": float,
            "free_planck": int,
        }
    """
    substrate = _get_substrate()
    try:
        result = substrate.query("System", "Account", [address])
        data = result.value["data"]
        free_planck = data["free"]
        reserved_planck = data["reserved"]
        total_planck = free_planck + reserved_planck
        return {
            "address": address,
            "free_pot": planck_to_pot(free_planck),
            "reserved_pot": planck_to_pot(reserved_planck),
            "total_pot": planck_to_pot(total_planck),
            "free_planck": free_planck,
        }
    finally:
        substrate.close()


def estimate_transfer_fee(from_address: str, to_address: str, amount_pot: float) -> dict:
    """
    Estimate the POT gas fee for a balance transfer.

    Portaldot runs Substrate 2.x with Metadata V13, which does not support
    the payment.queryInfo RPC used by newer chains. We skip that call entirely
    and return a conservative fixed estimate (~0.001 POT) to avoid a guaranteed
    round-trip failure on every request.
    """
    # Portaldot Substrate 2.x does not support payment.queryInfo — fixed estimate only.
    fixed_planck = pot_to_planck(0.001)
    return {
        "estimated_fee_pot": 0.001,
        "estimated_fee_planck": fixed_planck,
        "is_fixed_estimate": True,
    }


def build_transfer_call_params(to_address: str, amount_pot: float) -> dict:
    """
    Build the extrinsic call parameters for a balance transfer.
    These parameters are sent to the frontend, which assembles and signs the extrinsic.

    Returns:
        {
            "call_module": str,
            "call_function": str,
            "call_params": dict,
            "amount_planck": int,
            "amount_pot": float,
        }
    """
    amount_planck = pot_to_planck(amount_pot)
    return {
        "call_module": "Balances",
        "call_function": "transfer_keep_alive",
        "call_params": {
            "dest": to_address,
            "value": amount_planck,
        },
        "amount_planck": amount_planck,
        "amount_pot": amount_pot,
    }


def query_validators(limit: int = 20) -> dict:
    """
    Query active validators from the Staking pallet.

    Returns:
        {
            "validators": [{"address": str, "commission_pct": float}, ...],
            "total_count": int,
        }
    """
    substrate = _get_substrate()
    try:
        # Get current active validators
        validators_result = substrate.query("Session", "Validators")
        validator_addresses = validators_result.value or []

        validators = []
        for addr in validator_addresses[:limit]:
            try:
                prefs = substrate.query("Staking", "Validators", [addr])
                commission_perthousand = prefs.value.get("commission", 0)
                # Commission is stored as parts per billion (1_000_000_000 = 100%)
                commission_pct = commission_perthousand / 10_000_000
            except Exception:
                commission_pct = 0.0
            validators.append({
                "address": addr,
                "commission_pct": round(commission_pct, 2),
            })

        return {
            "validators": validators,
            "total_count": len(validator_addresses),
        }
    finally:
        substrate.close()


def _read_compact(data: bytes, pos: int):
    """
    Decode a SCALE compact-encoded integer.

    Big-integer mode (mode=3): the upper 6 bits encode (n - 4), where n is the
    number of following bytes. So actual byte count = (upper_6_bits) + 4.
    Example: compact(10^14) = [0x0b, 0x00, 0x40, 0x7a, 0x10, 0xf3, 0x5a]
      0x0b >> 2 = 2, n = 2 + 4 = 6 bytes → value = 100_000_000_000_000
    """
    mode = data[pos] & 0x03
    if mode == 0:
        return data[pos] >> 2, pos + 1
    elif mode == 1:
        return (data[pos] | data[pos + 1] << 8) >> 2, pos + 2
    elif mode == 2:
        return (data[pos] | data[pos+1]<<8 | data[pos+2]<<16 | data[pos+3]<<24) >> 2, pos + 4
    else:
        n = (data[pos] >> 2) + 4   # big-int: byte_count = upper_6_bits + 4
        return int.from_bytes(data[pos + 1:pos + 1 + n], "little"), pos + 1 + n


def _decode_transfer_extrinsic(hex_str: str) -> Optional[dict]:
    """
    Manually decode a Substrate 2.x signed extrinsic and extract transfer info.

    Portaldot uses Metadata V13. The newer substrate-interface GenericExtrinsic
    decoder requires Metadata V14's portable_registry and cannot decode V13
    extrinsics. This manual decoder handles the known Substrate 2.x format:

        [compact_length][version][multiaddr_prefix][AccountId(32)][sig_prefix][sig(64)]
        [era][nonce_compact][tip_compact][pallet_idx][call_idx][dest_prefix][dest(32)][amount_compact]

    Balances pallet index on Portaldot dev chain = 6.
    Call indices: 0=transfer, 3=transfer_keep_alive.
    """
    try:
        raw = bytes.fromhex(hex_str.lstrip("0x"))
        pos = 0

        _, pos = _read_compact(raw, pos)        # compact length (skip)
        ver = raw[pos]; pos += 1                # version byte
        if not (ver & 0x80):
            return None                         # unsigned extrinsic (e.g. timestamp)

        pos += 1                                # MultiAddress prefix byte (0x00 = AccountId)
        from_bytes = raw[pos:pos + 32]; pos += 32  # sender AccountId
        pos += 1                                # MultiSignature type prefix
        pos += 64                               # 64-byte signature

        # Extra: era (1 or 2 bytes), nonce (compact), tip (compact)
        pos += 2 if raw[pos] != 0x00 else 1
        _, pos = _read_compact(raw, pos)
        _, pos = _read_compact(raw, pos)

        pallet_idx = raw[pos]; call_idx = raw[pos + 1]; pos += 2

        # Only interested in Balances pallet (index 6) transfer calls (0 or 3)
        if pallet_idx != 6 or call_idx not in (0, 3):
            return None

        pos += 1                                # dest MultiAddress prefix
        dest_bytes = raw[pos:pos + 32]; pos += 32
        amount_planck, _ = _read_compact(raw, pos)

        return {
            "from": ss58_encode(from_bytes, ss58_format=42),
            "to":   ss58_encode(dest_bytes, ss58_format=42),
            "amount_planck": amount_planck,
        }
    except Exception:
        return None


_HTTP_BATCH_SIZE = 30   # max requests per HTTP batch (node limit)


def _http_batch_rpc(method: str, params_list: list) -> list:
    """
    Send batch JSON-RPC requests over HTTP, chunked to avoid node limits.
    Substrate nodes expose HTTP JSON-RPC at port 9933 by default.
    Returns results in the same order as params_list.
    """
    http_url = os.getenv("PORTALDOT_HTTP_URL", "http://127.0.0.1:9933")
    results = []
    for chunk_start in range(0, len(params_list), _HTTP_BATCH_SIZE):
        chunk = params_list[chunk_start:chunk_start + _HTTP_BATCH_SIZE]
        batch = [
            {"id": i, "jsonrpc": "2.0", "method": method, "params": p}
            for i, p in enumerate(chunk)
        ]
        resp = _http.post(http_url, json=batch, timeout=15)
        resp.raise_for_status()
        raw = resp.text.strip()
        if not raw:
            results.extend([None] * len(chunk))
            continue
        by_id = {r["id"]: r.get("result") for r in resp.json()}
        results.extend(by_id.get(i) for i in range(len(chunk)))
    return results


def query_tx_history(address: str, limit: int = 20) -> dict:
    """
    Query recent transfer transactions involving an address by scanning extrinsics.

    Uses HTTP batch JSON-RPC to fetch all block hashes and blocks in just
    2 round trips (one batch for hashes, one for blocks), instead of the
    previous approach of 2 serial WebSocket calls per block.

    SubstrateNodeExtension.filter_events() was replaced because it cannot
    decode Portaldot's Metadata V13 event types (Phase, DispatchInfo, etc.).

    Returns:
        {
            "transactions": [{"block", "from", "to", "amount_pot", "direction"}],
            "scanned_blocks": int,
        }
    """
    substrate = _get_substrate()
    try:
        block_end = substrate.get_block_number(substrate.get_chain_head())
        scan_range = min(TX_HISTORY_BLOCK_RANGE, block_end)
        block_start = max(1, block_end - scan_range)

        block_numbers = list(range(block_end, block_start - 1, -1))

        # Round-trip 1: fetch all block hashes in one batch
        hashes = _http_batch_rpc("chain_getBlockHash", [[n] for n in block_numbers])

        # Round-trip 2: fetch all blocks in one batch
        blocks = _http_batch_rpc("chain_getBlock", [[h] for h in hashes if h])

        transactions = []
        for block_num, block_data in zip(block_numbers, blocks):
            if block_data is None:
                continue
            extrinsics = block_data.get("block", {}).get("extrinsics", [])
            for ext_hex in extrinsics[1:]:   # skip [0] = timestamp
                tx = _decode_transfer_extrinsic(ext_hex)
                if tx is None:
                    continue
                if tx["from"] == address or tx["to"] == address:
                    transactions.append({
                        "block": block_num,
                        "from": tx["from"],
                        "to":   tx["to"],
                        "amount_pot": planck_to_pot(tx["amount_planck"]),
                        "direction": "out" if tx["from"] == address else "in",
                    })

        transactions.sort(key=lambda x: x["block"], reverse=True)
        return {
            "transactions": transactions[:limit],
            "scanned_blocks": scan_range,
        }
    finally:
        substrate.close()
