"""验证：pallet=6 = Balances，完整解码 dest + amount"""
from substrateinterface import SubstrateInterface
from substrateinterface.utils.ss58 import ss58_encode

TYPES = {
    "AccountInfo": {"type": "struct", "type_mapping": [["nonce","u32"],["consumers","u32"],["providers","u32"],["sufficients","u32"],["data","AccountData"]]},
    "AccountData": {"type": "struct", "type_mapping": [["free","u128"],["reserved","u128"],["miscFrozen","u128"],["feeFrozen","u128"]]},
    "Weight": "u64", "LookupSource": "AccountId", "Address": "AccountId",
}

sub = SubstrateInterface(url="ws://127.0.0.1:9944", ss58_format=42, type_registry={"types": TYPES})

def read_compact(data, pos):
    mode = data[pos] & 0x03
    if mode == 0: return data[pos] >> 2, pos + 1
    elif mode == 1: return (data[pos] | data[pos+1] << 8) >> 2, pos + 2
    elif mode == 2: return (data[pos] | data[pos+1]<<8 | data[pos+2]<<16 | data[pos+3]<<24) >> 2, pos + 4
    else:
        n = data[pos] >> 2
        return int.from_bytes(data[pos+1:pos+1+n], "little"), pos+1+n

def decode_transfer_ext(hex_str):
    raw = bytes.fromhex(hex_str.lstrip("0x"))
    pos = 0
    _, pos = read_compact(raw, pos)
    ver = raw[pos]; pos += 1
    if not (ver & 0x80): return None
    pos += 1                            # MultiAddress prefix
    from_bytes = raw[pos:pos+32]; pos += 32
    pos += 1                            # MultiSignature prefix
    pos += 64                           # signature
    if raw[pos] == 0x00: pos += 1
    else: pos += 2
    _, pos = read_compact(raw, pos)
    _, pos = read_compact(raw, pos)
    pallet = raw[pos]; call = raw[pos+1]; pos += 2
    args = raw[pos:]
    return {"from": ss58_encode(from_bytes, 42), "pallet": pallet, "call": call, "args": args}

def decode_dest_amount(args):
    pos = 0
    pos += 1  # MultiAddress prefix
    dest = ss58_encode(args[pos:pos+32], 42); pos += 32
    amount, _ = read_compact(args, pos)
    return dest, amount

bn = sub.get_block_number(sub.get_chain_head())
print(f"当前区块 #{bn}\n")
for n in range(1, bn+1):
    bh = sub.get_block_hash(n)
    exts = sub.rpc_request("chain_getBlock", [bh])["result"]["block"]["extrinsics"]
    for ext_hex in exts[1:]:
        try:
            r = decode_transfer_ext(ext_hex)
            if r and r["pallet"] == 6 and r["call"] in (0, 3):
                dest, amount = decode_dest_amount(r["args"])
                print(f"Block#{n}: {r['from'][:20]}... -> {dest[:20]}... = {amount} planck ({amount/10**12:.6f} UNIT)")
        except: pass
sub.close()
