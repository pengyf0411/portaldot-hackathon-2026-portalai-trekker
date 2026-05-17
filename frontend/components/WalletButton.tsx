"use client";

import { useState } from "react";
import { Wallet, ChevronDown, LogOut, Copy, Check } from "lucide-react";
import type { InjectedAccountWithMeta } from "@polkadot/extension-inject/types";
import { connectWallet, formatAddress } from "@/lib/polkadot";
import clsx from "clsx";

interface WalletButtonProps {
  account: InjectedAccountWithMeta | null;
  onConnect: (account: InjectedAccountWithMeta) => void;
  onDisconnect: () => void;
}

export default function WalletButton({ account, onConnect, onDisconnect }: WalletButtonProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [accounts, setAccounts] = useState<InjectedAccountWithMeta[]>([]);
  const [copied, setCopied] = useState(false);

  async function handleConnect() {
    setLoading(true);
    setError(null);
    try {
      const list = await connectWallet();
      if (list.length === 1) {
        onConnect(list[0]);
      } else {
        setAccounts(list);
        setShowDropdown(true);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "连接失败");
    } finally {
      setLoading(false);
    }
  }

  async function copyAddress() {
    if (!account) return;
    await navigator.clipboard.writeText(account.address);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  if (!account) {
    return (
      <div className="relative">
        <button
          onClick={handleConnect}
          disabled={loading}
          className={clsx(
            "flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm transition-all",
            "bg-portal-600 hover:bg-portal-500 text-white",
            "disabled:opacity-60 disabled:cursor-not-allowed"
          )}
        >
          <Wallet size={16} />
          {loading ? "连接中..." : "连接钱包"}
        </button>

        {error && (
          <p className="absolute top-12 right-0 w-72 text-xs text-red-400 bg-red-900/30 border border-red-500/30 rounded-lg p-2 z-50">
            {error}
          </p>
        )}

        {/* Multi-account picker */}
        {showDropdown && accounts.length > 1 && (
          <div className="absolute top-12 right-0 w-80 bg-slate-800 border border-slate-600 rounded-xl shadow-2xl z-50 overflow-hidden">
            <p className="text-xs text-slate-400 px-3 py-2 border-b border-slate-700">
              选择账户
            </p>
            {accounts.map((acc) => (
              <button
                key={acc.address}
                onClick={() => {
                  onConnect(acc);
                  setShowDropdown(false);
                }}
                className="w-full text-left px-3 py-2.5 hover:bg-slate-700 transition-colors"
              >
                <p className="text-sm font-medium text-slate-100">
                  {acc.meta.name || "未命名账户"}
                </p>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  {formatAddress(acc.address)}
                </p>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setShowDropdown((v) => !v)}
        className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm bg-slate-800 hover:bg-slate-700 border border-slate-600 transition-colors"
      >
        <span className="w-2 h-2 rounded-full bg-green-400" />
        <span className="font-medium text-slate-200 max-w-[120px] truncate">
          {account.meta.name || formatAddress(account.address)}
        </span>
        <ChevronDown size={14} className="text-slate-400" />
      </button>

      {showDropdown && (
        <div className="absolute top-12 right-0 w-64 bg-slate-800 border border-slate-600 rounded-xl shadow-2xl z-50 overflow-hidden">
          <div className="px-3 py-2.5 border-b border-slate-700">
            <p className="text-xs text-slate-400">已连接</p>
            <p className="text-sm font-medium text-slate-100 mt-0.5">
              {account.meta.name || "账户"}
            </p>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              {formatAddress(account.address)}
            </p>
          </div>
          <button
            onClick={copyAddress}
            className="w-full flex items-center gap-2 px-3 py-2.5 text-sm text-slate-300 hover:bg-slate-700 transition-colors"
          >
            {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
            {copied ? "已复制" : "复制地址"}
          </button>
          <button
            onClick={() => { onDisconnect(); setShowDropdown(false); }}
            className="w-full flex items-center gap-2 px-3 py-2.5 text-sm text-red-400 hover:bg-slate-700 transition-colors"
          >
            <LogOut size={14} />
            断开连接
          </button>
        </div>
      )}

      {/* Close dropdown on outside click */}
      {showDropdown && (
        <div className="fixed inset-0 z-40" onClick={() => setShowDropdown(false)} />
      )}
    </div>
  );
}
