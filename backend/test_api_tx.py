"""通过 FastAPI 接口测试交易历史（会正确加载 .env）"""
from dotenv import load_dotenv
load_dotenv()

from chain_client import query_tx_history, planck_to_pot

trekker = "5HE6mypozftPLF38GXffXw5YvbnjMBGwbSMWpMoWAix68aW7"
alice   = "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"

import os
print(f"连接节点: {os.getenv('PORTALDOT_WS_URL', 'wss://mainnet.portaldot.io')}")

print("\n=== TREKKER1 交易记录 ===")
r = query_tx_history(trekker, limit=10)
for tx in r["transactions"]:
    pot = tx["amount_pot"]
    print(f"  Block#{tx['block']} [{tx['direction']}] {tx['from'][:12]}...→{tx['to'][:12]}... = {pot} POT")
print(f"扫描 {r['scanned_blocks']} 块，找到 {len(r['transactions'])} 条")

print("\n=== Alice 交易记录 ===")
r2 = query_tx_history(alice, limit=10)
for tx in r2["transactions"]:
    print(f"  Block#{tx['block']} [{tx['direction']}] {tx['from'][:12]}...→{tx['to'][:12]}... = {tx['amount_pot']} POT")
print(f"扫描 {r2['scanned_blocks']} 块，找到 {len(r2['transactions'])} 条")
