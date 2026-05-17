# PortalAI — AI-Powered Portaldot Onchain Copilot

> **Portaldot Online Mini Hackathon S1 · Track: AI-Powered Onchain Workflows**

PortalAI is a conversational AI assistant that lets you interact with the Portaldot blockchain using plain language. No CLI, no raw hex, no guesswork — just type what you want to do.

---

## Demo

> 📹 Demo video: [TBD — will be added before submission deadline]

**Supported operations:**

| What you type | What happens |
|---|---|
| "我的 POT 余额是多少？" | Queries your wallet balance from the chain |
| "转 10 POT 给地址 5Gxxx…" | Shows tx preview → you click confirm → wallet signs → sent |
| "转 5 POT 手续费是多少？" | Estimates gas fee via RPC |
| "查看活跃验证节点" | Lists current validators with commission rates |
| "我最近的交易记录" | Scans last 1,000 blocks for your transfers |

---

## Architecture

```
User (Browser)
  │
  ├─ Next.js Frontend
  │    ├─ ChatWindow    — conversation UI
  │    ├─ WalletButton  — connects Portaldot Extension
  │    ├─ TxConfirmModal — shows tx details before signing
  │    └─ lib/extrinsic.ts — @polkadot/api signs & submits
  │
  │  POST /chat (user message + wallet address)
  │
  ├─ FastAPI Backend
  │    ├─ llm_agent.py  — OpenAI GPT-4o-mini Function Calling
  │    ├─ chain_client.py — substrate-interface READ queries
  │    └─ intent_handlers.py — 5 handlers, POT 14-decimal aware
  │
  └─ Portaldot Mainnet  wss://mainnet.portaldot.io
       └─ ink! SavedMacros contract (on-chain macro storage)
```

**Key design principle:** Private keys never leave the browser. The backend only performs READ operations. All WRITE operations (extrinsic signing + submission) happen in the frontend via `@polkadot/api` + the user's wallet extension.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Blockchain | Portaldot (Substrate, LAO NPoS) |
| Smart Contract | ink! v5 (`saved_macros`) |
| Chain SDK | `substrate-interface` (Python) |
| AI / NLU | OpenAI GPT-4o-mini Function Calling |
| Backend | Python 3.11 + FastAPI |
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Wallet | `@polkadot/extension-dapp` + `@polkadot/api` |
| Token | POT (14 decimals, 1 POT = 10¹⁴ planck) |

---

## Project Structure

```
portaldot-ai-copilot/
├── contracts/
│   └── saved_macros/       # ink! smart contract
│       ├── Cargo.toml
│       └── lib.rs
├── backend/
│   ├── main.py             # FastAPI entrypoint
│   ├── llm_agent.py        # GPT-4o-mini intent parser
│   ├── chain_client.py     # Portaldot RPC wrapper
│   ├── intent_handlers.py  # 5 intent handlers
│   ├── validators.py       # SS58 + amount validation
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   └── page.tsx        # Main page
│   ├── components/
│   │   ├── ChatWindow.tsx  # Conversation UI + response cards
│   │   ├── TxConfirmModal.tsx
│   │   └── WalletButton.tsx
│   ├── lib/
│   │   ├── polkadot.ts     # Wallet connection helpers
│   │   └── extrinsic.ts    # Extrinsic assembly + submission
│   └── package.json
└── README.md
```

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- Rust + `cargo-contract` (for ink! contract builds)
- [Portaldot Extension](https://chromewebstore.google.com/detail/portaldot-extension/cpdecangbhmfijmlmjglfcocfpaojceo) or Polkadot.js Extension
- OpenAI API key

### 1. Run local Portaldot testnet node (recommended during dev)

Download the testnet binary from [Chain Info](https://portaldot-dev.readthedocs.io/en/latest/chain-info.html) and run:

```bash
# Linux/macOS
./portaldot_dev --dev --alice
```

### 2. Build the ink! contract

> **Note**: Portaldot runs on Substrate 2.x (Metadata V13). Use Rust 1.85.0 and cargo-contract 5.0.3 for compilation. Deploy via the Portaldot Web Explorer (see below).

```bash
# Install toolchain
rustup install 1.85.0
rustup component add rust-src --toolchain 1.85.0
rustup target add wasm32-unknown-unknown --toolchain 1.85.0
cargo install cargo-contract

cd contracts/saved_macros
rustup override set 1.85.0
cargo +1.85.0 contract build --release
```

Pre-built artifacts are included at `contracts/saved_macros/target/ink/`.

### 3. Deploy via Portaldot Web Explorer

1. Open [https://www.portaldot.io/](https://www.portaldot.io/) → select **Local Node** (or Mainnet)
2. Go to **Developer → Contracts → Upload & Deploy**
3. Upload `saved_macros.wasm` and `saved_macros.json`
4. Set constructor to `new`, click **Deploy**
5. Copy the deployed contract address into `backend/.env` and `frontend/.env.local`

### 3. Start the backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Fill in OPENAI_API_KEY and PORTALDOT_WS_URL in .env
uvicorn main:app --reload --port 8000
```

### 4. Start the frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Fill in NEXT_PUBLIC_API_URL and NEXT_PUBLIC_WS_URL
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Mainnet Deployment

### Smart Contract

Deployed on Portaldot Mainnet (`wss://mainnet.portaldot.io`):

```
Contract Address: [TO BE FILLED AFTER MAINNET DEPLOY]
```

### Backend

Set in `backend/.env`:
```
PORTALDOT_WS_URL=wss://mainnet.portaldot.io
CONTRACT_ADDRESS=<deployed address>
```

### Frontend

Set in `frontend/.env.local`:
```
NEXT_PUBLIC_WS_URL=wss://mainnet.portaldot.io
NEXT_PUBLIC_CONTRACT_ADDRESS=<deployed address>
```

---

## ink! Contract — SavedMacros

Users can save frequently-used AI commands as on-chain macros (e.g., "Send 5 POT to Alice every week"). Macros are stored per account, max 10 per user.

```rust
// Save a macro
save_macro(name: String, intent: String, params: String) -> Result<()>

// Delete a macro by name
delete_macro(name: String) -> Result<()>

// Read all macros for the caller
get_macros() -> Vec<Macro>
```

All contract interactions consume POT as gas, fulfilling the hackathon's native deployment requirement.

---

## Judging Criteria Alignment

| Criterion | How PortalAI satisfies it |
|---|---|
| **Portaldot Native Deployment** | ink! contract deployed on mainnet; all txs use POT as gas |
| **Demo Completion** | Full end-to-end MVP: NL input → AI parse → chain op → result |
| **Application Value** | Lowers UX barrier for non-technical Portaldot users |
| **Presentation Quality** | Clean chat UI, rich response cards, one-click tx confirmation |

---

## License

MIT
