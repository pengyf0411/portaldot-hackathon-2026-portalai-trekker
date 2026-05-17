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
from substrateinterface import SubstrateInterface
from substrateinterface import SubstrateNodeExtension

logger = logging.getLogger(__name__)

# POT token has 14 decimal places (not the usual 18)
POT_DECIMALS = 14
PLANCK_PER_POT = 10 ** POT_DECIMALS

# Maximum block range for transaction history scan (SubstrateNodeExtension is slow)
TX_HISTORY_BLOCK_RANGE = 1000


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
    Falls back to a fixed estimate if payment.queryInfo is not supported (old chains).
    """
    substrate = _get_substrate()
    try:
        from substrateinterface import Keypair
        dummy_keypair = Keypair(ss58_address=from_address)
        amount_planck = pot_to_planck(amount_pot)
        call = substrate.compose_call(
            call_module="Balances",
            call_function="transfer_keep_alive",
            call_params={"dest": to_address, "value": amount_planck},
        )
        payment_info = substrate.get_payment_info(call=call, keypair=dummy_keypair)
        fee_planck = payment_info["partialFee"]
        return {
            "estimated_fee_pot": planck_to_pot(fee_planck),
            "estimated_fee_planck": fee_planck,
        }
    except Exception as e:
        logger.warning(f"Fee estimation via payment.queryInfo failed ({e}), using fixed estimate")
        # Portaldot Substrate 2.x may not support payment.queryInfo
        # Use a conservative fixed estimate: ~0.001 POT
        fixed_planck = pot_to_planck(0.001)
        return {
            "estimated_fee_pot": 0.001,
            "estimated_fee_planck": fixed_planck,
        }
    finally:
        substrate.close()


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


def query_tx_history(address: str, limit: int = 20) -> dict:
    """
    Query recent transfer events involving an address.
    Scans only the last TX_HISTORY_BLOCK_RANGE blocks to avoid timeout.

    Returns:
        {
            "transactions": [
                {
                    "block": int,
                    "from": str,
                    "to": str,
                    "amount_pot": float,
                    "direction": "in" | "out",
                }
            ],
            "scanned_blocks": int,
        }
    """
    substrate = _get_substrate()
    try:
        substrate.register_extension(SubstrateNodeExtension(max_block_range=TX_HISTORY_BLOCK_RANGE))

        block_end = substrate.get_block_number(substrate.get_chain_head())
        block_start = max(0, block_end - TX_HISTORY_BLOCK_RANGE)

        events = substrate.extensions.filter_events(
            pallet_name="Balances",
            event_name="Transfer",
            block_start=block_start,
            block_end=block_end,
        )

        transactions = []
        for event in events:
            try:
                attrs = event.value.get("attributes", event.value.get("event", {}).get("attributes", {}))
                from_addr = attrs.get("from", "")
                to_addr = attrs.get("to", "")
                amount_planck = attrs.get("amount", 0)

                if from_addr == address or to_addr == address:
                    transactions.append({
                        "block": event.value.get("block_number", 0),
                        "from": from_addr,
                        "to": to_addr,
                        "amount_pot": planck_to_pot(amount_planck),
                        "direction": "out" if from_addr == address else "in",
                    })
            except Exception as e:
                logger.warning(f"Failed to parse event: {e}")
                continue

        # Sort by block descending, take latest `limit`
        transactions.sort(key=lambda x: x["block"], reverse=True)
        transactions = transactions[:limit]

        return {
            "transactions": transactions,
            "scanned_blocks": TX_HISTORY_BLOCK_RANGE,
        }
    finally:
        substrate.close()
