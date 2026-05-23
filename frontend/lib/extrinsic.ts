/**
 * extrinsic.ts — Assemble, sign, and submit extrinsics via @polkadot/api.
 *
 * The backend returns call parameters (call_module, call_function, call_params).
 * This module uses @polkadot/api to construct the extrinsic, requests signing
 * from the wallet extension, and submits it to the Portaldot chain.
 *
 * Private keys NEVER leave the browser/extension.
 */

import { ApiPromise, WsProvider } from "@polkadot/api";
import type { Signer } from "@polkadot/api/types";
import { getInjectorForAddress } from "./polkadot";

const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ?? "wss://mainnet.portaldot.io";

let apiInstance: ApiPromise | null = null;

async function getApi(): Promise<ApiPromise> {
  if (apiInstance && apiInstance.isConnected) return apiInstance;
  const provider = new WsProvider(WS_URL);
  apiInstance = await ApiPromise.create({
    provider,
    // Portaldot uses ss58_format=42 (generic Substrate)
    ss58Format: 42,
  });
  return apiInstance;
}

export interface TxCallParams {
  call_module: string;
  call_function: string;
  call_params: Record<string, unknown>;
}

export interface TxResult {
  success: boolean;
  txHash?: string;
  blockHash?: string;
  error?: string;
  events?: string[];
}

/**
 * Submit a signed extrinsic to the Portaldot chain.
 *
 * @param fromAddress  The sender's SS58 address (used to find the injector)
 * @param callParams   The call parameters returned by the backend
 * @param onStatus     Optional callback for status updates during submission
 */
export async function submitExtrinsic(
  fromAddress: string,
  callParams: TxCallParams,
  onStatus?: (status: string) => void
): Promise<TxResult> {
  try {
    const api = await getApi();
    const injector = await getInjectorForAddress(fromAddress);

    onStatus?.("Building transaction...");

    // Dynamically access the pallet and method from call_module / call_function
    // e.g. api.tx["Balances"]["transfer_keep_alive"](dest, value)
    const palletName = callParams.call_module;
    const methodName = callParams.call_function;

    // @polkadot/api exposes pallets in camelCase: "Balances" → "balances"
    const palletKey = palletName.charAt(0).toLowerCase() + palletName.slice(1);
    // Methods are also camelCase: "transfer_keep_alive" → "transferKeepAlive"
    const methodKey = methodName.replace(/_([a-z])/g, (_: string, c: string) => c.toUpperCase());

    const pallet = (api.tx as Record<string, Record<string, (...args: unknown[]) => unknown>>)[palletKey];
    if (!pallet) throw new Error(`Pallet '${palletName}' not found on chain (tried key: '${palletKey}')`);

    const method = pallet[methodKey];
    if (!method) throw new Error(`Method '${methodName}' not found in pallet '${palletName}' (tried key: '${methodKey}')`);

    // Build arguments array from call_params in the correct order
    const args = buildArgs(palletName, methodName, callParams.call_params);
    const tx = method(...args) as ReturnType<typeof api.tx.balances.transferKeepAlive>;

    onStatus?.("Confirm signing in your wallet extension...");

    return await new Promise<TxResult>((resolve) => {
      tx.signAndSend(
        fromAddress,
        { signer: injector.signer as unknown as Signer },
        ({ status, events, dispatchError }) => {
          if (status.isInBlock) {
            onStatus?.(`Included in block: ${status.asInBlock.toString()}`);

            if (dispatchError) {
              let errMsg = "Transaction execution failed";
              if (dispatchError.isModule) {
                try {
                  const decoded = api.registry.findMetaError(dispatchError.asModule);
                  errMsg = `${decoded.section}.${decoded.name}: ${decoded.docs.join(" ")}`;
                } catch {
                  errMsg = dispatchError.toString();
                }
              }
              resolve({ success: false, error: errMsg });
            } else {
              const eventNames = events.map(
                ({ event }) => `${event.section}.${event.method}`
              );
              resolve({
                success: true,
                txHash: tx.hash.toString(),
                blockHash: status.asInBlock.toString(),
                events: eventNames,
              });
            }
          } else if (status.isFinalized) {
            onStatus?.(`Finalized: ${status.asFinalized.toString()}`);
          } else {
            onStatus?.(`Status: ${status.type}`);
          }
        }
      ).catch((err: Error) => {
        resolve({ success: false, error: err.message });
      });
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return { success: false, error: msg };
  }
}

/**
 * Build ordered arguments array for a specific pallet/method.
 * Handles the Balances.transfer_keep_alive case (dest, value).
 */
function buildArgs(
  pallet: string,
  method: string,
  params: Record<string, unknown>
): unknown[] {
  // Map known methods to their argument order
  const knownMethods: Record<string, string[]> = {
    "Balances.transfer_keep_alive": ["dest", "value"],
    "Balances.transfer": ["dest", "value"],
    "Balances.transfer_all": ["dest", "keep_alive"],
  };

  const key = `${pallet}.${method}`;
  const order = knownMethods[key];

  if (order) {
    return order.map((k) => params[k]);
  }

  // Fallback: return values in insertion order
  return Object.values(params);
}

/**
 * Disconnect the API when no longer needed (cleanup).
 */
export async function disconnectApi(): Promise<void> {
  if (apiInstance) {
    await apiInstance.disconnect();
    apiInstance = null;
  }
}
