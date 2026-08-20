# PS-02 Backend — How to Run

## 🚀 1-Command Quickstart (Runs All 4 Servers)

From the project root directory, run:

```powershell
python backend/services/run_all.py
```

This single command starts all 4 microservices with hot-reload enabled:

| Server | Port | Swagger UI / Documentation |
| :--- | :--- | :--- |
| **Server 1: Core / API Server** | `8000` | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| **Server 2: Event + Intelligence Server** | `8001` | [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) |
| **Server 3: Action + Commission Server** | `8002` | [http://127.0.0.1:8002/docs](http://127.0.0.1:8002/docs) |
| **Server 4: Audit + Blockchain Server** | `8003` | [http://127.0.0.1:8003/docs](http://127.0.0.1:8003/docs) |

---

## ⚙️ Connecting to Supabase

To connect all 4 servers directly to your live Supabase PostgreSQL database:

1. Create a `.env` file in the project root:
```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@[YOUR-SUPABASE-HOST]:5432/postgres
SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
SUPABASE_KEY=[YOUR-SUPABASE-ANON-KEY]
```
*(If no `.env` is supplied, it automatically uses local SQLite storage for seamless development without configuration).*

---

## 🧪 Running the Automated Test Suite

Run the full 20-test suite across all 4 servers, 3 agents, hash-chain integrity, and idempotency:

```powershell
python -m pytest tests/ -v
```

---

## 🖥️ Running Individual Servers Separately

If you prefer running each server in a dedicated terminal window:

```powershell
# Terminal 1: Core API Gateway
uvicorn backend.services.core_server.main:app --port 8000 --reload

# Terminal 2: Event & Intelligence (Agents)
uvicorn backend.services.event_intelligence_server.main:app --port 8001 --reload

# Terminal 3: Action & Commission Engine
uvicorn backend.services.action_commission_server.main:app --port 8002 --reload

# Terminal 4: Audit & Cryptographic Proofs
uvicorn backend.services.audit_blockchain_server.main:app --port 8003 --reload
```
