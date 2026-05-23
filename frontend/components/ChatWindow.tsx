"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send, Loader2, Wallet, ArrowUpRight, ArrowDownLeft,
  Zap, Users, Clock, BookmarkPlus, AlertCircle,
} from "lucide-react";
import clsx from "clsx";
import TxConfirmModal from "./TxConfirmModal";
import type { TxResult } from "@/lib/extrinsic";
import { formatAddress } from "@/lib/polkadot";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ─── Types ───────────────────────────────────────────────────────────────────

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  displayType?: string;
  data?: Record<string, unknown>;
  timestamp: Date;
}

interface ChatWindowProps {
  userAddress: string | null;
}

// ─── Suggestion chips ────────────────────────────────────────────────────────

const SUGGESTIONS = [
  "我的 POT 余额是多少？",
  "转 1 POT 给 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
  "转 0.5 POT 手续费是多少？",
  "查看活跃验证节点",
  "我最近的交易记录",
];

// ─── Response card renderers ─────────────────────────────────────────────────

function BalanceCard({ data }: { data: Record<string, unknown> }) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/60 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-700 bg-slate-800">
        <Wallet size={14} className="text-portal-400" />
        <span className="text-xs font-medium text-slate-300">账户余额</span>
      </div>
      <div className="p-4 space-y-3">
        <div>
          <p className="text-xs text-slate-400 mb-1">可用余额</p>
          <p className="text-2xl font-bold text-white">
            {Number(data.free_pot).toLocaleString(undefined, { maximumFractionDigits: 6 })}
            <span className="text-sm font-normal text-slate-400 ml-1">POT</span>
          </p>
        </div>
        {Number(data.reserved_pot) > 0 && (
          <div className="flex justify-between text-sm">
            <span className="text-slate-400">质押锁定</span>
            <span className="text-slate-300">{Number(data.reserved_pot).toLocaleString()} POT</span>
          </div>
        )}
        <div className="pt-1 border-t border-slate-700">
          <p className="text-xs text-slate-500 font-mono truncate">
            {String(data.address)}
          </p>
        </div>
      </div>
    </div>
  );
}

function FeeCard({ data }: { data: Record<string, unknown> }) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/60 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-700 bg-slate-800">
        <Zap size={14} className="text-yellow-400" />
        <span className="text-xs font-medium text-slate-300">Gas 费估算</span>
      </div>
      <div className="p-4 space-y-2">
        <div className="flex justify-between">
          <span className="text-sm text-slate-400">转账金额</span>
          <span className="text-sm text-slate-200">{Number(data.amount_pot)} POT</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-slate-400">预估 Gas 费</span>
          <span className="text-sm font-semibold text-yellow-400">
            {String(data.estimated_fee_formatted)}
          </span>
        </div>
      </div>
    </div>
  );
}

