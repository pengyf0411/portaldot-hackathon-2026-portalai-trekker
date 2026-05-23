"""测试通过扫描 extrinsic 来获取转账记录"""
from substrateinterface import SubstrateInterface

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

# 扫描最近几个区块的 extrinsics
found = []
for block_num in range(bn, max(0, bn - 50), -1):
    try:
        bh = sub.get_block_hash(block_num)
        block = sub.get_block(block_hash=bh)
        extrinsics = block.get("extrinsics", [])
        for ext in extrinsics:
            try:
                call = ext.get("call", {})
                module = call.get("call_module", "")
                func = call.get("call_function", "")
                if module == "Balances" and func in ("transfer_keep_alive", "transfer", "transfer_all"):
                    signer = str(ext.get("address", ""))
                    args = call.get("call_args", [])
                    dest = ""
                    amount = 0
                    for arg in args:
                        if arg.get("name") in ("dest", "to"):
                            dest = str(arg.get("value", ""))
                        elif arg.get("name") in ("value", "amount"):
                            amount = int(arg.get("value", 0))
                    found.append({"block": block_num, "from": signer, "to": dest, "amount": amount, "func": func})
                    print(f"  Block #{block_num}: {signer[:10]}... → {dest[:10]}... = {amount}")
            except Exception as e:
                pass
    except Exception as e:
        print(f"  Block #{block_num} error: {e}")

print(f"\n找到 {len(found)} 笔转账")
sub.close()
