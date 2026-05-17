"use client";

import { useState } from "react";
import { X, AlertTriangle, ArrowRight, Loader2, CheckCircle, XCircle } from "lucide-react";
import { submitExtrinsic, type TxCallParams, type TxResult } from "@/lib/extrinsic";
import { formatAddress } from "@/lib/polkadot";
import clsx from "clsx";

interface TxPreviewData {
  call_module: string;
  call_function: string;
  call_params: Record<string, unknown>;
  amount_pot: number;
  amount_planck: number;
  to: string;
  from?: string;
  estimated_fee_pot?: number;
  estimated_fee_formatted?: string;
  message: string;
}

interface TxConfirmModalProps {
  data: TxPreviewData;
  fromAddress: string;
  onClose: () => void;
  onSuccess: (result: TxResult) => void;
}

type Phase = "confirm" | "signing" | "success" | "error";

export default function TxConfirmModal({ data, fromAddress, onClose, onSuccess }: TxConfirmModalProps) {
  const [phase, setPhase] = useState<Phase>("confirm");
  const [statusText, setStatusText] = useState("");
  const [result, setResult] = useState<TxResult | null>(null);

  async function handleConfirm() {
    setPhase("signing");
    const callParams: TxCallParams = {
      call_module: data.call_module,
      call_function: data.call_function,
      call_params: data.call_params,
    };

    const txResult = await submitExtrinsic(fromAddress, callParams, (status) => {
      setStatusText(status);
    });

    setResult(txResult);
    if (txResult.success) {
      setPhase("success");
      onSuccess(txResult);
    } else {
      setPhase("error");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-700">
          <h2 className="font-semibold text-slate-100">
            {phase === "confirm" && "确认交易"}
            {phase === "signing" && "交易进行中"}
            {phase === "success" && "交易成功"}
            {phase === "error" && "交易失败"}
          </h2>
          {(phase === "confirm" || phase === "success" || phase === "error") && (
            <button onClick={onClose} className="text-slate-400 hover:text-slate-200 transition-colors">
              <X size={18} />
            </button>
          )}
        </div>

        <div className="p-5">
          {/* Confirm Phase */}
          {phase === "confirm" && (
            <>
              <div className="flex items-center justify-between mb-5">
                <div className="text-center flex-1">
                  <p className="text-xs text-slate-400 mb-1">发送方</p>
                  <p className="font-mono text-sm text-slate-300">{formatAddress(fromAddress)}</p>
                </div>
                <ArrowRight size={20} className="text-portal-400 mx-2 flex-shrink-0" />
                <div className="text-center flex-1">
                  <p className="text-xs text-slate-400 mb-1">接收方</p>
                  <p className="font-mono text-sm text-slate-300">{formatAddress(data.to)}</p>
                </div>
              </div>

              <div className="rounded-xl bg-slate-800 border border-slate-700 divide-y divide-slate-700 mb-5">
                <div className="flex justify-between items-center px-4 py-3">
                  <span className="text-sm text-slate-400">转账金额</span>
                  <span className="font-semibold text-white text-lg">
                    {data.amount_pot.toLocaleString(undefined, { maximumFractionDigits: 6 })} POT
                  </span>
                </div>
                <div className="flex justify-between items-center px-4 py-3">
                  <span className="text-sm text-slate-400">预估 Gas 费</span>
                  <span className="text-sm text-slate-300">
                    {data.estimated_fee_formatted ?? "计算中..."}
                  </span>
                </div>
                <div className="flex justify-between items-center px-4 py-3">
                  <span className="text-sm text-slate-400">操作类型</span>
                  <span className="text-xs font-mono text-portal-400 bg-portal-900/40 px-2 py-0.5 rounded">
                    {data.call_module}.{data.call_function}
                  </span>
                </div>
              </div>

              <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-900/20 border border-amber-500/30 mb-5">
                <AlertTriangle size={15} className="text-amber-400 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-amber-300">
                  请在钱包扩展中仔细核对收款地址和金额，链上交易不可撤销。
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={onClose}
                  className="flex-1 py-2.5 rounded-xl border border-slate-600 text-slate-300 hover:bg-slate-800 text-sm transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleConfirm}
                  className="flex-1 py-2.5 rounded-xl bg-portal-600 hover:bg-portal-500 text-white font-medium text-sm transition-colors"
                >
                  确认发送
                </button>
              </div>
            </>
          )}

          {/* Signing / Pending Phase */}
          {phase === "signing" && (
            <div className="text-center py-6">
              <Loader2 size={40} className="animate-spin text-portal-400 mx-auto mb-4" />
              <p className="text-slate-300 font-medium mb-2">交易处理中</p>
              <p className="text-sm text-slate-400">{statusText}</p>
            </div>
          )}

          {/* Success Phase */}
          {phase === "success" && result && (
            <div className="text-center py-4">
              <CheckCircle size={40} className="text-green-400 mx-auto mb-3" />
              <p className="font-semibold text-slate-100 mb-4">交易已成功上链！</p>
              {result.txHash && (
                <div className="text-left rounded-xl bg-slate-800 border border-slate-700 p-3 mb-4">
                  <p className="text-xs text-slate-400 mb-1">交易 Hash</p>
                  <p className="text-xs font-mono text-green-400 break-all">{result.txHash}</p>
                  {result.blockHash && (
                    <>
                      <p className="text-xs text-slate-400 mt-2 mb-1">区块 Hash</p>
                      <p className="text-xs font-mono text-slate-300 break-all">{result.blockHash}</p>
                    </>
                  )}
                </div>
              )}
              <button
                onClick={onClose}
                className="w-full py-2.5 rounded-xl bg-green-700 hover:bg-green-600 text-white font-medium text-sm transition-colors"
              >
                完成
              </button>
            </div>
          )}

          {/* Error Phase */}
          {phase === "error" && result && (
            <div className="text-center py-4">
              <XCircle size={40} className="text-red-400 mx-auto mb-3" />
              <p className="font-semibold text-slate-100 mb-2">交易失败</p>
              <p className="text-sm text-red-400 mb-4">{result.error}</p>
              <div className="flex gap-3">
                <button
                  onClick={onClose}
                  className="flex-1 py-2.5 rounded-xl border border-slate-600 text-slate-300 hover:bg-slate-800 text-sm transition-colors"
                >
                  关闭
                </button>
                <button
                  onClick={() => setPhase("confirm")}
                  className="flex-1 py-2.5 rounded-xl bg-portal-600 hover:bg-portal-500 text-white text-sm transition-colors"
                >
                  重试
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
