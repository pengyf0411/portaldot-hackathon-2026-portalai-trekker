"use client";

import { useState } from "react";
import type { InjectedAccountWithMeta } from "@polkadot/extension-inject/types";
import WalletButton from "@/components/WalletButton";
import ChatWindow from "@/components/ChatWindow";
import { BookmarkPlus, Cpu, Github } from "lucide-react";

export default function Home() {
  const [account, setAccount] = useState<InjectedAccountWithMeta | null>(null);

  return (
    <div className="flex flex-col h-screen max-h-screen overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 border-b border-slate-700/60 bg-slate-900/80 backdrop-blur-sm px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Logo */}
          <div className="w-8 h-8 rounded-lg bg-portal-600 flex items-center justify-center">
            <Cpu size={16} className="text-white" />
          </div>
          <div>
            <h1 className="font-bold text-slate-100 text-sm leading-none">PortalAI</h1>
            <p className="text-xs text-slate-500 mt-0.5">Portaldot AI Copilot</p>
          </div>

          {/* Chain badge */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-900/30 border border-green-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            <span className="text-xs text-green-400">Portaldot Mainnet</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* GitHub link */}
          <a
            href="https://github.com/your-org/portaldot-ai-copilot"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            <Github size={14} />
            GitHub
          </a>

          <WalletButton
            account={account}
            onConnect={setAccount}
            onDisconnect={() => setAccount(null)}
          />
        </div>
      </header>

      {/* Main layout: sidebar + chat */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar: capability list */}
        <aside className="hidden lg:flex flex-col w-56 flex-shrink-0 border-r border-slate-700/60 bg-slate-900/50 p-4 gap-2">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
            支持的操作
          </p>
          {[
            { icon: "💰", label: "查询 POT 余额", example: "我的余额是多少？" },
            { icon: "➡️", label: "POT 转账", example: "转 10 POT 给地址…" },
            { icon: "⛽", label: "估算 Gas 费", example: "转 5 POT 要多少费用？" },
            { icon: "🔗", label: "查看验证节点", example: "有哪些活跃验证人？" },
            { icon: "📋", label: "交易记录", example: "我最近的转账" },
          ].map((item) => (
            <div
              key={item.label}
              className="rounded-lg p-2.5 bg-slate-800/50 hover:bg-slate-800 transition-colors cursor-default"
            >
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-sm">{item.icon}</span>
                <span className="text-xs font-medium text-slate-300">{item.label}</span>
              </div>
              <p className="text-xs text-slate-500 pl-6">{item.example}</p>
            </div>
          ))}

          <div className="mt-auto pt-4 border-t border-slate-700/50">
            <div className="rounded-lg p-3 bg-portal-900/30 border border-portal-700/30">
              <div className="flex items-center gap-1.5 mb-1">
                <BookmarkPlus size={12} className="text-portal-400" />
                <span className="text-xs font-medium text-portal-300">链上宏</span>
              </div>
              <p className="text-xs text-slate-400">
                将常用操作保存为链上宏，快速复用。
              </p>
            </div>
          </div>
        </aside>

        {/* Chat area */}
        <main className="flex-1 flex flex-col min-w-0">
          <ChatWindow userAddress={account?.address ?? null} />
        </main>
      </div>
    </div>
  );
}
