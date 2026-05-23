"""测试：用原始 RPC 获取 extrinsics，不走 get_block() 的完整解码"""
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
print(f"当前区块: #{bn}")

found = []
for block_num in range(bn, max(0, bn - 50), -1):
    try:
        bh = sub.get_block_hash(block_num)
        # 直接用 RPC 获取原始区块（返回 JSON，不走 SCALE 解码）
        raw = sub.rpc_request("chain_getBlock", [bh])
        raw_extrinsics = raw["result"]["block"]["extrinsics"]

        for ext_hex in raw_extrinsics:
            try:
                # 只解码 extrinsic，跳过 block header 的 DigestItem 问题
                ext_obj = sub.runtime_config.create_scale_object(
                    "GenericExtrinsic", data=ScaleBytes(ext_hex)
                )
                ext_obj.decode()
                value = ext_obj.value_serialized or ext_obj.value

                # 提取 call 信息
                call_module = ""
                call_func = ""
                call_args = {}

                if isinstance(value, dict):
                    call = value.get("call", value)
                    call_module = call.get("call_module", "")
                    call_func = call.get("call_function", "")
                    for arg in call.get("call_args", []):
                        call_args[arg.get("name", "")] = arg.get("value", "")
                    address = value.get("address", "")
                else:
                    continue

                if call_module == "Balances" and call_func in ("transfer_keep_alive", "transfer"):
                    dest = str(call_args.get("dest", call_args.get("to", "")))
                    amount = int(call_args.get("value", call_args.get("amount", 0)))
                    print(f"  Block #{block_num}: {str(address)[:12]}... → {dest[:12]}... = {amount}")
                    found.append({"block": block_num, "from": str(address), "to": dest, "amount": amount})
            except Exception as e:
                pass
    except Exception as e:
        print(f"  Block #{block_num} error: {e}")

print(f"\n共找到 {len(found)} 笔转账")
sub.close()
