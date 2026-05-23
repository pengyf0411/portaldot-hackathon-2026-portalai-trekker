"""
手动解析 Substrate 2.x extrinsic，不依赖 GenericExtrinsic
顺便探查 Balances pallet 的 index
"""
from substrateinterface import SubstrateInterface
from scalecodec.base import ScaleBytes
import json

TYPES = {
    "AccountInfo": {"type": "struct", "type_mapping": [["nonce","u32"],["consumers","u32"],["providers","u32"],["sufficients","u32"],["data","AccountData"]]},
    "AccountData": {"type": "struct", "type_mapping": [["free","u128"],["reserved","u128"],["miscFrozen","u128"],["feeFrozen","u128"]]},
    "Weight": "u64", "LookupSource": "AccountId", "Address": "AccountId",
}

sub = SubstrateInterface(url="ws://127.0.0.1:9944", ss58_format=42, type_registry={"types": TYPES})

# 1. 查 Balances pallet index
print("=== Metadata pallet indices ===")
try:
    meta = sub.get_runtime_metadata()
    pallets = meta.value[1].get("V13", meta.value[1].get("V12", []))
    for p in pallets:
        name = p.get("name", "?")
        idx = p.get("index", "?")
        if name in ("Balances", "System", "Timestamp"):
            print(f"  {name}: index={idx}")
except Exception as e:
    print(f"  metadata error: {e}")

# 2. 手动解析 extrinsic 字节
def read_compact(data: bytes, pos: int):
    mode = data[pos] & 0x03
    if mode == 0:
        return data[pos] >> 2, pos + 1
    elif mode == 1:
        v = (data[pos] | (data[pos+1] << 8)) >> 2
        return v, pos + 2
    elif mode == 2:
        v = (data[pos] | (data[pos+1] << 8) | (data[pos+2] << 16) | (data[pos+3] << 24)) >> 2
        return v, pos + 4
    else:
        n = data[pos] >> 2
        v = int.from_bytes(data[pos+1:pos+1+n], "little")
        return v, pos + 1 + n

def decode_ext(hex_str: str):
    raw = bytes.fromhex(hex_str.lstrip("0x"))
    pos = 0
    # compact length
    _, pos = read_compact(raw, pos)
    # version
    ver = raw[pos]; pos += 1
    is_signed = bool(ver & 0x80)
    if not is_signed:
        return None
    # address: 32 bytes AccountId (Substrate 2.x LookupSource=AccountId)
    from_addr = raw[pos:pos+32].hex(); pos += 32
    # signature: sr25519 = 64 bytes
    sig = raw[pos:pos+64]; pos += 64
    # era
    if raw[pos] == 0x00:
        pos += 1
    else:
        pos += 2
    # nonce (compact)
    _, pos = read_compact(raw, pos)
    # tip (compact)
    _, pos = read_compact(raw, pos)
    # call: pallet_idx + call_idx
    pallet = raw[pos]; call = raw[pos+1]; pos += 2
    return {"from": from_addr, "pallet": pallet, "call": call, "args_hex": raw[pos:].hex()}

print("\n=== Block #6 extrinsic[1] ===")
bh6 = sub.get_block_hash(6)
raw6 = sub.rpc_request("chain_getBlock", [bh6])
ext_hex = raw6["result"]["block"]["extrinsics"][1]
print(f"hex = {ext_hex[:80]}...")
result = decode_ext(ext_hex)
if result:
    addr_bytes = bytes.fromhex(result["from"])
    from substrateinterface.utils.ss58 import ss58_encode
    addr_ss58 = ss58_encode(addr_bytes, ss58_format=42)
    print(f"from SS58 = {addr_ss58}")
    print(f"pallet_idx = {result['pallet']}, call_idx = {result['call']}")
    print(f"args_hex = {result['args_hex'][:80]}...")
else:
    print("unsigned extrinsic")

sub.close()
