from substrateinterface import SubstrateInterface
import time

TYPES = {
    "AccountInfo": {"type": "struct", "type_mapping": [["nonce","u32"],["consumers","u32"],["providers","u32"],["sufficients","u32"],["data","AccountData"]]},
    "AccountData": {"type": "struct", "type_mapping": [["free","u128"],["reserved","u128"],["miscFrozen","u128"],["feeFrozen","u128"]]},
    "Weight": "u64", "LookupSource": "AccountId", "Address": "AccountId",
}

sub = SubstrateInterface(url="ws://127.0.0.1:9944", ss58_format=42, type_registry={"types": TYPES})

b1 = sub.get_block_number(sub.get_chain_head())
print(f"当前区块: #{b1}")
time.sleep(8)
b2 = sub.get_block_number(sub.get_chain_head())
print(f"8秒后区块: #{b2}")
if b2 > b1:
    print("出块正常")
else:
    print("没有出块 - 节点未在生产区块")

trekker = "5HE6mypozftPLF38GXffXw5YvbnjMBGwbSMWpMoWAix68aW7"
r = sub.query("System", "Account", [trekker])
print(f"TREKKER1 余额: {r.value['data']['free']} planck")
sub.close()
