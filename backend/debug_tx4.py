"""扫描全链所有非 timestamp extrinsic"""
from substrateinterface import SubstrateInterface
from scalecodec.base import ScaleBytes

TYPES = {
    "AccountInfo": {"type": "struct", "type_mapping": [["nonce","u32"],["consumers","u32"],["providers","u32"],["sufficients","u32"],["data","AccountData"]]},
    "AccountData": {"type": "struct", "type_mapping": [["free","u128"],["reserved","u128"],["miscFrozen","u128"],["feeFrozen","u128"]]},
    "Weight": "u64", "LookupSource": "AccountId", "Address": "AccountId",
}

sub = SubstrateInterface(url="ws://127.0.0.1:9944", ss58_format=42, type_registry={"types": TYPES})
bn = sub.get_block_number(sub.get_chain_head())
print(f"总区块数: {bn}")

for n in range(1, min(bn + 1, 500)):
    bh = sub.get_block_hash(n)
    raw = sub.rpc_request("chain_getBlock", [bh])
    exts = raw["result"]["block"]["extrinsics"]
    if len(exts) <= 1:
        continue
    for ext_hex in exts[1:]:
        try:
            obj = sub.runtime_config.create_scale_object("GenericExtrinsic", data=ScaleBytes(ext_hex))
            obj.decode()
            v = obj.value_serialized or obj.value
            if isinstance(v, dict):
                call = v.get("call", v)
                mod = call.get("call_module", "?")
                func = call.get("call_function", "?")
                addr = str(v.get("address", "?"))[:16]
                print(f"Block#{n}: {mod}.{func}  from={addr}")
        except Exception as e:
            print(f"Block#{n}: decode error — {e}")

sub.close()
print("扫描完成")
