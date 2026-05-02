# VERAX - Deterministic Merchant Growth Decision Engine

VERAX is a production-grade, deterministic, explainable AI decision system for merchant growth.
It is fully rule-based plus scoring-based, with zero random generation and no external runtime APIs.

## Why This Is Competition-Grade

- Deterministic decision pipeline from input to output.
- Multi-stage signal fusion with triage on dominant growth signal.
- Trigger semantic intelligence for business-aware interpretation.
- 3 deterministic variants scored and selected with transparent factors.
- Explicit rationale bullets and confidence score per decision.
- Suppression and fatigue control to prevent over-messaging.
- Category-aware tone, persona routing, and contextual CTA generation.
- Full-stack product surface: FastAPI backend + Next.js premium simulator UI.

## Tech Stack

- Backend: FastAPI, Pydantic, Python 3.11
- Frontend: Next.js (App Router), TypeScript, Tailwind CSS
- State: In-memory deterministic memory store

## Engine Architecture

Input
-> Context Normalization
-> Signal Fusion
-> Trigger Intelligence
-> Decision Engine (Triage)
-> Variant Generator (3)
-> Scoring Engine
-> Best Variant Selector
-> Message Assembly
-> Rationale Generation
-> Output

## Directory Layout

- backend/app/main.py: API entrypoint and endpoints
- backend/app/engine/composer.py: compose orchestration
- backend/app/engine/normalizer.py: context normalization engine
- backend/app/engine/signal_fusion.py: intent/urgency/fit fusion engine
- backend/app/engine/trigger_intelligence.py: trigger semantic mapping
- backend/app/engine/decision_engine.py: dominant signal triage and plan
- backend/app/engine/variant_generator.py: deterministic template variants
- backend/app/engine/scoring_engine.py: deterministic scoring + ranking
- backend/app/engine/anti_pattern.py: anti-pattern checks
- backend/app/engine/persona.py: send_as routing
- backend/app/engine/suppression.py: suppression key generation
- backend/app/engine/fatigue.py: customer fatigue model
- backend/app/store/memory_store.py: in-memory state and suppression windows
- backend/tests/test_compose.py: endpoint and determinism tests
- frontend/app/page.tsx: simulator page
- frontend/components/ComposeSimulator.tsx: input controls and run action
- frontend/components/OutputPanel.tsx: message, CTA, score, rationale rendering
- examples/tick_request.json: sample request
- examples/tick_response.json: sample response

## API Contract

### GET /v1/healthz

Returns basic liveness.

### GET /v1/metadata

Returns model metadata, deterministic capability, and supported enums.

### POST /v1/context

Stores memory for merchant-level behavior tuning.

Request:
{
  "merchant_id": "m_1021",
  "memory": {"preferred_tone": "soft"}
}

### POST /v1/tick

Main composition endpoint. Deterministic output.

Request shape:
- category
- merchant
- trigger
- customer (optional)

Response shape:
- message
- cta
- send_as
- suppression_key
- rationale[]
- decision_score (0 to 100)

### POST /v1/reply

Adjusts memory-aware tone handling from response text.

## Determinism Guarantees

- No random, no temperature, no probabilistic sampling.
- Pure rule-and-score path with stable tie-break ordering.
- Same input and state snapshot always yields same output.
- Suppression behavior is deterministic by merchant+trigger+time slot.

## Message Rule Compliance

Each composed winner enforces:

- Numeric quantity in message (people count)
- Rupee value in message (Rs...)
- Urgency token in message (today or now)
- Exactly one CTA field
- Max 2 message lines
- Specific context variables injected (city, trigger meaning, plan values)

## Scoring Model

Each variant is scored on:

- decision_quality
- specificity
- category_fit
- merchant_fit
- engagement

Then penalized by anti-pattern checker:

- double urgency
- long message
- weak CTA

Winner selection is deterministic via sorted score and stable tie-break keys.

## Run Locally

### Backend

1. cd backend
2. python -m venv .venv
3. .venv\\Scripts\\activate
4. pip install -r requirements.txt
5. uvicorn app.main:app --reload --port 8000

### Frontend

1. cd frontend
2. npm install
3. set NEXT_PUBLIC_API_BASE=http://localhost:8000
4. npm run dev

## Test

From backend folder:

- pytest

## Deployment

### Render (Backend)

- Use backend/render.yaml (blueprint) or manual setup:
  - Root Directory: backend
  - Build: pip install -r requirements.txt
  - Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT

### Vercel (Frontend)

- Import frontend project folder
- Add env var:
  - NEXT_PUBLIC_API_BASE=<your-render-backend-url>
- Deploy with default Next.js settings or frontend/vercel.json

## Performance Notes

- No blocking IO in compose path.
- O(1) to O(n variants) evaluation where n=3.
- In-memory lookups and arithmetic-only scoring.
- Designed for sub-300ms decision latency on standard cloud instances.

## Submission Positioning

VERAX is engineered as a product-ready decision core:

- explainable outputs with strategic rationale
- deterministic and auditable behavior
- high-specificity growth messaging
- category-sensitive business intelligence
- rapid and robust execution path
