"""精确调试：为什么 query_tx_history 找不到 #396/#426 的转账"""
from chain_client import _decode_transfer_extrinsic, _http_batch_rpc, _get_substrate, planck_to_pot

sub = _get_substrate()
bn = sub.get_block_number(sub.get_chain_head())
print(f"current block: #{bn}")

# 直接测试 block 396 和 426
for target in [396, 426]:
    bh = sub.rpc_request("chain_getBlockHash", [target])["result"]
    raw = sub.rpc_request("chain_getBlock", [bh])
    exts = raw["result"]["block"]["extrinsics"]
    print(f"\nBlock #{target}: {len(exts)} extrinsics")
    for i, ext_hex in enumerate(exts):
        result = _decode_transfer_extrinsic(ext_hex)
        print(f"  [{i}] decode result: {result}")
        if result:
            print(f"       -> {planck_to_pot(result['amount_planck'])} POT")

# 测试 HTTP batch 是否正确返回这两个块
print("\n=== 测试 HTTP batch 包含 #396/#426 ===")
block_end = bn
block_start = max(1, block_end - 200)
block_numbers = list(range(block_end, block_start - 1, -1))
print(f"扫描 {len(block_numbers)} 个块: #{block_end} → #{block_start}")
print(f"Block #396 在扫描范围内: {396 in block_numbers}")
print(f"Block #426 在扫描范围内: {426 in block_numbers}")

sub.close()
