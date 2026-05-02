# ⚖️ VERAX — Deterministic Merchant Decision Engine

> A production-grade, deterministic system that converts structured business context into **precise, explainable actions** — without randomness.

**Live API:** https://verax-backend-v5ea.onrender.com
**Live UI:** https://verax-frontend.vercel.app

---

## What is VERAX?

VERAX is a **decision engine, not a chatbot**. It takes structured merchant context and produces the next best growth action using:

- Category context and tone intelligence
- Merchant performance signals (AOV, orders, rating, margin)
- Real-time business triggers (demand spike, rating drop, competitor entry, etc.)
- Optional customer signals (loyalty tier, visit history, engagement recency)

Every output is **deterministic, grounded, and fully explainable**.

---

## Core Principle

> **Same input → Same output. Always.**

- No randomness
- No hallucination
- No temperature or sampling
- Pure rule + scoring pipeline

---

## API Response Shape

```json
{
  "message": "193 people in Bengaluru are actively searching for dinner deals right now.\nWant me to send them a ₹12 offer now?",
  "cta": "Want me to send them a ₹12 offer now?",
  "send_as": "vera",
  "suppression_key": "m_1021:spike:social_proof:2026050214",
  "suppressed": false,
  "rationale": "Trigger: spike | Signal: high-intent demand surge | Opportunity: 193 buyers in Bengaluru | Offer: ₹45,000 (193 buyers × AOV × conv × 88%) | rating 4.1 | Strategy: social_proof → push_now | Winner 80/100 vs 76, 72 | strong alignment across trigger, merchant, and demand",
  "decision_score": 80,
  "score_components": {
    "decision_quality": 8,
    "specificity": 10,
    "category_fit": 8,
    "merchant_fit": 7,
    "engagement": 8
  },
  "rule_trace": {
    "trigger_type": "spike",
    "dominant_signal": "demand",
    "priority": "capture-demand-now",
    "strategy": "social_proof",
    "deviation_pct": 126.7,
    "intent_score": 72,
    "urgency_score": 81
  }
}
```

---

## Engine Architecture

```
Input
  → Context Normalization      (cap, clamp, default missing fields)
  → Signal Fusion              (intent + urgency + merchant fit)
  → Trigger Intelligence       (semantic label + priority weight)
  → Decision Engine            (dominant signal → priority plan)
  → Variant Generator (×3)     (category tone + customer context)
  → Scoring Engine             (5-dimension weighted score)
  → Anti-Pattern Check         (penalty for weak CTA, missing ₹, etc.)
  → Best Variant Selector      (deterministic sort + stable tie-break)
  → Rationale Builder          (trigger + merchant + strategy + scores)
  → Output
```

---

## Key Features

### 1. Deterministic Pipeline
- Stable sort tie-break: `(-score, -quality, -specificity, message_lex)`
- No probabilistic paths anywhere
- Byte-identical output for identical inputs — verified by live audit

### 2. Full Explainability
Every decision includes trigger reasoning, merchant context, strategy selection, variant scores (winner vs rejected), and a structured rule trace. A judge can audit exactly how the system reached its conclusion.

### 3. Robust Input Handling
- `{}` empty input → valid decision using all defaults
- Missing merchant fields → sensible defaults applied
- Unknown triggers → fallback to `spike` with annotated rule trace
- Extra/unexpected fields → silently ignored (`extra: ignore`)
- Zero crashes, zero 422 failures on any input shape

### 4. Category Intelligence

| Category | Tone Voice | Message Style | CTA Verb |
|---|---|---|---|
| Restaurant | sharp-growth | dinner deals, food demand | send offer |
| Gym | coach-driven | fitness sessions, book a session | launch plan |
| Salon | premium-friendly | beauty slots, style-seekers | promote deal |
| Dentist | clinical-trust | checkup appointments, patients | offer checkup |
| Pharmacy | care-urgent | medicine refills, care visits | send refill |

Raw category labels never appear in output — always contextual nouns.

### 5. Suppression and Fatigue Control
Suppression key format: `merchant_id:trigger:strategy:timeslot`

- Prevents duplicate messages within the same window
- Strategy rotates after repeated sends (urgency → discount → social_proof)
- Fatigue penalty reduces intent/urgency scores after high interaction volume

### 6. Stateful Reply Intelligence
`POST /v1/reply` interprets merchant responses:

| Reply | Interpreted As | Next Tick Effect |
|---|---|---|
| "yes", "ok", "approved" | accepted | Reinforce with follow-up offer |
| "no", "stop", "reject" | rejected | Softer tone, longer cooldown |
| "later", "maybe" | deferred | Low-pressure info strategy |
| (no match) | ignored | Rotate to social_proof |

---

## API Endpoints

### `GET /v1/healthz`
Liveness check. Returns status, version, uptime, deterministic flag.

### `GET /v1/metadata`
Full system metadata: supported triggers, categories, tone engine config, determinism guarantee, suppression model, fatigue model.

