"""
deploy_local.py — Deploy SavedMacros to Portaldot (Substrate 2.x / Metadata V13).
"""
import os, sys, json, time, argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WASM_PATH  = os.path.join(SCRIPT_DIR, "saved_macros", "target", "ink", "saved_macros.wasm")
META_PATH  = os.path.join(SCRIPT_DIR, "saved_macros", "target", "ink", "saved_macros.json")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url",  default="ws://127.0.0.1:9944")
    parser.add_argument("--suri", default="//Alice")
    args = parser.parse_args()

    for path, name in [(WASM_PATH, "WASM"), (META_PATH, "Metadata")]:
        if not os.path.exists(path):
            print(f"ERROR: {name} not found: {path}")
            sys.exit(1)

    from substrateinterface import SubstrateInterface, Keypair

    print(f"Connecting to {args.url} ...")
    substrate = SubstrateInterface(url=args.url, ss58_format=42)
    print(f"Connected. Chain: {substrate.chain}")

    keypair = Keypair.create_from_uri(args.suri)
    print(f"Deployer: {keypair.ss58_address}")

    with open(WASM_PATH, "rb") as f:
        wasm_bytes = f.read()
    with open(META_PATH) as f:
        meta = json.load(f)

    constructors = (meta.get("V3") or meta).get("spec", {}).get("constructors", [])
    selector_hex = next(
        (c["selector"] for c in constructors if c.get("label") == "new"),
        "0x9bae9d5e"
    )
    data_hex = selector_hex if selector_hex.startswith("0x") else f"0x{selector_hex}"
    print(f"Constructor selector: {data_hex}")

    call = substrate.compose_call(
        call_module="Contracts",
        call_function="instantiate_with_code",
        call_params={
            "endowment": 0,
            "gas_limit": 30_000_000_000,
            "code":      f"0x{wasm_bytes.hex()}",
            "data":      data_hex,
            "salt":      "0x",
        }
    )

    print("Signing and submitting (no wait)...")
    extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)

    # Submit without waiting to avoid DigestItem decode error on V13 chain
    receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=False)
    tx_hash = receipt.extrinsic_hash
    print(f"Transaction submitted: {tx_hash}")
    print("Waiting 10s for inclusion...")
    time.sleep(10)

    # Scan Contracts.ContractInfoOf storage to find the newly deployed contract
    print("Scanning ContractInfoOf storage for deployed contracts...")
    try:
        result = substrate.query_map("Contracts", "ContractInfoOf", max_results=50)
        contracts = []
        for addr, info in result:
            contracts.append(str(addr.value))
        if contracts:
            # The last contract in the list is likely the newly deployed one
            contract_address = contracts[-1]
            print(f"\n=== SUCCESS ===")
            print(f"Found {len(contracts)} contract(s) on chain.")
            print(f"Contract address: {contract_address}")
            print(f"\nCopy to backend/.env:")
            print(f"  CONTRACT_ADDRESS={contract_address}")
            print(f"\nCopy to frontend/.env.local:")
            print(f"  NEXT_PUBLIC_CONTRACT_ADDRESS={contract_address}")
        else:
            print("No contracts found in storage yet. Try re-running after a few more seconds.")
    except Exception as e:
        print(f"Storage query error: {e}")
        print(f"Transaction was submitted: {tx_hash}")
        print("Check the Portaldot explorer to find the contract address.")

if __name__ == "__main__":
    main()
