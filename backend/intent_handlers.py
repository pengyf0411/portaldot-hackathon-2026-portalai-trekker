"""
intent_handlers.py — Orchestrates chain queries and builds frontend-ready responses.

For READ intents: queries the chain and returns formatted data.
For WRITE intents (transfer): validates params and returns call parameters
  for the frontend to assemble, sign, and submit the extrinsic.

POT decimals: 14 (1 POT = 10^14 planck). This is enforced in chain_client.py.
"""

import logging
from typing import Optional
from chain_client import (
    query_balance,
    estimate_transfer_fee,
    build_transfer_call_params,
    query_validators,
    query_tx_history,
    planck_to_pot,
    POT_DECIMALS,
)
from validators import (
    ValidationError,
    validate_transfer_params,
    validate_estimate_fee_params,
    validate_query_balance_params,
    validate_query_tx_history_params,
    validate_query_validators_params,
)

logger = logging.getLogger(__name__)

# Fallback destination for fee estimation when no 'to' is provided
FEE_ESTIMATION_FALLBACK_ADDR = "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"


def _format_pot(amount: float) -> str:
    """Format POT amount for display, showing up to 6 significant digits."""
    if amount == 0:
        return "0 POT"
    if amount >= 1:
        return f"{amount:,.6f} POT"
    return f"{amount:.{POT_DECIMALS}f} POT".rstrip("0").rstrip(".")


def handle_query_balance(params: dict) -> dict:
    """
    Handle 'query_balance' intent.

    Response display_type: "balance"
    """
    try:
        cleaned = validate_query_balance_params(params)
        address = cleaned["address"]
        if not address:
            return {
                "intent": "query_balance",
                "display_type": "error",
                "message": "请先连接钱包，或提供要查询的地址",
            }

        data = query_balance(address)
        return {
            "intent": "query_balance",
            "display_type": "balance",
            "address": data["address"],
            "free_pot": data["free_pot"],
            "reserved_pot": data["reserved_pot"],
            "total_pot": data["total_pot"],
            "free_formatted": _format_pot(data["free_pot"]),
            "reserved_formatted": _format_pot(data["reserved_pot"]),
            "total_formatted": _format_pot(data["total_pot"]),
            "message": f"地址 {address[:8]}...{address[-6:]} 的可用余额为 {_format_pot(data['free_pot'])}",
        }
    except ValidationError as e:
        return {"intent": "query_balance", "display_type": "error", "message": e.message}
    except Exception as e:
        logger.error(f"query_balance error: {e}")
        return {"intent": "query_balance", "display_type": "error", "message": f"查询失败：{e}"}


def handle_transfer(params: dict) -> dict:
    """
    Handle 'transfer' intent.

    Does NOT execute the transfer. Returns call parameters for the frontend
    to assemble and sign via @polkadot/api + wallet extension.

    Response display_type: "tx_preview"
    """
    try:
        cleaned = validate_transfer_params(params)
        to = cleaned["to"]
        amount_pot = cleaned["amount_pot"]
        from_address = cleaned.get("from_address")

        # Optionally check sender balance (only if we have the address)
        balance_info = None
        if from_address:
            try:
                balance_info = query_balance(from_address)
                if balance_info["free_pot"] < amount_pot:
                    return {
                        "intent": "transfer",
                        "display_type": "error",
                        "message": (
                            f"余额不足：账户仅有 {_format_pot(balance_info['free_pot'])}，"
                            f"无法转出 {_format_pot(amount_pot)}"
                        ),
                    }
            except Exception as e:
                logger.warning(f"Balance pre-check failed (non-fatal): {e}")

        call_params = build_transfer_call_params(to, amount_pot)

        # Estimate fee for display
        fee_info = None
        if from_address:
            fee_info = estimate_transfer_fee(from_address, to, amount_pot)

        is_fixed = fee_info.get("is_fixed_estimate", False) if fee_info else False
        fee_formatted = (
            f"≈ {_format_pot(fee_info['estimated_fee_pot'])}（近似值）" if (fee_info and is_fixed)
            else _format_pot(fee_info["estimated_fee_pot"]) if fee_info
            else "未知"
        )

        return {
            "intent": "transfer",
            "display_type": "tx_preview",
            "requires_confirmation": True,
            "call_module": call_params["call_module"],
            "call_function": call_params["call_function"],
            "call_params": call_params["call_params"],
            "amount_pot": amount_pot,
            "amount_planck": call_params["amount_planck"],
            "to": to,
            "from": from_address,
            "estimated_fee_pot": fee_info["estimated_fee_pot"] if fee_info else None,
            "estimated_fee_formatted": fee_formatted,
            "message": (
                f"准备转账 {_format_pot(amount_pot)} 给 {to[:8]}...{to[-6:]}\n"
                f"预计 gas 费：{fee_formatted}"
            ),
        }
    except ValidationError as e:
        return {"intent": "transfer", "display_type": "error", "message": e.message}
    except Exception as e:
        logger.error(f"transfer handler error: {e}")
        return {"intent": "transfer", "display_type": "error", "message": f"处理失败：{e}"}


