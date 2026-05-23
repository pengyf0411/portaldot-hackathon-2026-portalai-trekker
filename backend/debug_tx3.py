"""打印最近几个区块里所有 extrinsics 的 call 内容"""
from substrateinterface import SubstrateInterface
from scalecodec.base import ScaleBytes

TYPES = {
    "AccountInfo": {"type": "struct", "type_mapping": [["nonce","u32"],["consumers","u32"],["providers","u32"],["sufficients","u32"],["data","AccountData"]]},
    "AccountData": {"type": "struct", "type_mapping": [["free","u128"],["reserved","u128"],["miscFrozen","u128"],["feeFrozen","u128"]]},
    "Weight": "u64", "LookupSource": "AccountId", "Address": "AccountId",
    "ValidatorId": "AccountId", "AuthorityId": "AccountId",
}

sub = SubstrateInterface(url="ws://127.0.0.1:9944", ss58_format=42, type_registry={"types": TYPES})
head = sub.get_chain_head()
bn = sub.get_block_number(head)
print(f"当前区块: #{bn}，扫描最近 30 块\n")

for block_num in range(bn, max(0, bn - 30), -1):
    bh = sub.get_block_hash(block_num)
    raw = sub.rpc_request("chain_getBlock", [bh])
    raw_extrinsics = raw["result"]["block"]["extrinsics"]
    if len(raw_extrinsics) <= 1:  # 只有 timestamp 的块跳过
        continue
    print(f"Block #{block_num} — {len(raw_extrinsics)} extrinsics:")
    for i, ext_hex in enumerate(raw_extrinsics):
        try:
            ext_obj = sub.runtime_config.create_scale_object("GenericExtrinsic", data=ScaleBytes(ext_hex))
            ext_obj.decode()
            v = ext_obj.value_serialized or ext_obj.value
            if isinstance(v, dict):
                call = v.get("call", v)
                module = call.get("call_module", "?")
                func = call.get("call_function", "?")
                addr = v.get("address", "unsigned")
                print(f"  [{i}] {module}.{func}  from={str(addr)[:20]}")
            else:
                print(f"  [{i}] raw value type: {type(v)}")
        except Exception as e:
            print(f"  [{i}] decode error: {e}")

sub.close()
