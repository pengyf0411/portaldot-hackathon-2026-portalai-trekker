/**
 * deploy.mjs — Deploy SavedMacros ink! contract via @polkadot/api
 * Usage: node deploy.mjs
 */
import { ApiPromise, WsProvider, Keyring } from '@polkadot/api';
import { CodePromise } from '@polkadot/api-contract';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dir = dirname(fileURLToPath(import.meta.url));
const CONTRACT_PATH = join(__dir, 'saved_macros', 'target', 'ink', 'saved_macros_full.contract');

async function main() {
  console.log('Reading contract bundle...');
  const bundle = JSON.parse(readFileSync(CONTRACT_PATH, 'utf8'));
  console.log(`  ink! version : ${bundle.source?.language ?? 'unknown'}`);
  console.log(`  WASM bytes   : ${Math.round(bundle.source?.wasm?.length / 2)} bytes`);

  console.log('\nConnecting to ws://127.0.0.1:9944 ...');
  const provider = new WsProvider('ws://127.0.0.1:9944');
  const api = await ApiPromise.create({ provider });
  console.log(`  Chain: ${(await api.rpc.system.chain()).toString()}`);

  const keyring = new Keyring({ type: 'sr25519' });
  const alice = keyring.addFromUri('//Alice');
  console.log(`  Deployer: ${alice.address}`);

  console.log('\nUploading & instantiating contract...');
  const code = new CodePromise(api, bundle, bundle.source.wasm);

  const gasLimit = api.registry.createType('WeightV2', {
    refTime: 30_000_000_000,
    proofSize: 1_000_000,
  });

  await new Promise((resolve, reject) => {
    let contractAddress = null;

    code.tx.new({ gasLimit, storageDepositLimit: null, value: 0 })
      .signAndSend(alice, ({ status, contract, dispatchError, events }) => {
        console.log(`  Status: ${status.type}`);

        if (dispatchError) {
          if (dispatchError.isModule) {
            const decoded = api.registry.findMetaError(dispatchError.asModule);
            reject(new Error(`Dispatch error: ${decoded.section}.${decoded.name}: ${decoded.docs}`));
          } else {
            reject(new Error(`Dispatch error: ${dispatchError.toString()}`));
          }
          return;
        }

        if (contract) {
          contractAddress = contract.address.toString();
        }

        if (status.isInBlock || status.isFinalized) {
          if (contractAddress) {
            console.log('\n=== SUCCESS ===');
            console.log(`Contract address: ${contractAddress}`);
            console.log('\nAdd to backend/.env:');
            console.log(`  CONTRACT_ADDRESS=${contractAddress}`);
            console.log('\nAdd to frontend/.env.local:');
            console.log(`  NEXT_PUBLIC_CONTRACT_ADDRESS=${contractAddress}`);
            resolve(contractAddress);
          } else {
            // Try extracting from events
            for (const { event } of events) {
              if (event.section === 'contracts' && event.method === 'Instantiated') {
                const addr = event.data[1].toString();
                console.log('\n=== SUCCESS (from event) ===');
                console.log(`Contract address: ${addr}`);
                console.log('\nAdd to backend/.env:');
                console.log(`  CONTRACT_ADDRESS=${addr}`);
                console.log('\nAdd to frontend/.env.local:');
                console.log(`  NEXT_PUBLIC_CONTRACT_ADDRESS=${addr}`);
                resolve(addr);
                return;
              }
            }
            if (status.isFinalized) {
              reject(new Error('Finalized but no contract address found in events'));
            }
          }
        }
      })
      .catch(reject);
  }).catch(async (err) => {
    console.error('Error:', err.message);
    // Fallback: try old-style gasLimit (u64)
    console.log('\nRetrying with legacy gas limit format...');
    await deployLegacy(api, alice, bundle);
  });

  await api.disconnect();
}

async function deployLegacy(api, alice, bundle) {
  const code = new CodePromise(api, bundle, bundle.source.wasm);
  const gasLimit = 30_000_000_000n;

  return new Promise((resolve, reject) => {
    code.tx.new({ gasLimit, value: 0 })
      .signAndSend(alice, ({ status, contract, dispatchError, events }) => {
        console.log(`  [legacy] Status: ${status.type}`);
        if (dispatchError) {
          reject(new Error(dispatchError.toString()));
          return;
        }
        if (contract) {
          const addr = contract.address.toString();
          console.log(`\n=== SUCCESS (legacy) ===\nContract address: ${addr}`);
          console.log(`\nAdd to backend/.env:\n  CONTRACT_ADDRESS=${addr}`);
          resolve(addr);
        } else if (status.isInBlock || status.isFinalized) {
          for (const { event } of events) {
            if (event.section === 'contracts' && event.method === 'Instantiated') {
              const addr = event.data[1].toString();
              console.log(`\n=== SUCCESS (legacy, from event) ===\nContract address: ${addr}`);
              resolve(addr);
              return;
            }
          }
        }
      })
      .catch(reject);
  });
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