function ValidatorsCard({ data }: { data: Record<string, unknown> }) {
  const validators = (data.validators as Array<{ address: string; commission_pct: number }>) ?? [];
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/60 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700 bg-slate-800">
        <div className="flex items-center gap-2">
          <Users size={14} className="text-green-400" />
          <span className="text-xs font-medium text-slate-300">活跃验证节点</span>
        </div>
        <span className="text-xs text-slate-500">共 {Number(data.total_count)} 个</span>
      </div>
      <div className="divide-y divide-slate-700/50 max-h-60 overflow-y-auto">
        {validators.map((v) => (
          <div key={v.address} className="flex items-center justify-between px-4 py-2.5">
            <p className="text-xs font-mono text-slate-300">{formatAddress(v.address)}</p>
            <span className="text-xs text-slate-400">{v.commission_pct.toFixed(1)}% 佣金</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TxHistoryCard({ data }: { data: Record<string, unknown> }) {
  const txs = (data.transactions as Array<{
    block: number; from: string; to: string;
    amount_formatted: string; direction: "in" | "out";
  }>) ?? [];

  if (txs.length === 0) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-800/60 p-4 text-center">
        <Clock size={24} className="text-slate-600 mx-auto mb-2" />
        <p className="text-sm text-slate-400">最近 {Number(data.scanned_blocks)} 块中无交易记录</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/60 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-700 bg-slate-800">
        <Clock size={14} className="text-blue-400" />
        <span className="text-xs font-medium text-slate-300">最近交易记录</span>
        <span className="ml-auto text-xs text-slate-500">扫描 {Number(data.scanned_blocks)} 块</span>
      </div>
      <div className="divide-y divide-slate-700/50 max-h-64 overflow-y-auto">
        {txs.map((tx, i) => (
          <div key={i} className="flex items-center gap-3 px-4 py-3">
            <div className={clsx(
              "flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center",
              tx.direction === "in" ? "bg-green-900/50" : "bg-red-900/50"
            )}>
              {tx.direction === "in"
                ? <ArrowDownLeft size={13} className="text-green-400" />
                : <ArrowUpRight size={13} className="text-red-400" />}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-slate-400">
                {tx.direction === "in" ? `来自 ${formatAddress(tx.from)}` : `发往 ${formatAddress(tx.to)}`}
              </p>
              <p className="text-xs text-slate-500 mt-0.5">Block #{tx.block}</p>
            </div>
            <span className={clsx(
              "text-sm font-medium flex-shrink-0",
              tx.direction === "in" ? "text-green-400" : "text-red-400"
            )}>
              {tx.direction === "in" ? "+" : "-"}{tx.amount_formatted}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TxPreviewCard({
  data,
  userAddress,
  onConfirm,
}: {
  data: Record<string, unknown>;
  userAddress: string;
  onConfirm: () => void;
}) {
  return (
    <div className="rounded-xl border border-portal-600/50 bg-portal-900/20 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-portal-700/40">
        <ArrowUpRight size={14} className="text-portal-400" />
        <span className="text-xs font-medium text-portal-300">待确认转账</span>
      </div>
      <div className="p-4 space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm text-slate-400">金额</span>
          <span className="text-lg font-bold text-white">
            {Number(data.amount_pot).toLocaleString(undefined, { maximumFractionDigits: 6 })} POT
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-slate-400">接收方</span>
          <span className="text-sm font-mono text-slate-300">{formatAddress(String(data.to))}</span>
        </div>
        {!!data.estimated_fee_formatted && (
          <div className="flex justify-between">
            <span className="text-sm text-slate-400">预估 Gas</span>
            <span className="text-sm text-yellow-400">{String(data.estimated_fee_formatted)}</span>
          </div>
        )}
        <button
          onClick={onConfirm}
          className="w-full mt-1 py-2.5 rounded-xl bg-portal-600 hover:bg-portal-500 text-white font-medium text-sm transition-colors flex items-center justify-center gap-2"
        >
          <Zap size={14} />
          点击确认并签名
        </button>
      </div>
    </div>
  );
}

// ─── Main ChatWindow Component ────────────────────────────────────────────────

function getWelcomeText(address: string | null) {
  return address
    ? "你好！我是 PortalAI，你的 Portaldot 链上助手。你可以用自然语言查询余额、发起转账、查看验证节点等。"
    : "你好！我是 PortalAI。请先连接钱包，再开始链上操作。你也可以直接输入问题来查询链上公开数据。";
}

export default function ChatWindow({ userAddress }: ChatWindowProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      text: getWelcomeText(userAddress),
      displayType: "text",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [confirmData, setConfirmData] = useState<Record<string, unknown> | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // 钱包连接/断开时，同步更新欢迎语（只更新那条固定 id 的消息）
  useEffect(() => {
    setMessages((prev) => {
      const idx = prev.findIndex((m) => m.id === "welcome");
      if (idx === -1) return prev;
      const updated = [...prev];
      updated[idx] = { ...updated[idx], text: getWelcomeText(userAddress) };
      return updated;
    });
  }, [userAddress]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage(text: string) {
    if (!text.trim() || loading) return;
    setInput("");

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      text: text.trim(),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text.trim(),
          user_address: userAddress ?? null,
        }),
      });

      if (!res.ok) throw new Error(`服务器错误 ${res.status}`);
      const json = await res.json();

      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        text: json.message ?? "",
        displayType: json.display_type,
        data: json.data ?? undefined,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e) {
      const errMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        text: `连接后端失败：${e instanceof Error ? e.message : String(e)}`,
        displayType: "error",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  function handleTxSuccess(result: TxResult) {
    const successMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "assistant",
      text: `转账成功！交易 Hash：${result.txHash?.slice(0, 16)}...`,
      displayType: "text",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, successMsg]);
    setConfirmData(null);
  }

  return (
    <div className="flex flex-col h-full">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={clsx("flex", msg.role === "user" ? "justify-end" : "justify-start")}
          >
            <div className={clsx("max-w-[85%] space-y-2", msg.role === "user" ? "items-end" : "items-start")}>
              {/* Bubble text */}
              {msg.text && (
                <div className={clsx(
                  "px-4 py-2.5 rounded-2xl text-sm leading-relaxed",
                  msg.role === "user"
                    ? "bg-portal-600 text-white rounded-br-sm"
                    : msg.displayType === "error"
                      ? "bg-red-900/30 border border-red-500/30 text-red-300 rounded-bl-sm"
                      : "bg-slate-800 text-slate-200 rounded-bl-sm"
                )}>
                  {msg.displayType === "error" && (
                    <AlertCircle size={13} className="inline mr-1.5 mb-0.5 text-red-400" />
                  )}
                  <span className="whitespace-pre-line">{msg.text}</span>
                </div>
              )}

              {/* Rich data cards */}
              {msg.role === "assistant" && msg.data && (
                <div className="w-full">
                  {msg.displayType === "balance" && <BalanceCard data={msg.data} />}
                  {msg.displayType === "fee_info" && <FeeCard data={msg.data} />}
                  {msg.displayType === "validators" && <ValidatorsCard data={msg.data} />}
                  {msg.displayType === "tx_history" && <TxHistoryCard data={msg.data} />}
                  {msg.displayType === "tx_preview" && userAddress && (
                    <TxPreviewCard
                      data={msg.data}
                      userAddress={userAddress}
                      onConfirm={() => setConfirmData(msg.data!)}
                    />
                  )}
                </div>
              )}

              <p className="text-xs text-slate-600 px-1">
                {msg.timestamp.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}
              </p>
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-800 rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-2">
              <Loader2 size={14} className="animate-spin text-portal-400" />
              <span className="text-sm text-slate-400">AI 分析中...</span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Suggestions — 输入框为空时始终显示，方便用户快速操作 */}
      {!input.trim() && !loading && (
        <div className="px-4 pb-2 flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => sendMessage(s)}
              className="text-xs px-3 py-1.5 rounded-full bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-300 transition-colors"
            >
              {s.length > 20 ? s.slice(0, 20) + "…" : s}
            </button>
          ))}
        </div>
      )}

      {/* Input box */}
      <div className="border-t border-slate-700/60 px-4 py-3">
        <div className="flex items-end gap-2 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 focus-within:border-portal-500 transition-colors">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入你的问题或操作…"
            rows={1}
            className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-500 resize-none outline-none max-h-32"
            style={{ lineHeight: "1.5" }}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || loading}
            className={clsx(
              "flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-colors",
              input.trim() && !loading
                ? "bg-portal-600 hover:bg-portal-500 text-white"
                : "bg-slate-700 text-slate-500 cursor-not-allowed"
            )}
          >
            <Send size={14} />
          </button>
        </div>
        <p className="text-xs text-slate-600 mt-1.5 text-center">
          Enter 发送 · Shift+Enter 换行 · 私钥不离开浏览器
        </p>
      </div>

      {/* Tx Confirm Modal */}
      {confirmData && userAddress && (
        <TxConfirmModal
          data={confirmData as unknown as Parameters<typeof TxConfirmModal>[0]["data"]}
          fromAddress={userAddress}
          onClose={() => setConfirmData(null)}
          onSuccess={handleTxSuccess}
        />
      )}
    </div>
  );
}
