"""
deploy_official.py — Deploy SavedMacros using official Portaldot SDK approach
Reference: https://portaldot-dev.readthedocs.io/en/latest/python-sdk/Examples.html
"""
import os, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WASM_PATH = os.path.join(SCRIPT_DIR, "saved_macros", "target", "ink", "saved_macros.wasm")
META_PATH = os.path.join(SCRIPT_DIR, "saved_macros", "target", "ink", "saved_macros.json")

def main():
    for path, name in [(WASM_PATH, "WASM"), (META_PATH, "Metadata JSON")]:
        if not os.path.exists(path):
            print(f"ERROR: {name} not found at {path}")
            sys.exit(1)

    from substrateinterface.contracts import ContractCode, ContractInstance
    from substrateinterface import SubstrateInterface, Keypair

    print("Connecting to local node...")
    portaldot = SubstrateInterface(
        url="ws://127.0.0.1:9944",
        ss58_format=42,
    )
    print(f"Connected. Chain: {portaldot.chain}")

    keypair = Keypair.create_from_uri('//Alice')
    print(f"Deployer: {keypair.ss58_address}")

    # Use official Portaldot SDK approach
    print("\nLoading contract code...")
    code = ContractCode.create_from_contract_files(
        metadata_file=META_PATH,
        wasm_file=WASM_PATH,
        substrate=portaldot
    )

    print("Deploying contract (upload_code=True)...")
    try:
        contract = code.deploy(
            keypair=keypair,
            constructor="new",
            args={},
            value=0,
            gas_limit={
                'ref_time': 25_990_000_000,
                'proof_size': 11_990_383_647_911_208_550
            },
            upload_code=True
        )
        addr = contract.contract_address
        print(f"\n=== SUCCESS ===")
        print(f"Contract address: {addr}")
        print(f"\nAdd to backend/.env:")
        print(f"  CONTRACT_ADDRESS={addr}")
        print(f"\nAdd to frontend/.env.local:")
        print(f"  NEXT_PUBLIC_CONTRACT_ADDRESS={addr}")
        return addr
    except Exception as e:
        print(f"Error: {e}")
        print("\nTrying with endowment=1000000000000000...")
        try:
            contract = code.deploy(
                keypair=keypair,
                constructor="new",
                args={},
                value=1_000_000_000_000_000,
                gas_limit={
                    'ref_time': 25_990_000_000,
                    'proof_size': 11_990_383_647_911_208_550
                },
                upload_code=True
            )
            addr = contract.contract_address
            print(f"\n=== SUCCESS (with endowment) ===")
            print(f"Contract address: {addr}")
            print(f"\nAdd to backend/.env:")
            print(f"  CONTRACT_ADDRESS={addr}")
            return addr
        except Exception as e2:
            print(f"Also failed: {e2}")
            sys.exit(1)

if __name__ == "__main__":
    main()
