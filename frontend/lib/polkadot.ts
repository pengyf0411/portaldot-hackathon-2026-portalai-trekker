/**
 * polkadot.ts — Wallet connection via @polkadot/extension-dapp
 *
 * Handles connecting to the Portaldot browser extension (or any
 * polkadot.js-compatible extension), listing accounts, and providing
 * the injector for signing extrinsics in the frontend.
 */

import type { InjectedAccountWithMeta, InjectedExtension } from "@polkadot/extension-inject/types";

const APP_NAME = "PortalAI";

let cachedExtension: InjectedExtension | null = null;

/**
 * Request access to the wallet extension and return all available accounts.
 * Must be called from a user gesture (button click) to avoid popup blockers.
 */
export async function connectWallet(): Promise<InjectedAccountWithMeta[]> {
  // Dynamically import to avoid SSR issues (extension only works in browser)
  const { web3Enable, web3Accounts } = await import("@polkadot/extension-dapp");

  const extensions = await web3Enable(APP_NAME);
  if (extensions.length === 0) {
    throw new Error(
      "未检测到钱包扩展。请安装 Portaldot Extension 或 Polkadot.js Extension 后刷新页面。"
    );
  }

  // Cache the first available extension for signing later
  cachedExtension = extensions[0];

  const accounts = await web3Accounts();
  if (accounts.length === 0) {
    throw new Error("钱包中没有账户，请在扩展中创建或导入账户。");
  }

  return accounts;
}

/**
 * Get an injector for a specific account address (needed for signing).
 */
export async function getInjectorForAddress(address: string) {
  const { web3FromAddress } = await import("@polkadot/extension-dapp");
  return web3FromAddress(address);
}

/**
 * Format a SS58 address for display (first 6 + ... + last 6 chars).
 */
export function formatAddress(address: string): string {
  if (!address || address.length < 16) return address;
  return `${address.slice(0, 6)}...${address.slice(-6)}`;
}

/**
 * Format a POT amount from planck (14 decimals) to human-readable string.
 * 1 POT = 10^14 planck
 */
export function formatPOT(planck: bigint | number | string, decimals = 14): string {
  const { formatBalance } = require("@polkadot/util");
  return formatBalance(planck.toString(), {
    decimals,
    withUnit: "POT",
    withSi: true,
  });
}

/**
 * Convert POT amount (number) to planck (bigint).
 */
export function potToPlanck(pot: number): bigint {
  // Use integer arithmetic to avoid floating point precision issues
  const potStr = pot.toFixed(14);
  const [whole, frac = ""] = potStr.split(".");
  const fracPadded = frac.padEnd(14, "0").slice(0, 14);
  return BigInt(whole) * BigInt(10 ** 14) + BigInt(fracPadded);
}
