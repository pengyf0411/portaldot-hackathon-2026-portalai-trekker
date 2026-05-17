import requests
from dotenv import load_dotenv
load_dotenv()

BASE = "http://localhost:8000"
ALICE = "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"

tests = [
    ("查询余额", {"message": "我的POT余额是多少？", "user_address": ALICE}),
    ("估算手续费", {"message": "转账10 POT手续费大概多少？", "user_address": ALICE}),
    ("查看验证节点", {"message": "查看活跃验证节点", "user_address": ALICE}),
    ("转账预览", {"message": "转 0.001 POT 给 5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty", "user_address": ALICE}),
]

for name, payload in tests:
    try:
        r = requests.post(f"{BASE}/chat", json=payload, timeout=30)
        d = r.json()
        print(f"[{name}] intent={d['intent']} display={d['display_type']}")
        print(f"  {d['message'][:100]}")
        print()
    except Exception as e:
        print(f"[{name}] ERROR: {e}")
