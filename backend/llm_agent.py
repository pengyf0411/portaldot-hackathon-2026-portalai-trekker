"""
llm_agent.py — OpenAI GPT-4o-mini Function Calling for intent recognition.

Maps natural language user input to one of 5 structured intents:
  - query_balance
  - transfer
  - estimate_fee
  - query_validators
  - query_tx_history

Unknown inputs are gracefully handled with a helpful fallback message.
"""

import os
import json
import logging
from typing import Optional
from openai import OpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

SUPPORTED_INTENTS = [
    "query_balance",
    "transfer",
    "estimate_fee",
    "query_validators",
    "query_tx_history",
    "unknown_intent",
]

UNKNOWN_INTENT_MESSAGE = (
    "I only support the following operations. Please rephrase your request:\n"
    "• Check balance (e.g. What is my POT balance?)\n"
    "• Transfer (e.g. Send 10 POT to address 5Gxxx)\n"
    "• Estimate gas fee (e.g. How much gas to send 5 POT?)\n"
    "• List validators (e.g. Show active validators)\n"
    "• Transaction history (e.g. My recent transfers)"
)

# Tool definitions for OpenAI Function Calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_balance",
            "description": (
                "Query the POT token balance of the current user or a specific address. "
                "Use when the user asks about their balance, how much POT they have, "
                "or the balance of another address."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": (
                            "The Portaldot SS58 address to query. "
                            "If the user refers to 'my balance', leave this empty — "
                            "the backend will use the connected wallet address."
                        ),
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer",
            "description": (
                "Transfer POT tokens to another address. "
                "Use when the user says 'send', 'transfer', 'pay', or similar verbs "
                "with an amount and a destination address."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Destination Portaldot SS58 address (starts with '5').",
                    },
                    "amount_pot": {
                        "type": "number",
                        "description": "Amount of POT to transfer (a positive number).",
                    },
                },
                "required": ["to", "amount_pot"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_fee",
            "description": (
                "Estimate the gas fee for transferring POT. "
                "Use when the user asks about fee, gas cost, transaction cost, "
                "or how much it costs to send a certain amount."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": (
                            "Destination address for fee estimation. "
                            "Can be omitted — a default address will be used for estimation."
                        ),
                    },
                    "amount_pot": {
                        "type": "number",
                        "description": "Amount of POT to estimate the fee for.",
                    },
                },
                "required": ["amount_pot"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_validators",
            "description": (
                "List active validators on the Portaldot network. "
                "Use when the user asks about validators, staking nodes, "
                "or active network participants."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of validators to return (default 10).",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_tx_history",
            "description": (
                "Query recent transfer transaction history for the user's address. "
                "Use when the user asks about their recent transactions, transfer history, "
                "sent/received records."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of transactions to return (default 10).",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "unknown_intent",
            "description": (
                "Use this when the user's request does NOT match any of the five supported operations. "
                "Triggers include: greetings, questions about PortalAI itself, requests to stake/unstake, "
                "NFT queries, governance votes, or any other off-topic input. "
                "Do NOT use this as a fallback when the intent is unclear — try the best matching tool first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_intent": {
                        "type": "string",
                        "description": "One-sentence description of what the user seemed to want.",
                    }
                },
                "required": [],
            },
        },
    },
]

SYSTEM_PROMPT = """You are PortalAI, an AI assistant for the Portaldot blockchain.
Your role is to understand the user's intent and extract structured parameters for blockchain operations.

You MUST call one of the provided tools for every user message.
Do NOT respond in plain text — always use a tool call.

Portaldot uses POT as its native token. SS58 addresses start with '5' and are 47-48 characters long.
Users may write in English or Chinese; map their intent to the correct tool regardless of language.

Supported operations: query_balance, transfer, estimate_fee, query_validators, query_tx_history.
If the user's request clearly does not match any of these five operations, call unknown_intent.
When in doubt, try the most relevant operation tool — only fall back to unknown_intent for clearly off-topic requests."""


class ParsedIntent(BaseModel):
    intent: str
    params: dict
    raw_message: str


def _make_client() -> OpenAI:
    """
    Build an OpenAI-compatible client.
    Supports OpenAI and any compatible provider (DeepSeek, etc.)
    by reading LLM_BASE_URL from the environment.

    DeepSeek example in .env:
        OPENAI_API_KEY=sk-...          # DeepSeek key
        LLM_BASE_URL=https://api.deepseek.com
        LLM_MODEL=deepseek-chat
    """
    base_url = os.getenv("LLM_BASE_URL") or None   # None = use OpenAI default
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=base_url)


def parse_intent(user_message: str, user_address: Optional[str] = None) -> ParsedIntent:
    """
    Parse user natural language message into a structured intent using Function Calling.

    Supports OpenAI and DeepSeek (OpenAI-compatible) via LLM_BASE_URL env var.

    Args:
        user_message: The user's input text.
        user_address: The connected wallet address, injected into context if available.

    Returns:
        ParsedIntent with intent name and extracted parameters.
    """
    client = _make_client()

    context_note = ""
    if user_address:
        context_note = f"\nThe user's connected wallet address is: {user_address}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + context_note},
        {"role": "user", "content": user_message},
    ]

    try:
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="required",  # Force a tool call every time
            temperature=0,
        )

        message = response.choices[0].message

        if not message.tool_calls:
            logger.warning("LLM returned no tool calls despite tool_choice=required")
            return ParsedIntent(
                intent="unknown",
                params={},
                raw_message=user_message,
            )

        tool_call = message.tool_calls[0]
        intent_name = tool_call.function.name
        try:
            params = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            params = {}

        # Normalize unknown_intent tool call to the canonical "unknown" intent
        if intent_name == "unknown_intent":
            logger.info(f"LLM signaled unknown intent | user_intent={params.get('user_intent', '')}")
            return ParsedIntent(intent="unknown", params=params, raw_message=user_message)

        # Fill in user address for intents that may need it
        if user_address:
            if intent_name == "query_balance" and not params.get("address"):
                params["address"] = user_address
            if intent_name == "query_tx_history" and not params.get("address"):
                params["address"] = user_address
            if intent_name == "estimate_fee" and not params.get("from_address"):
                params["from_address"] = user_address
            if intent_name == "transfer" and not params.get("from_address"):
                params["from_address"] = user_address

        logger.info(f"Parsed intent: {intent_name} | params: {params}")

        return ParsedIntent(
            intent=intent_name,
            params=params,
            raw_message=user_message,
        )

    except Exception as e:
        logger.error(f"LLM intent parsing failed: {e}")
        return ParsedIntent(
            intent="unknown",
            params={"error": str(e)},
            raw_message=user_message,
        )


def get_unknown_intent_response() -> dict:
    return {
        "intent": "unknown",
        "display_type": "text",
        "message": UNKNOWN_INTENT_MESSAGE,
    }
