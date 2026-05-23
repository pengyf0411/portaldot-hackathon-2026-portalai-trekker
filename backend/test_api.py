import requests
from dotenv import load_dotenv
load_dotenv()

BASE = "http://localhost:8000"
ALICE = "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"

tests = [
    ("query_balance", {"message": "What is my POT balance?", "user_address": ALICE}),
    ("estimate_fee", {"message": "How much gas to send 10 POT?", "user_address": ALICE}),
    ("query_validators", {"message": "Show active validators", "user_address": ALICE}),
    (
        "transfer_preview",
        {
            "message": "Send 0.001 POT to 5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty",
            "user_address": ALICE,
        },
    ),
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
