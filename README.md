# PortalAI Copilot (DEMO)

> **Portaldot Online Mini Hackathon S1 · Track: AI-Powered Onchain Workflows**

---

## Project Overview

### Problem Statement

Interacting with Substrate-based chains like Portaldot typically requires understanding extrinsics, SS58 addresses, decimal precision, and wallet tooling. Non-technical users face a steep learning curve, and even developers lose time navigating explorers and CLI commands for routine tasks such as balance checks, fee estimates, and transfers.

### Solution

PortalAI Copilot is a conversational AI assistant that turns natural language into Portaldot onchain actions. Users connect a browser wallet, type plain English requests, and receive structured responses with one-click transaction confirmation for write operations. Private keys never leave the browser — the backend performs read-only chain queries while the frontend handles signing via `@polkadot/api`.

### Blockchain Relevance

- Built natively for **Portaldot** (Substrate 2.x, LAO NPoS consensus)
- All transfers and queries use **POT** (14-decimal native token) as gas and value
- Supports core **Balances** pallet operations: balance query, fee estimate, transfer, tx history
- Includes an **ink! v5 SavedMacros** contract (source + pre-built artifacts) for on-chain macro storage — optional extension beyond the MVP demo
- Demonstrates **AI-Powered Onchain Workflows**: NLU intent parsing → validated chain parameters → wallet-signed extrinsics

---

## Technical Architecture

### Architecture Diagram

```
User (Browser)
  │
  ├─ Next.js Frontend (localhost:3000)
  │    ├─ ChatWindow       — conversation UI + suggestion chips
  │    ├─ WalletButton     — Portaldot / Polkadot.js Extension
  │    ├─ TxConfirmModal   — tx preview before signing
  │    └─ lib/extrinsic.ts — @polkadot/api signs & submits extrinsics
  │
  │  POST /chat  { message, user_address }
  │
  ├─ FastAPI Backend (localhost:8000)
  │    ├─ llm_agent.py       — OpenAI GPT-4o-mini Function Calling
  │    ├─ chain_client.py     — substrate-interface READ queries
  │    ├─ intent_handlers.py  — 6 intent handlers (POT 14-decimal aware)
  │    └─ validators.py       — SS58 address + amount validation
  │
  └─ Portaldot Node
       ws://127.0.0.1:9944  (local dev)
       wss://mainnet.portaldot.io  (production)
```

**Security model:** Backend = read-only. Frontend = write (sign + submit). OpenAI API key stays server-side.

### Core Tech Stack


| Layer                   | Technology                                   |
| ----------------------- | -------------------------------------------- |
| Blockchain Platform     | Portaldot (Substrate 2.x, Metadata V13)      |
| Smart Contract Language | ink! v5 (Rust) — SavedMacros contract        |
| Chain SDK (Backend)     | `substrate-interface` (Python)               |
| AI / NLU                | OpenAI GPT-4o-mini Function Calling          |
| Backend                 | Python 3.11 + FastAPI + Uvicorn              |
| Frontend Framework      | Next.js 14 + TypeScript + Tailwind CSS       |
| Wallet Integration      | `@polkadot/extension-dapp` + `@polkadot/api` |
| Native Token            | POT (14 decimals, 1 POT = 10¹⁴ planck)       |


### Project Structure

```
portaldot-ai-copilot/
├── contracts/saved_macros/   # ink! smart contract source + build artifacts
├── backend/                  # FastAPI server
├── frontend/                 # Next.js app
├── start.bat                 # One-click local startup script (Windows)
├── LICENSE                   # MIT
└── README.md
```

---

## Smart Contracts

### Directory

`contracts/saved_macros/`

### Key Contracts

**SavedMacros** — stores user-defined command macros on-chain (max 10 per account).


| Function                           | Description                                   |
| ---------------------------------- | --------------------------------------------- |
| `new()`                            | Constructor — initializes empty macro storage |
| `save_macro(name, intent, params)` | Save a named macro with intent + JSON params  |
| `delete_macro(name)`               | Remove a macro by name                        |
| `get_macros()`                     | Return all macros for the caller              |


### Deployment

Pre-built artifacts: `contracts/saved_macros/target/ink/saved_macros.contract`