def handle_estimate_fee(params: dict) -> dict:
    """
    Handle 'estimate_fee' intent.

    Response display_type: "fee_info"
    """
    try:
        cleaned = validate_estimate_fee_params(params)
        amount_pot = cleaned["amount_pot"]
        to = cleaned.get("to") or FEE_ESTIMATION_FALLBACK_ADDR
        from_address = cleaned.get("from_address") or FEE_ESTIMATION_FALLBACK_ADDR

        fee_info = estimate_transfer_fee(from_address, to, amount_pot)
        is_fixed = fee_info.get("is_fixed_estimate", False)
        fee_label = f"≈ {_format_pot(fee_info['estimated_fee_pot'])}（近似值）" if is_fixed else _format_pot(fee_info["estimated_fee_pot"])
        return {
            "intent": "estimate_fee",
            "display_type": "fee_info",
            "amount_pot": amount_pot,
            "amount_formatted": _format_pot(amount_pot),
            "estimated_fee_pot": fee_info["estimated_fee_pot"],
            "estimated_fee_planck": fee_info["estimated_fee_planck"],
            "estimated_fee_formatted": fee_label,
            "is_fixed_estimate": is_fixed,
            "message": f"转账 {_format_pot(amount_pot)} 预计 gas 费约 {fee_label}",
        }
    except ValidationError as e:
        return {"intent": "estimate_fee", "display_type": "error", "message": e.message}
    except Exception as e:
        logger.error(f"estimate_fee error: {e}")
        return {"intent": "estimate_fee", "display_type": "error", "message": f"估算失败：{e}"}


def handle_query_validators(params: dict) -> dict:
    """
    Handle 'query_validators' intent.

    Response display_type: "validators"
    """
    try:
        cleaned = validate_query_validators_params(params)
        limit = cleaned["limit"]

        data = query_validators(limit=limit)
        return {
            "intent": "query_validators",
            "display_type": "validators",
            "validators": data["validators"],
            "total_count": data["total_count"],
            "shown_count": len(data["validators"]),
            "message": f"当前共有 {data['total_count']} 个活跃验证节点，显示前 {len(data['validators'])} 个",
        }
    except ValidationError as e:
        return {"intent": "query_validators", "display_type": "error", "message": e.message}
    except Exception as e:
        logger.error(f"query_validators error: {e}")
        return {"intent": "query_validators", "display_type": "error", "message": f"查询失败：{e}"}


def handle_query_tx_history(params: dict) -> dict:
    """
    Handle 'query_tx_history' intent.

    Scans the last 1000 blocks for Transfer events (see chain_client.py).
    Response display_type: "tx_history"
    """
    try:
        cleaned = validate_query_tx_history_params(params)
        address = cleaned["address"]
        limit = cleaned["limit"]

        if not address:
            return {
                "intent": "query_tx_history",
                "display_type": "error",
                "message": "请先连接钱包，才能查询交易记录",
            }

        data = query_tx_history(address, limit=limit)
        txs = data["transactions"]

        for tx in txs:
            tx["amount_formatted"] = _format_pot(tx["amount_pot"])

        return {
            "intent": "query_tx_history",
            "display_type": "tx_history",
            "address": address,
            "transactions": txs,
            "count": len(txs),
            "scanned_blocks": data["scanned_blocks"],
            "message": (
                f"在最近 {data['scanned_blocks']} 个区块中找到 {len(txs)} 笔相关交易"
                if txs
                else f"在最近 {data['scanned_blocks']} 个区块中未找到相关交易记录"
            ),
        }
    except ValidationError as e:
        return {"intent": "query_tx_history", "display_type": "error", "message": e.message}
    except Exception as e:
        logger.error(f"query_tx_history error: {e}")
        return {"intent": "query_tx_history", "display_type": "error", "message": f"查询失败：{e}"}


# Dispatch table mapping intent name -> handler function
INTENT_HANDLERS = {
    "query_balance": handle_query_balance,
    "transfer": handle_transfer,
    "estimate_fee": handle_estimate_fee,
    "query_validators": handle_query_validators,
    "query_tx_history": handle_query_tx_history,
}


def dispatch(intent: str, params: dict) -> dict:
    """Route an intent to its handler. Returns error dict for unknown intents."""
    handler = INTENT_HANDLERS.get(intent)
    if not handler:
        from llm_agent import get_unknown_intent_response
        return get_unknown_intent_response()
    return handler(params)
