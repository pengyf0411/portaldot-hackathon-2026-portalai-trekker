"""测试交易历史查询是否正常"""
import os
from dotenv import load_dotenv
load_dotenv()

# 用 chain_client 里最新的类型定义测试
from chain_client import query_tx_history

ALICE = "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"

print(f"查询 Alice 的交易记录...")
try:
    result = query_tx_history(ALICE, limit=10)
    print(f"成功！扫描了 {result['scanned_blocks']} 个区块")
    print(f"找到 {len(result['transactions'])} 笔交易")
    for tx in result["transactions"]:
        print(f"  Block #{tx['block']}: {tx['direction']} {tx['amount_pot']} POT")
except Exception as e:
    print(f"失败: {e}")
