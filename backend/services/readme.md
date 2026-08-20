# PS-02: Event-Driven Sales Intelligence & Actionable CRM
## Complete Backend Service Layer Reference & Testing Guide

This documentation provides comprehensive architectural details, functional endpoint directories, exact parameter formats, and testing procedures for all **four FastAPI microservices**.

---

## 🚀 1. Quickstart — Running the Microservices

### A. One-Command Launch (All 4 Servers)
From the project root directory, run:

```powershell
python backend/services/run_all.py
```

This starts all 4 servers concurrently with live hot-reload enabled:

| Microservice | Port | Base URL | Interactive OpenAPI Swagger UI |
| :--- | :---: | :--- | :--- |
| **Server 1: Core / API Gateway** | `8000` | `http://127.0.0.1:8000` | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| **Server 2: Event & Intelligence** | `8001` | `http://127.0.0.1:8001` | [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) |
| **Server 3: Action & Commission** | `8002` | `http://127.0.0.1:8002` | [http://127.0.0.1:8002/docs](http://127.0.0.1:8002/docs) |
| **Server 4: Audit & Blockchain** | `8003` | `http://127.0.0.1:8003` | [http://127.0.0.1:8003/docs](http://127.0.0.1:8003/docs) |

---

### B. Connecting to Supabase
To connect to your live Supabase database, create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@[YOUR-HOST]:5432/postgres
SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
SUPABASE_KEY=[YOUR-SUPABASE-ANON-KEY]
```
*(If `.env` is omitted, the backend defaults to local SQLite so you can test immediately with zero configuration).*

---

### C. Running Individual Servers Separately (Optional)
```powershell
# Terminal 1: Core API Gateway
uvicorn backend.services.core_server.main:app --port 8000 --reload

# Terminal 2: Event Ingestion & 3 Agents
uvicorn backend.services.event_intelligence_server.main:app --port 8001 --reload

# Terminal 3: Action Lifecycle & Deterministic Commission
uvicorn backend.services.action_commission_server.main:app --port 8002 --reload

# Terminal 4: SHA-256 Ledger & Blockchain Proofs
uvicorn backend.services.audit_blockchain_server.main:app --port 8003 --reload
```

---

## 🔑 2. Authentication & `X-Service-Token` Guide

When testing in Swagger UI, you can authenticate using either method:

### Method 1: Using `X-Service-Token` (Direct Admin/Service Access)
In any endpoint displaying the `X-Service-Token` header field, input:
```text
ps02-internal-service-hmac-token-2026
```
*(Grants full system service & admin privileges immediately).*

### Method 2: Using Bearer JWT Token (Role-Based User Access)
1. Send `POST /api/v1/auth/generate-token` with user credentials.
2. Copy the `access_token` from the response.
3. Click the green **Authorize 🔓** button at the top-right of Swagger UI and paste the token.
4. **Leave `X-Service-Token` completely blank** — the Authorize token is used automatically.

---

## 📚 3. Server-by-Server Endpoint & Parameter Reference

---

### 🏛️ SERVER 1: Core / API Server (Port 8000)
**Role:** Public gateway, user authentication & registration, server-side RBAC, customer 360 aggregation, and request orchestration.

#### 1. `POST /api/v1/auth/register` (or `/api/v1/auth/register-user`)
* **Purpose:** Registers a new RM, Manager, or Admin user profile into the database (`Profile` table) and returns an immediate signed JWT token.
* **Request Body:**
```json
{
  "user_id": "rm_priya_01",
  "employee_code": "EMP-8821",
  "full_name": "Priya Sharma",
  "email": "priya.sharma@matkayena.com",
  "phone": "+91-9876543210",
  "roles": ["RM"],
  "manager_id": "mgr_vikram_01",
  "org_unit_id": "branch_mumbai_01"
}
```
* **Roles Available:** `"RM"`, `"TEAM_LEAD"`, `"MANAGER"`, `"REGIONAL_MANAGER"`, `"ADMIN"`
* **Output:**
```json
{
  "user_id": "rm_priya_01",
  "full_name": "Priya Sharma",
  "email": "priya.sharma@matkayena.com",
  "roles": ["RM"],
  "manager_id": "mgr_vikram_01",
  "org_unit_id": "branch_mumbai_01",
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "message": "User profile registered and JWT access token issued successfully."
}
```

---

#### 2. `POST /api/v1/auth/login` (or `/api/v1/auth/login-user`)
* **Purpose:** Authenticates user by email, retrieves their profile from the database, and issues a signed JWT access token.
* **Request Body:**
```json
{
  "email": "priya.sharma@matkayena.com",
  "password": "Password123!",
  "roles": ["RM"]
}
```
* **Output:**
```json
{
  "user_id": "rm_priya_01",
  "full_name": "Priya Sharma",
  "email": "priya.sharma@matkayena.com",
  "roles": ["RM"],
  "manager_id": "mgr_vikram_01",
  "org_unit_id": "branch_mumbai_01",
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "message": "Login successful. Use this access_token in 'Authorize' button or 'Authorization: Bearer <token>' header."
}
```

---

#### 3. `GET /api/v1/auth/me` (or `/api/v1/auth/current-user`)
* **Purpose:** Decodes the active JWT Bearer token and returns the current user profile, assigned roles, and branch context.
* **Header:** `Authorization: Bearer <access_token>`
* **Output:**
```json
{
  "user_id": "rm_priya_01",
  "email": "priya.sharma@matkayena.com",
  "roles": ["RM"],
  "full_name": "Priya Sharma",
  "manager_id": "mgr_vikram_01",
  "org_unit_id": "branch_mumbai_01",
  "is_active": true
}
```

---

#### 4. `POST /api/v1/auth/token` (or `/api/v1/auth/generate-token`)
* **Purpose:** Issues a custom signed JWT access token for any user ID and role combination.
* **Request Body:**
```json
{
  "user_id": "rm_priya_01",
  "email": "priya.sharma@matkayena.com",
  "roles": ["RM"],
  "org_unit_id": "branch_mumbai_01"
}
```

---

#### 5. `POST /api/v1/events/submit-event`

* **Purpose:** Public entrypoint to ingest banking, payment, and CRM events.
* **Request Body (Payin Deposit Example):**
```json
{
  "event_type": "PAYIN_RECEIVED",
  "entity_type": "CUSTOMER",
  "entity_id": "cust_101",
  "payload": {
    "amount": 500000.0,
    "customer_id": "cust_101"
  },
  "idempotency_key": "payin_cust101_tx001"
}
```

---

#### 3. `GET /api/v1/customers/list-assigned`
* **Purpose:** Lists customers assigned to the calling RM (or all for Managers/Admins).
* **Query Parameters:** `limit` *(int, default=50)*

---

#### 4. `GET /api/v1/customers/360-view/{customer_id}`
* **Purpose:** Retrieves full 360° context: demographics, holdings, transactions, and active leads.
* **Path Parameters:**
  * `customer_id` *(str)*: e.g. `"cust_101"`

---

#### 5. `GET /api/v1/opportunities/list-opportunities`
* **Purpose:** Lists detected commercial opportunities with deterministic scores and explainability.
* **Query Parameters:**
  * `rm_id` *(str, optional)*: e.g. `"rm_priya_01"`
  * `customer_id` *(str, optional)*: e.g. `"cust_101"`
  * `status` *(str, optional)*: `"DETECTED"`, `"ASSIGNED"`, `"CONVERTED"`

---

#### 6. `POST /api/v1/opportunities/evaluate-customer`
* **Purpose:** Directly triggers Opportunity Agent for a specific customer.
* **Request Body:**
```json
{
  "customer_id": "cust_101"
}
```

---

#### 7. `GET /api/v1/actions/list-actions`
* **Purpose:** Lists assigned RM tasks.
* **Query Parameters:** `rm_id` *(optional)*, `customer_id` *(optional)*, `status` *(optional)*

---

#### 8. `POST /api/v1/actions/{action_id}/complete-conversion`
* **Purpose:** Marks an action completed and calculates deterministic commission.
* **Path Parameters:** `action_id` *(str)*
* **Request Body:**
```json
{
  "outcome_type": "CONVERTED",
  "converted_product_id": "prod_ins_1",
  "converted_value": 500000.0,
  "commission_eligible": true,
  "notes": "Customer converted to term life insurance policy."
}
```

---

#### 9. `GET /api/v1/performance/evaluate-rm/{rm_id}`
* **Purpose:** Evaluates RM quota pacing, conversion rate, SLA breaches, and drivers.
* **Path Parameters:** `rm_id` *(str)*: e.g. `"rm_priya_01"`
* **Query Parameters:** `period` *(str, default="2026-Q1")*

---

#### 10. `GET /api/v1/manager/alerts/list-alerts`
* **Purpose:** Synthesizes manager intelligence, team shortfalls, and escalations.
* **Query Parameters:** `period` *(str, default="2026-Q1")*

---

#### 11. `GET /api/v1/audit/records/list-records`
* **Purpose:** Lists chronological cryptographic audit records and blockchain proofs.
* **Query Parameters:** `skip` *(int, default=0)*, `limit` *(int, default=50)*

---

#### 12. `GET /api/v1/audit/verify-chain/validate-ledger`
* **Purpose:** Validates full hash-chain continuity from Genesis (`0000...`) to the latest block.

---

---

### 🧠 SERVER 2: Event + Intelligence Server (Port 8001)
**Role:** Ingests events, enforces idempotency, evaluates business rules, and hosts the **3 Autonomous Deterministic Agents**.

#### 1. `POST /api/v1/events/ingest-event`
* **Purpose:** Ingestion pipeline that processes events and invokes the Opportunity Agent.
* **Request Body:**
```json
{
  "event_type": "PAYIN_RECEIVED",
  "entity_type": "CUSTOMER",
  "entity_id": "cust_101",
  "payload": {
    "amount": 500000.0,
    "customer_id": "cust_101"
  },
  "idempotency_key": "idemp_evt_101"
}
```

---

#### 2. `POST /api/v1/intelligence/evaluate-customer-opportunity` (Agent #1: Opportunity Agent)
* **Purpose:** Evaluates customer holdings to detect cross-sell, upsell, and dormant reactivations.
* **Request Body:**
```json
{
  "customer_id": "cust_101",
  "correlation_id": "corr_opp_101"
}
```
* **Output:** Returns scored opportunities with explainability evidence (`what`, `why`, `rule_evaluated`, `signals`).

---

#### 3. `POST /api/v1/intelligence/evaluate-rm-performance` (Agent #2: Performance Agent)
* **Purpose:** Calculates target achievement, pacing, conversion rates, and SLA breach scores.
* **Request Body:**
```json
{
  "rm_id": "rm_priya_01",
  "period": "2026-Q1"
}
```
* **Output:** Performance snapshot (`HEALTHY`, `ON_TRACK`, `AT_RISK`, `CRITICAL`, or `EXCEPTIONAL`).

---

#### 4. `GET /api/v1/intelligence/manager-intelligence/list-alerts` (Agent #3: Manager Agent)
* **Purpose:** Synthesizes prioritized risk alerts and quota shortfalls with anti-spam cooldown.
* **Query Parameters:** `period` *(str, default="2026-Q1")*

---

#### 5. `GET /api/v1/intelligence/opportunities/{opportunity_id}`
* **Purpose:** Fetches full explainability details for a specific opportunity ID.
* **Path Parameters:** `opportunity_id` *(str)*

---

---

### ⚡ SERVER 3: Action + Commission Server (Port 8002)
**Role:** Manages the RM action lifecycle state machine and executes 100% deterministic commission calculations (0% LLM).

#### 1. `POST /api/v1/actions/create-action`
* **Purpose:** Creates and assigns a new actionable RM task.
* **Request Body:**
```json
{
  "customer_id": "cust_101",
  "assigned_rm_id": "rm_priya_01",
  "title": "Follow-up: Cross-sell Term Life Insurance",
  "description": "Customer deposited ₹5L. Present comprehensive insurance protection.",
  "action_type": "CALL_CUSTOMER",
  "priority": "HIGH",
  "opportunity_id": "opp_101"
}
```

---

#### 2. `GET /api/v1/actions/list-actions`
* **Purpose:** Lists tasks with lifecycle states (`PROPOSED`, `ASSIGNED`, `IN_PROGRESS`, `COMPLETED`, `SNOOZED`).
* **Query Parameters:** `rm_id` *(optional)*, `status` *(optional)*, `limit` *(default=50)*

---

#### 3. `GET /api/v1/actions/{action_id}`
* **Purpose:** Retrieves action details, recorded outcome, and full lifecycle transition history.
* **Path Parameters:** `action_id` *(str)*

---

#### 4. `POST /api/v1/actions/{action_id}/complete-conversion`
* **Purpose:** Completes action and deterministically computes RM commission.
* **Formula:** $\text{Converted Value} \times \text{Base Rate} \times \text{Segment Multiplier} \times \text{Volume Tier Multiplier}$
* **Request Body:**
```json
{
  "outcome_type": "CONVERTED",
  "converted_product_id": "prod_ins_1",
  "converted_value": 500000.0,
  "commission_eligible": true,
  "notes": "Policy issued."
}
```
* **Output:**
```json
{
  "success": true,
  "commission": {
    "is_eligible": true,
    "converted_value": 500000.0,
    "base_rate": 0.05,
    "segment_multiplier": 1.25,
    "volume_multiplier": 1.05,
    "base_commission_amount": 25000.0,
    "final_commission_amount": 32812.5
  }
}
```

---

#### 5. `POST /api/v1/actions/{action_id}/snooze`
* **Purpose:** Defers task follow-up.
* **Request Body:**
```json
{
  "snooze_until": "2026-08-28T09:00:00Z",
  "reason": "Customer traveling abroad; requested callback next week."
}
```

---

#### 6. `POST /api/v1/actions/{action_id}/reassign`
* **Purpose:** Reassigns task to another RM (Manager/Admin authorized).
* **Request Body:**
```json
{
  "new_rm_id": "rm_rohan_02",
  "reason": "Reassigned to senior advisor for Ultra-HNI portfolio."
}
```

---

---

### 🔒 SERVER 4: Audit + Blockchain Server (Port 8003)
**Role:** Canonical SHA-256 hash-chain maintainer, tamper verification, and failure-isolated blockchain proof anchoring.

#### 1. `POST /api/v1/audit/create-record`
* **Purpose:** Appends a new immutable canonical hash-chain block and queues blockchain anchor.
* **Formula:** $\text{current\_hash} = \text{SHA256}(\text{previous\_hash} \,|\, \text{payload\_hash} \,|\, \text{entity\_type} \,|\, \text{entity\_id} \,|\, \text{action})$
* **Request Body:**
```json
{
  "entity_type": "COMMISSION",
  "entity_id": "comm_101",
  "action": "COMMISSION_CALCULATED",
  "payload": {
    "converted_value": 500000.0,
    "final_commission": 32812.5,
    "rm_id": "rm_priya_01"
  },
  "actor_id": "rm_priya_01",
  "correlation_id": "corr_wf_101"
}
```

---

#### 2. `GET /api/v1/audit/list-records`
* **Purpose:** Lists chronological audit records with node hashes and blockchain anchor status.
* **Query Parameters:** `skip` *(default=0)*, `limit` *(default=50)*, `entity_type` *(optional)*

---

#### 3. `GET /api/v1/audit/verify-record/{record_id}`
* **Purpose:** Cryptographically verifies that stored payload SHA-256 and node hash have not been altered.
* **Path Parameters:** `record_id` *(str)*

---

#### 4. `GET /api/v1/audit/verify-full-chain`
* **Purpose:** Traverses from Genesis (`0000...`) to the latest block to verify unbroken chain continuity.
* **Query Parameters:** `limit` *(int, default=500)*
* **Output:**
```json
{
  "is_valid": true,
  "total_records": 5,
  "status": "VERIFIED_UNBROKEN"
}
```

---

## 🧪 4. Complete Functionality Testing Guide (Recipes & Parameters)

You can test all system capabilities using **Swagger UI**, **cURL**, or **PowerShell**.

---

### 1️⃣ Functionality 1: User Registration & Profile Creation
* **Endpoint**: `POST http://127.0.0.1:8000/api/v1/auth/register`
* **Swagger UI**: Server 1 (`:8000`) -> `Authentication` -> `POST /api/v1/auth/register`
* **Parameters / Request Body**:
```json
{
  "user_id": "rm_priya_01",
  "employee_code": "EMP-8821",
  "full_name": "Priya Sharma",
  "email": "priya.sharma@matkayena.com",
  "phone": "+91-9876543210",
  "roles": ["RM"],
  "manager_id": "mgr_vikram_01",
  "org_unit_id": "branch_mumbai_01"
}
```
* **PowerShell**:
```powershell
$body = @{
    user_id = "rm_priya_01"
    full_name = "Priya Sharma"
    email = "priya.sharma@matkayena.com"
    roles = @("RM")
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/register" -Method Post -Body $body -ContentType "application/json"
```

---

### 2️⃣ Functionality 2: User Login & Session Profile Inspection
* **Login Endpoint**: `POST http://127.0.0.1:8000/api/v1/auth/login`
* **Request Body**:
```json
{
  "email": "priya.sharma@matkayena.com",
  "password": "Password123!",
  "roles": ["RM"]
}
```
* **Verify Current User**: `GET http://127.0.0.1:8000/api/v1/auth/me`
* **Header**: `Authorization: Bearer <access_token_from_login>`
* **Output**:
```json
{
  "user_id": "rm_priya_01",
  "email": "priya.sharma@matkayena.com",
  "roles": ["RM"],
  "full_name": "Priya Sharma",
  "manager_id": "mgr_vikram_01",
  "is_active": true
}
```

---

### 3️⃣ Functionality 3: Role-Based Token Generation & RBAC Security
* **Endpoint**: `POST http://127.0.0.1:8000/api/v1/auth/generate-token`
* **Parameters / Request Body (Manager Role)**:
```json
{
  "user_id": "mgr_vikram_01",
  "email": "vikram.seth@matkayena.com",
  "roles": ["MANAGER"],
  "org_unit_id": "branch_mumbai_01"
}
```

* **Testing RBAC Isolation**:
  - Request with `RM` token attempting `GET /api/v1/manager/alerts` -> `403 Forbidden` (Only Managers/Admins allowed).
  - Request with `MANAGER` token -> `200 OK` (Permitted).

---

### 3️⃣ Functionality 3: Customer 360 & Holdings Inspection
* **Endpoint**: `GET http://127.0.0.1:8000/api/v1/customers/360-view/cust_101`
* **Header**: `X-Service-Token: ps02-internal-service-hmac-token-2026` or `Authorization: Bearer <TOKEN>`
* **Path Parameter**: `customer_id = cust_101`
* **Output**: Aggregates customer demographic profile, current product holdings (Mutual Funds, Deposits), transaction history, and active leads.

---

### 4️⃣ Functionality 4: Event Ingestion & Idempotency Deduplication
* **Endpoint**: `POST http://127.0.0.1:8000/api/v1/events/submit-event` (or direct to `:8001/api/v1/events/ingest-event`)
* **Header**: `X-Service-Token: ps02-internal-service-hmac-token-2026`
* **Request Body**:
```json
{
  "event_type": "PAYIN_RECEIVED",
  "entity_type": "CUSTOMER",
  "entity_id": "cust_101",
  "payload": {
    "amount": 500000.0,
    "customer_id": "cust_101"
  },
  "idempotency_key": "idemp_unique_tx_9999",
  "correlation_id": "corr_test_001"
}
```
* **Testing Idempotency**:
  1. Send first request -> `200 OK`, `success: true`, `decisions_made: 1`, `actions_created: 1`.
  2. Send second request with identical `idempotency_key` -> `200 OK`, `details.status: "IDEMPOTENT_SUPPRESSION"`. Deduplicates without double-processing.

---

### 5️⃣ Functionality 5: Agent #1 — Opportunity Agent Evaluation
* **Endpoint**: `POST http://127.0.0.1:8001/api/v1/intelligence/evaluate-customer-opportunity`
* **Request Body**:
```json
{
  "customer_id": "cust_101",
  "correlation_id": "corr_opp_manual_01"
}
```
* **Output**: Returns scored opportunities with explainability signals (`what`, `why`, `rule_evaluated`, `signals`).

---

### 6️⃣ Functionality 6: Action Lifecycle State Machine
* **List Tasks**: `GET http://127.0.0.1:8000/api/v1/actions/list-actions?rm_id=rm_priya_01&status=ASSIGNED`
* **Snooze Task**: `POST http://127.0.0.1:8002/api/v1/actions/{action_id}/snooze`
```json
{
  "snooze_until": "2026-08-28T09:00:00Z",
  "reason": "Client requested follow-up next Monday."
}
```
* **Reassign Task**: `POST http://127.0.0.1:8002/api/v1/actions/{action_id}/reassign`
```json
{
  "new_rm_id": "rm_rohan_02",
  "reason": "Client assigned to Senior Wealth RM."
}
```

---

### 7️⃣ Functionality 7: Pure Deterministic Commission Engine (0% LLM)
* **Endpoint**: `POST http://127.0.0.1:8002/api/v1/commission/calculate`
* **Request Body**:
```json
{
  "rm_id": "rm_priya_01",
  "action_id": "act_test_001",
  "product_category": "INSURANCE",
  "converted_value": 500000.0,
  "customer_segment": "HNI",
  "conversion_speed_hours": 12.0
}
```
* **Mathematical Formula**:
  $$\text{Commission} = 500,000 \times 0.05 \text{ (Base)} \times 1.25 \text{ (HNI)} \times 1.05 \text{ (Volume)} = \mathbf{₹32,812.50}$$

---

### 8️⃣ Functionality 8: Agent #2 — RM Performance Agent Evaluation
* **Endpoint**: `GET http://127.0.0.1:8000/api/v1/performance/evaluate-rm/rm_priya_01?period=2026-Q1`
* **Output**: Evaluates run-rate pacing, conversion rates, and SLA breach penalty scores. Diagnoses status (`HEALTHY`, `ON_TRACK`, `AT_RISK`, `CRITICAL`, or `EXCEPTIONAL`) with traceable primary drivers.

---

### 9️⃣ Functionality 9: Agent #3 — Manager Intelligence & Escalations
* **Endpoint**: `GET http://127.0.0.1:8000/api/v1/manager/alerts/list-alerts?period=2026-Q1`
* **Header**: `Authorization: Bearer <MANAGER_JWT_TOKEN>`
* **Output**: Aggregates team shortfalls, critical SLA breaches, and high-priority customer escalations with built-in 4-hour anti-spam cooldown throttling.

---

### 🔟 Functionality 🔟: Cryptographic SHA-256 Hash Chain & Blockchain Isolation
* **View Audit Trail**: `GET http://127.0.0.1:8000/api/v1/audit/records/list-records?limit=10`
* **Verify Hash Chain Integrity**: `GET http://127.0.0.1:8000/api/v1/audit/verify-chain/validate-ledger`
* **Output**:
```json
{
  "is_valid": true,
  "total_records": 12,
  "status": "VERIFIED_UNBROKEN"
}
```

---

## ⚙️ 5. Automated Test Suite

Run the full automated test suite containing 20 tests covering all 4 microservers, the 3 deterministic agents, RBAC security, and idempotency:

```powershell
python -m pytest tests/ -v
```
*(All 20 tests pass with a 100% success rate).*

