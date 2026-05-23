"""
deploy_v2.py — Deploy SavedMacros to Portaldot local node (Substrate 2.x, old pallet-contracts)
The old pallet-contracts uses 'endowment' not 'value', and gas_limit is a plain u64.
"""
import os, sys, json, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WASM_PATH  = os.path.join(SCRIPT_DIR, "saved_macros", "target", "ink", "saved_macros.wasm")
META_PATH  = os.path.join(SCRIPT_DIR, "saved_macros", "target", "ink", "saved_macros.json")

def main():
    from substrateinterface import SubstrateInterface, Keypair

    print("Connecting to ws://127.0.0.1:9944 ...")
    substrate = SubstrateInterface(url="ws://127.0.0.1:9944", ss58_format=42)
    print(f"Connected. Chain: {substrate.chain}")

    keypair = Keypair.create_from_uri('//Alice')
    print(f"Deployer: {keypair.ss58_address}")

    with open(WASM_PATH, "rb") as f:
        wasm_bytes = f.read()
    with open(META_PATH) as f:
        meta = json.load(f)

    # Get constructor selector for 'new'
    spec = meta.get("spec", {})
    constructors = spec.get("constructors", [])
    selector = next(
        (c["selector"] for c in constructors if c.get("label") == "new"),
        "0x9bae9d5e"
    )
    data_hex = selector if selector.startswith("0x") else f"0x{selector}"
    print(f"Constructor selector: {data_hex}")

    wasm_hex = f"0x{wasm_bytes.hex()}"

    # Try old pallet-contracts API: instantiate_with_code with endowment
    # endowment=0 first, then fallback to 1 POT
    for endowment in [0, 10**14]:
        print(f"\nTrying instantiate_with_code (endowment={endowment})...")
        try:
            call = substrate.compose_call(
                call_module="Contracts",
                call_function="instantiate_with_code",
                call_params={
                    "endowment": endowment,
                    "gas_limit": 50_000_000_000,
                    "code": wasm_hex,
                    "data": data_hex,
                    "salt": "0x",
                }
            )
            extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)
            receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
            print(f"Included in block: {receipt.block_hash}")
            if receipt.is_success:
                print("Transaction succeeded!")
                # Find contract address from events
                for event in receipt.triggered_events:
                    ev = event.value
                    module = ev.get("event", {}).get("module_id", "")
                    name   = ev.get("event", {}).get("event_id", "")
                    if module == "Contracts" and name == "Instantiated":
                        params = ev.get("event", {}).get("params", [])
                        # second param is the contract address
                        addr = params[1]["value"] if len(params) > 1 else None
                        if addr:
                            print(f"\n=== SUCCESS ===")
                            print(f"Contract address: {addr}")
                            print(f"\nAdd to backend/.env:\n  CONTRACT_ADDRESS={addr}")
                            print(f"\nAdd to frontend/.env.local:\n  NEXT_PUBLIC_CONTRACT_ADDRESS={addr}")
                            return addr
                # fallback: scan ContractInfoOf
                print("Scanning ContractInfoOf for address...")
                result = substrate.query_map("Contracts", "ContractInfoOf", max_results=50)
                contracts = [str(a.value) for a, _ in result]
                if contracts:
                    addr = contracts[-1]
                    print(f"\n=== SUCCESS (from storage) ===")
                    print(f"Contract address: {addr}")
                    print(f"\nAdd to backend/.env:\n  CONTRACT_ADDRESS={addr}")
                    return addr
                else:
                    print("No contract in storage after success?")
            else:
                print(f"Transaction failed: {receipt.error_message}")
        except Exception as e:
            print(f"Error: {e}")
            continue

    print("\nAll attempts failed.")
    sys.exit(1)

if __name__ == "__main__":
    main()
