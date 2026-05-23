"""检查 block 6/10/60 的原始 extrinsic hex 并尝试多种解码方式"""
from substrateinterface import SubstrateInterface
from scalecodec.base import ScaleBytes
import json

TYPES = {
    "AccountInfo": {"type": "struct", "type_mapping": [["nonce","u32"],["consumers","u32"],["providers","u32"],["sufficients","u32"],["data","AccountData"]]},
    "AccountData": {"type": "struct", "type_mapping": [["free","u128"],["reserved","u128"],["miscFrozen","u128"],["feeFrozen","u128"]]},
    "Weight": "u64", "LookupSource": "AccountId", "Address": "AccountId",
}

sub = SubstrateInterface(url="ws://127.0.0.1:9944", ss58_format=42, type_registry={"types": TYPES})

for target_block in [6, 10, 60]:
    bh = sub.get_block_hash(target_block)
    raw = sub.rpc_request("chain_getBlock", [bh])
    exts = raw["result"]["block"]["extrinsics"]
    print(f"\n=== Block #{target_block}: {len(exts)} extrinsics ===")
    for i, ext_hex in enumerate(exts):
        print(f"  [{i}] hex={ext_hex[:60]}...")
        # 方式1: GenericExtrinsic
        try:
            obj = sub.runtime_config.create_scale_object("GenericExtrinsic", data=ScaleBytes(ext_hex))
            obj.decode()
            print(f"       GenericExtrinsic.value={obj.value}")
            print(f"       GenericExtrinsic.value_serialized={obj.value_serialized}")
        except Exception as e:
            print(f"       GenericExtrinsic error: {e}")
        # 方式2: Extrinsic
        try:
            obj2 = sub.runtime_config.create_scale_object("Extrinsic", data=ScaleBytes(ext_hex))
            obj2.decode()
            print(f"       Extrinsic.value={str(obj2.value)[:100]}")
        except Exception as e:
            print(f"       Extrinsic error: {e}")

sub.close()
