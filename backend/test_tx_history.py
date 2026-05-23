from chain_client import query_tx_history

alice   = "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"
trekker = "5HE6mypozftPLF38GXffXw5YvbnjMBGwbSMWpMoWAix68aW7"

print("=== Alice tx history ===")
r = query_tx_history(alice, limit=10)
for tx in r["transactions"]:
    print(tx)
print(f"scanned: {r['scanned_blocks']} blocks, found: {len(r['transactions'])}")

print()
print("=== TREKKER1 tx history ===")
r2 = query_tx_history(trekker, limit=10)
for tx in r2["transactions"]:
    print(tx)
print(f"scanned: {r2['scanned_blocks']} blocks, found: {len(r2['transactions'])}")
