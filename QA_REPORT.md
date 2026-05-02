# VERAX QA Validation Report

Date: 2026-05-02
Scope: Backend + Frontend runtime validation, feature compliance, determinism, performance, quality.

## Execution Summary

- Backend dependency install: completed.
- Frontend dependency install: completed.
- Backend unit tests: 3 passed.
- Backend live API tests: executed against running FastAPI server.
- Frontend runtime: Next.js app served successfully; UI rendered.
- Frontend-backend integration from browser: failed due CORS preflight rejection.

## Endpoint Results

- GET /v1/healthz: PASS (200, 89.18 ms)
- GET /v1/metadata: PASS (200, 7.94 ms)
- POST /v1/context: PASS (200, 11.58 ms)
- POST /v1/reply: PASS (200, 9.04 ms)
- POST /v1/tick: PASS for valid payloads (200); PASS for invalid payload handling (422)

## Functional Cases

### Case 1: restaurant + spike
- Status: 200
- Latency: 15.46 ms
- Structure: PASS
- Message rules:
  - Number present: PASS
  - Rupee symbol ₹ present: FAIL (uses Rs)
  - Urgency present: PASS
  - Single CTA field present: PASS
  - Max 2 lines: PASS

### Case 2: gym + dip (mapped to drop)
- Status: 200
- Latency: 7.16 ms
- Structure: PASS
- Message rules: same pattern as Case 1 (₹ FAIL, others PASS)

### Case 3: salon + festival (mapped to weekend_opportunity)
- Status: 200
- Latency: 6.70 ms
- Structure: PASS
- Message rules: same pattern as Case 1 (₹ FAIL, others PASS)

### Case 4: pharmacy + refill reminder (mapped to low_repeat_rate)
- Status: 200
- Latency: 5.16 ms
- Structure: PASS
- Message rules: same pattern as Case 1 (₹ FAIL, others PASS)

## Edge Cases

- Repeated triggers suppression: PASS
  - Same suppression key reused
  - Second response rationale mentions suppression
- High fatigue tone reduction: PASS
  - CTA changes to soft style ("Run a soft ... refill reminder")
- Conflicting triggers triage: FAIL
  - API supports single trigger only; multi-trigger conflict resolution not implemented
- Invalid input graceful handling: PASS
  - Unsupported trigger returns 422 quickly

## Determinism and Performance

- Determinism (same input -> same output): FAIL
  - Second identical request in same suppression window returns different fallback output
- Performance (<300 ms): PASS
  - Functional case max observed: 15.46 ms

## Frontend Validation

- UI render: PASS
  - Compose Simulator and Output Panel load correctly
- API integration from browser: FAIL
  - Browser preflight OPTIONS to /v1/tick receives 405 due missing CORS middleware

## Quality Review

- Specificity: PARTIAL PASS
  - Contains numeric values and city/trigger context, but language patterns are repetitive across categories
- CTA strength: PASS
  - Clear and actionable yes/no form
- Rationale explainability: PASS
  - Structured bullet rationale with signal, trigger semantics, scoring winner
- Decision score meaningfulness: PARTIAL PASS
  - Score varies by scenario and penalties, but range is narrow and suppression can produce abrupt score shifts

## Key Issues Found

1. Strict rupee formatting mismatch with requirement
- Requirement asks for ₹ symbol; output uses Rs.

2. Determinism contract violation under identical repeated input
- Suppression changes output for same payload, breaking strict same-input same-output interpretation.

3. Frontend cannot call backend from browser due CORS
- OPTIONS /v1/tick returns 405; fetch fails in UI.

4. Trigger coverage mismatch for requested festival/dip/refill vocabulary
- Domain aliases are not first-class trigger enums; requires mapping assumptions.

5. Multi-trigger conflict triage not implemented
- No API model for competing triggers despite checklist expectation.

## Improvement Suggestions

1. Add CORS middleware in backend for local and deployed frontend origins.
2. Replace Rs with ₹ in message templates to satisfy strict formatting.
3. Make determinism definition explicit:
   - Either include suppression state in input contract, or
   - Return stable output for identical payload regardless of call order, and model suppression in metadata only.
4. Add trigger alias layer in normalization:
   - dip -> drop
   - festival -> weekend_opportunity
   - refill_reminder -> low_repeat_rate or inventory_expiry
5. Expand decision score calibration band to improve discrimination.
6. Add explicit multi-trigger endpoint or payload schema with arbitration policy.
7. Add QA regression tests for CORS, ₹ symbol, and same-input determinism.
