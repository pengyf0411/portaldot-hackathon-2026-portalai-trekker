"""
deploy_v3.py — Deploy SavedMacros with correct Portaldot pallet-contracts parameters.
Portaldot uses: value (not endowment), SpWeightsWeightV2Weight for gas_limit.
Ref: https://portaldot-dev.readthedocs.io/en/latest/module-interface/extrinsics/contracts.html
"""
import os, sys, json, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WASM_PATH  = os.path.join(SCRIPT_DIR, "saved_macros", "target", "ink", "saved_macros.wasm")
META_PATH  = os.path.join(SCRIPT_DIR, "saved_macros", "target", "ink", "saved_macros.json")

def scan_contracts(substrate):
    try:
        result = substrate.query_map("Contracts", "ContractInfoOf", max_results=50)
        return [str(a.value) for a, _ in result]
    except Exception as e:
        print(f"  scan error: {e}")
        return []

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

    spec = meta.get("spec", {})
    constructors = spec.get("constructors", [])
    selector = next(
        (c["selector"] for c in constructors if c.get("label") == "new"),
        "0x9bae9d5e"
    )
    data_hex = selector if selector.startswith("0x") else f"0x{selector}"
    print(f"Constructor selector: {data_hex}")
    print(f"WASM size: {len(wasm_bytes)} bytes")

    wasm_hex = f"0x{wasm_bytes.hex()}"

    # Official Portaldot pallet-contracts API:
    # instantiateWithCode(value, gas_limit: WeightV2, storage_deposit_limit, code, data, salt)
    configs = [
        {
            "name": "WeightV2 + value=0 + no storage_deposit_limit",
            "params": {
                "value": 0,
                "gas_limit": {"ref_time": 25_990_000_000, "proof_size": 11_990_383_647_911_208_550},
                "storage_deposit_limit": None,
                "code": wasm_hex,
                "data": data_hex,
                "salt": "0x",
            }
        },
        {
            "name": "WeightV2 + value=1POT",
            "params": {
                "value": 10**14,
                "gas_limit": {"ref_time": 25_990_000_000, "proof_size": 11_990_383_647_911_208_550},
                "storage_deposit_limit": None,
                "code": wasm_hex,
                "data": data_hex,
                "salt": "0x",
            }
        },
        {
            "name": "Compact gas (OldWeight) + value=0",
            "call_function": "instantiate_with_code_old_weight",
            "params": {
                "value": 0,
                "gas_limit": 50_000_000_000,
                "storage_deposit_limit": None,
                "code": wasm_hex,
                "data": data_hex,
                "salt": "0x",
            }
        },
    ]

    for cfg in configs:
        fn = cfg.get("call_function", "instantiate_with_code")
        print(f"\nTrying {fn} ({cfg['name']})...")
        try:
            call = substrate.compose_call(
                call_module="Contracts",
                call_function=fn,
                call_params=cfg["params"]
            )
            extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)
            print("  Submitting (no wait)...")
            receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=False)
            print(f"  TX hash: {receipt.extrinsic_hash}")
            print("  Waiting 15s for inclusion...")
            time.sleep(15)
            contracts = scan_contracts(substrate)
            if contracts:
                addr = contracts[-1]
                print(f"\n=== SUCCESS ===")
                print(f"Contract address: {addr}")
                print(f"\nAdd to backend/.env:\n  CONTRACT_ADDRESS={addr}")
                print(f"\nAdd to frontend/.env.local:\n  NEXT_PUBLIC_CONTRACT_ADDRESS={addr}")
                return addr
            else:
                print("  No contract found in storage after 15s")
        except Exception as e:
            print(f"  Error: {e}")
            continue

    print("\nAll attempts failed. Check node logs or try mainnet.")
    sys.exit(1)

if __name__ == "__main__":
    main()