```bash
# Build (requires Rust 1.85.0 + cargo-contract 5.0.3)
cd contracts/saved_macros
rustup override set 1.85.0
cargo +1.85.0 contract build --release
```

Deploy via [Portaldot Web Explorer](https://www.portaldot.io/) → Developer → Contracts → Upload & Deploy.

> **Note:** The MVP demo runs fully on native Balances pallet operations without requiring contract deployment. Contract source and artifacts are included for hackathon completeness.

---

## Installation & Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Rust + `cargo-contract` (only if rebuilding the ink! contract)
- [Portaldot Extension](https://chromewebstore.google.com/detail/portaldot-extension/cpdecangbhmfijmlmjglfcocfpaojceo) or Polkadot.js Extension
- OpenAI API key

### Steps

**1. Clone**

```bash
git clone https://github.com/pengyf0411/portaldot-ai-copilot.git
cd portaldot-ai-copilot
```

**2. Run local Portaldot node**

Download the dev binary from [Chain Info](https://portaldot-dev.readthedocs.io/en/latest/chain-info.html):

```bash
./portaldot_dev --dev --alice --force-authoring
```

**3. Install & start backend**

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Set OPENAI_API_KEY and PORTALDOT_WS_URL=ws://127.0.0.1:9944
uvicorn main:app --reload --port 8000
```

**4. Install & start frontend**

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
# Set NEXT_PUBLIC_WS_URL=ws://127.0.0.1:9944
npm run dev
```

**5. Open** [http://localhost:3000](http://localhost:3000), click **Connect Wallet**, and start chatting.

### Supported Operations


| User Input (example)           | Action                                                |
| ------------------------------ | ----------------------------------------------------- |
| "What is my POT balance?"      | Queries wallet balance from chain                     |
| "Transfer 10 POT to 5Gxxx…"    | Shows tx preview → confirm → wallet signs → submitted |
| "How much fee to send 10 POT?" | Estimates transfer gas fee                            |
| "Show active validators"       | Lists current validators with commission rates        |
| "Show my recent transfers"     | Scans recent blocks for transfer history              |


---

## Demo

### Demo Video

> 📹 **Demo Video:** [PortalAI — AI Copilot for Portaldot | Hackathon S1 Demo - YouTube](https://www.youtube.com/watch?v=64_78qLyd1c)

### Demo Flow (shown in video)

1. Connect wallet via Portaldot / Polkadot.js Extension
2. Query account POT balance
3. Estimate fee for a 10 POT transfer
4. Transfer 10 POT to a target SS58 address (wallet signing)
5. Verify updated balance
6. Query recent transfer history

### Live Demo (optional)

Run locally following the Installation steps above.

### Test Accounts

Use the Portaldot dev node **Alice** account (pre-funded) or import your own account via the browser extension. For local dev, fund your account by transferring POT from Alice via [Portaldot.js Apps](https://www.portaldot.io/?rpc=ws%3A%2F%2F127.0.0.1%3A9944).

---

## Roadmap

### Completed (Hackathon MVP)

- Natural language intent parsing (6 intents + unknown-intent fallback)
- Balance query, fee estimate, transfer preview + signing, tx history, validator list
- Wallet connection with dynamic welcome message refresh
- Transaction confirmation modal with status tracking
- Custom SCALE decoder for tx history on Portaldot Metadata V13
- Full English UI for reviewer accessibility
- End-to-end demo on local Portaldot dev node

### Next Phase

- Deploy SavedMacros ink! contract to Portaldot mainnet
- On-chain macro save / execute workflow
- Mainnet deployment of frontend + backend
- Additional intents (staking, governance, contract calls)
- Multi-turn conversation context

---

## Team


| Name    | Role                                                      | Contact                                              |
| ------- | --------------------------------------------------------- | ---------------------------------------------------- |
| Trekker | Solo Developer — Full Stack (AI, Backend, Frontend, ink!) | GitHub: [@pengyf0411](https://github.com/pengyf0411) |


**Team Name:** Trekker

**Hackathon Track:** AI-Powered Onchain Workflows

---

## License

This project is licensed under the [MIT License](LICENSE).