### `GET /version`
Deployment version probe. Confirms latest code is running.

### `POST /v1/context`
Stores merchant memory. Accepts both formats:

```json
// Challenge format
{ "scope": "merchant", "context_id": "m_001", "version": 1, "payload": { "preferred_tone": "soft" } }

// Legacy format
{ "merchant_id": "m_001", "memory": { "preferred_tone": "soft" } }
```

### `POST /v1/tick`
Main decision endpoint. All fields optional with defaults.

Minimal input:
```json
{ "category": "restaurant", "merchant": { "merchant_id": "m_001" }, "trigger": { "type": "spike" } }
```

Full input:
```json
{
  "category": "restaurant",
  "merchant": {
    "merchant_id": "m_1021",
    "name": "Biryani House",
    "city": "Bengaluru",
    "avg_order_value": 380,
    "weekly_orders": 1400,
    "conversion_rate": 0.19,
    "repeat_customer_rate": 0.27,
    "rating": 4.1,
    "margin_pct": 0.28
  },
  "trigger": {
    "type": "spike",
    "observed_value": 340,
    "baseline_value": 150,
    "window_minutes": 180,
    "timestamp_utc": "2026-05-02T14:00:00Z"
  },
  "customer": {
    "customer_id": "c_991",
    "loyalty_tier": "gold",
    "visits_last_30d": 5,
    "spend_last_30d": 2100,
    "last_engagement_days": 4
  }
}
```

### `POST /v1/reply`
Records merchant response to update tone and strategy memory.

---

## Scoring Model

Each of 3 generated variants is scored across 5 dimensions:

| Dimension | Weight | What it measures |
|---|---|---|
| Decision Quality | 32% | Signal fusion alignment (intent × urgency) |
| Specificity | 24% | Numbers, ₹ values, urgency markers |
| Category Fit | 16% | Domain keyword relevance |
| Merchant Fit | 16% | Merchant profile alignment |
| Engagement | 12% | CTA strength and fatigue state |

Anti-pattern penalties applied for: missing ₹, missing numbers, weak CTA, too many lines.

Winner selected by: `(-total_score, -decision_quality, -specificity, message_lex)` — fully deterministic.

---

## Trigger Priority Order

```
spike > drop > new_competitor > rating_dip > high_cart_abandon > low_repeat_rate > inventory_expiry > weekend_opportunity
```

Supported aliases: `dip`, `surge`, `festival`, `refill_reminder`, `churn_risk`, `checkout_drop`, and more.

---

## Revenue Formula

```
estimated_revenue = estimated_customers × AOV × conversion_rate × (1 − promo_pct)
```

Fully derived from merchant inputs. No hardcoded values.

---

## Run Locally

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
set NEXT_PUBLIC_API_BASE=http://localhost:8000
npm run dev
```

### Tests
```bash
cd backend
pytest
```

---

## Deployment

### Backend — Render
- Root Directory: `backend`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Env: `PYTHON_VERSION=3.11.11`

### Frontend — Vercel
- Root Directory: `frontend`
- Env: `NEXT_PUBLIC_API_BASE=<render-backend-url>`

---

## Tech Stack

- Backend: FastAPI, Pydantic v2, Python 3.11
- Frontend: Next.js 15 (App Router), TypeScript, Tailwind CSS, Framer Motion
- State: In-memory deterministic store with thread-safe locking
- Deployment: Render (backend) + Vercel (frontend)

---

## Directory Layout

```
backend/app/
  main.py                   API entrypoint and all endpoints
  schemas.py                Pydantic request/response models
  config.py                 DETERMINISTIC_MODE flag
  engine/
    composer.py             Orchestration pipeline
    normalizer.py           Input normalization and capping
    signal_fusion.py        Intent + urgency + fit fusion
    trigger_intelligence.py Trigger semantic mapping
    trigger_normalizer.py   Alias resolution and priority ranking
    decision_engine.py      Dominant signal triage and plan
    variant_generator.py    3 deterministic message variants
    scoring_engine.py       5-dimension weighted scoring
    anti_pattern.py         Penalty checks
    rationale.py            Explainability builder
    tone.py                 Category tone specs
    persona.py              send_as routing
    suppression.py          Suppression key generation
    fatigue.py              Interaction fatigue model
    strategy_engine.py      Strategy selection and rotation
  store/
    memory_store.py         Thread-safe in-memory state

frontend/
  app/page.tsx              Root page
  components/
    ComposeSimulator.tsx    Input panel with presets and validation
    OutputPanel.tsx         Decision output rendering
    Header.tsx              Logo and title
    UIComponents.tsx        Shared UI primitives
  lib/
    api.ts                  Fetch wrapper with timeout
    types.ts                TypeScript types matching API contract
```

---

> **VERAX is not an AI chatbot — it is a deterministic decision system built for real-world execution.**
