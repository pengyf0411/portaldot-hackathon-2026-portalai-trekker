"""
main.py — PortalAI FastAPI backend.

Endpoints:
  POST /chat          — Parse user message and return chain data or tx_preview
  GET  /health        — Health check
  GET  /balance/{address}  — Direct balance query (utility)
  GET  /validators    — Direct validator list query (utility)
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from llm_agent import parse_intent, get_unknown_intent_response
from intent_handlers import dispatch

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("PortalAI backend starting up...")
    logger.info(f"Portaldot node: {os.getenv('PORTALDOT_WS_URL', 'wss://mainnet.portaldot.io')}")
    yield
    logger.info("PortalAI backend shutting down...")


app = FastAPI(
    title="PortalAI Backend",
    description="AI-powered Portaldot onchain assistant backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend origin (configured in .env)
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request / Response Models ──────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    user_address: Optional[str] = None  # Connected wallet address from frontend


class ChatResponse(BaseModel):
    intent: str
    display_type: str        # "balance" | "tx_preview" | "fee_info" | "validators" | "tx_history" | "text" | "error"
    message: str
    data: Optional[dict] = None  # Additional structured data for the frontend to render


# ─── Routes ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "PortalAI Backend"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Main chat endpoint.

    Flow:
      1. LLM parses user message into structured intent + params
      2. Intent handler queries chain (READ) or builds tx preview (WRITE)
      3. Returns structured response for frontend rendering

    For WRITE intents (transfer), the response contains `call_module`,
    `call_function`, and `call_params` for the frontend to assemble and
    sign the extrinsic via @polkadot/api + wallet extension.
    """
    user_message = req.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    logger.info(f"Chat request | address={req.user_address} | message={user_message[:80]}")

    # Step 1: Parse intent via LLM
    parsed = parse_intent(user_message, user_address=req.user_address)

    # Step 2: Dispatch to handler
    if parsed.intent == "unknown":
        result = get_unknown_intent_response()
    else:
        result = dispatch(parsed.intent, parsed.params)

    # Step 3: Build unified response
    display_type = result.get("display_type", "text")
    message = result.get("message", "")

    # Extract top-level keys as data payload for the frontend
    data_keys = {k for k in result if k not in ("intent", "display_type", "message")}
    data = {k: result[k] for k in data_keys} if data_keys else None

    logger.info(f"Chat response | intent={result.get('intent')} | display_type={display_type}")

    return ChatResponse(
        intent=result.get("intent", parsed.intent),
        display_type=display_type,
        message=message,
        data=data,
    )


@app.get("/balance/{address}")
async def get_balance(address: str):
    """Direct balance query endpoint (useful for testing)."""
    from chain_client import query_balance
    from validators import validate_ss58_address, ValidationError
    try:
        validate_ss58_address(address)
        data = query_balance(address)
        return data
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/validators")
async def get_validators(limit: int = 10):
    """Direct validator list endpoint (useful for testing)."""
    from chain_client import query_validators
    try:
        return query_validators(limit=min(limit, 50))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
