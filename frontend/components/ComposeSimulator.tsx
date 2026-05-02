"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import { runCompose } from "../lib/api";
import { Category, ComposePayload, ComposeResponse, TriggerType } from "../lib/types";
import OutputPanel from "./OutputPanel";
import { OutputErrorBoundary } from "./OutputErrorBoundary";

const categories: Category[] = ["restaurant", "gym", "salon", "dentist", "pharmacy"];
const triggers: TriggerType[] = [
  "spike", "drop", "high_cart_abandon", "low_repeat_rate",
  "new_competitor", "rating_dip", "inventory_expiry", "weekend_opportunity",
];

const categoryIcons: Record<Category, string> = {
  restaurant: "🍽️", gym: "💪", salon: "✨", dentist: "🦷", pharmacy: "💊",
};

const triggerLabels: Record<TriggerType, string> = {
  spike: "Demand Spike", drop: "Order Drop", high_cart_abandon: "High Cart Abandon",
  low_repeat_rate: "Low Repeat Rate", new_competitor: "New Competitor",
  rating_dip: "Rating Dip", inventory_expiry: "Inventory Expiry",
  weekend_opportunity: "Weekend Opportunity",
};

// Realistic presets to cycle through with "Try another scenario"
const PRESETS: ComposePayload[] = [
  {
    category: "restaurant",
    merchant: { merchant_id: "m_1021", name: "Biryani House", category: "restaurant", city: "Bengaluru", avg_order_value: 380, weekly_orders: 1400, conversion_rate: 0.19, repeat_customer_rate: 0.27, rating: 4.1, margin_pct: 0.28 },
    trigger: { type: "spike", observed_value: 340, baseline_value: 150, window_minutes: 180, timestamp_utc: "2026-05-02T14:00:00Z" },
    customer: { customer_id: "c_991", loyalty_tier: "gold", visits_last_30d: 5, spend_last_30d: 2100, last_engagement_days: 4 },
  },
  {
    category: "gym",
    merchant: { merchant_id: "m_2045", name: "FitZone", category: "gym", city: "Mumbai", avg_order_value: 1200, weekly_orders: 180, conversion_rate: 0.14, repeat_customer_rate: 0.55, rating: 4.3, margin_pct: 0.40 },
    trigger: { type: "low_repeat_rate", observed_value: 60, baseline_value: 100, window_minutes: 10080, timestamp_utc: "2026-05-02T10:00:00Z" },
    customer: { customer_id: "c_201", loyalty_tier: "silver", visits_last_30d: 2, spend_last_30d: 1200, last_engagement_days: 12 },
  },
  {
    category: "pharmacy",
    merchant: { merchant_id: "m_3310", name: "MedPlus", category: "pharmacy", city: "Hyderabad", avg_order_value: 450, weekly_orders: 620, conversion_rate: 0.22, repeat_customer_rate: 0.61, rating: 4.5, margin_pct: 0.18 },
    trigger: { type: "inventory_expiry", observed_value: 340, baseline_value: 200, window_minutes: 4320, timestamp_utc: "2026-05-02T08:00:00Z" },
    customer: { customer_id: "c_512", loyalty_tier: "platinum", visits_last_30d: 8, spend_last_30d: 3600, last_engagement_days: 2 },
  },
  {
    category: "salon",
    merchant: { merchant_id: "m_4102", name: "Glam Studio", category: "salon", city: "Pune", avg_order_value: 850, weekly_orders: 95, conversion_rate: 0.17, repeat_customer_rate: 0.38, rating: 4.0, margin_pct: 0.35 },
    trigger: { type: "new_competitor", observed_value: 70, baseline_value: 95, window_minutes: 10080, timestamp_utc: "2026-05-02T12:00:00Z" },
    customer: { customer_id: "c_731", loyalty_tier: "new", visits_last_30d: 1, spend_last_30d: 850, last_engagement_days: 20 },
  },
];

type FieldKey = "aov" | "weekly_orders" | "observed" | "baseline";
type TouchedFields = Record<FieldKey, boolean>;

function validateFields(p: ComposePayload): Record<FieldKey, string> {
  const e: Record<FieldKey, string> = { aov: "", weekly_orders: "", observed: "", baseline: "" };
  if (!p.merchant.avg_order_value || p.merchant.avg_order_value <= 0) e.aov = "Must be greater than 0";
  if (!p.merchant.weekly_orders || p.merchant.weekly_orders <= 0) e.weekly_orders = "Must be greater than 0";
  if (!p.trigger.observed_value || p.trigger.observed_value <= 0) e.observed = "Must be greater than 0";
  if (!p.trigger.baseline_value || p.trigger.baseline_value <= 0) e.baseline = "Must be greater than 0";
  return e;
}

function FieldHint({ text }: { text: string }) {
  return <p className="text-xs text-gray-500 mt-1 leading-snug">{text}</p>;
}

export default function ComposeSimulator() {
  const [presetIndex, setPresetIndex] = useState(0);
  const [payload, setPayload] = useState<ComposePayload>(PRESETS[0]);
  const [output, setOutput] = useState<ComposeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<FieldKey, string>>({ aov: "", weekly_orders: "", observed: "", baseline: "" });
  const [touched, setTouched] = useState<TouchedFields>({ aov: false, weekly_orders: false, observed: false, baseline: false });
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);
  const hasAutoRun = useRef(false);

  const ratio = useMemo(() => {
    const b = payload.trigger.baseline_value;
    const o = payload.trigger.observed_value;
    if (!b || b <= 0) return 1;
    const r = o / b;
    return isNaN(r) || !isFinite(r) ? 1 : Math.min(Math.max(r, 0.1), 10);
  }, [payload.trigger.baseline_value, payload.trigger.observed_value]);

  const observedEqualsBaseline = payload.trigger.observed_value === payload.trigger.baseline_value;

  const allErrors = validateFields(payload);
  const hasErrors = Object.values(allErrors).some(Boolean);

  const runDecision = useCallback(async (p: ComposePayload) => {
    setLoading(true);
    setApiError(null);
    setLatencyMs(null);
    const t0 = performance.now();
    const [res] = await Promise.allSettled([
      runCompose(p),
      new Promise((r) => setTimeout(r, 600)),
    ]);
    const elapsed = Math.round(performance.now() - t0);
    if (res.status === "fulfilled") {
      setOutput(res.value as ComposeResponse);
      setLatencyMs(elapsed);
    } else {
      console.error("API ERROR:", (res as PromiseRejectedResult).reason);
      setOutput(null);
      setApiError("Unable to reach the decision engine. Please check your connection and try again.");
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (!hasAutoRun.current) {
      hasAutoRun.current = true;
      runDecision(PRESETS[0]);
    }
  }, [runDecision]);

  function onRun() {
    // Touch all fields to show errors
    setTouched({ aov: true, weekly_orders: true, observed: true, baseline: true });
    setFieldErrors(allErrors);
    if (hasErrors) return;
    runDecision(payload);
  }

  function onBlur(field: FieldKey) {
    setTouched((t) => ({ ...t, [field]: true }));
    setFieldErrors(validateFields(payload));
  }

  function onTryAnother() {
    const next = (presetIndex + 1) % PRESETS.length;
    setPresetIndex(next);
    const p = PRESETS[next];
    setPayload(p);
    setTouched({ aov: false, weekly_orders: false, observed: false, baseline: false });
    setFieldErrors({ aov: "", weekly_orders: "", observed: "", baseline: "" });
    runDecision(p);
  }

  function onCopyDecision() {
    if (!output) return;
    const text = [
      `VERAX Decision Output`,
      `─────────────────────`,
      `Message: ${output.message}`,
      `CTA: ${output.cta}`,
      `Score: ${output.decision_score}/100`,
      `Reasoning: ${output.rationale}`,
      ``,
      `Decision computed using trigger intensity, merchant performance, and category benchmarks.`,
    ].join("\n");
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  function numericField(
    fieldKey: FieldKey,
    value: number,
    onChange: (v: number) => void,
    min: number,
    max: number,
    hint: string,
    label: string
  ) {
    const err = touched[fieldKey] ? fieldErrors[fieldKey] : "";
    const isValid = touched[fieldKey] && !fieldErrors[fieldKey];
    return (
      <div className="space-y-1">
        <label className="text-xs font-semibold uppercase tracking-wider text-gray-300 flex items-center gap-1.5">
          {label}
          {isValid && <span className="text-emerald-400 text-xs">✓</span>}
        </label>
        <input
          type="number"
          inputMode="numeric"
          pattern="[0-9]*"
          className={`w-full transition-colors ${err ? "border-red-500/60 focus:border-red-500" : isValid ? "border-emerald-500/40 focus:border-emerald-500" : ""}`}
          value={value}
          min={min}
          max={max}
          onChange={(e) => {
            const raw = e.target.value;
            const parsed = parseFloat(raw);
            if (raw === "" || isNaN(parsed)) return;
            onChange(Math.min(max, Math.max(min, parsed)));
          }}
          onBlur={() => onBlur(fieldKey)}
        />
        {err ? (
          <p className="text-xs text-red-400 mt-1">{err}</p>
        ) : (
          <FieldHint text={hint} />
        )}
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 overflow-x-hidden">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">

        {/* ── Left Panel ── */}
        <motion.section
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="glass rounded-2xl p-5 md:p-7 border border-emerald-500/10"
        >
          <div className="flex items-start justify-between mb-1">
            <h2 className="text-xl font-bold text-white">Decision Inputs</h2>
            <button
              onClick={onTryAnother}
              disabled={loading}
              className="text-xs text-emerald-400 border border-emerald-500/30 rounded-lg px-3 py-1.5 hover:bg-emerald-500/10 transition-colors disabled:opacity-40 min-h-[36px]"
            >
              Try another scenario
            </button>
          </div>
          <p className="text-sm text-gray-400 mb-5">
            Rule-based engine — same inputs always produce the same decision.
          </p>

          <div className="space-y-5">
            {/* Context group */}
            <div>
              <p className="text-xs text-gray-600 uppercase tracking-widest mb-3 font-medium">Context</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-gray-300">
                    {categoryIcons[payload.category]} Category
                  </label>
                  <select
                    className="w-full glass rounded-lg px-4 py-3 text-sm border border-emerald-500/20 focus:border-emerald-500/50 min-h-[44px]"
                    value={payload.category}
                    onChange={(e) => {
                      const category = e.target.value as Category;
                      setPayload((prev) => ({ ...prev, category, merchant: { ...prev.merchant, category } }));
                    }}
                  >
                    {categories.map((c) => (
                      <option key={c} value={c}>{categoryIcons[c]} {c}</option>
                    ))}
                  </select>
                  <FieldHint text="Business type of the merchant" />
                </div>

                <div className="space-y-1">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-gray-300">
                    ⚡ Trigger
                  </label>
                  <select
                    className="w-full glass rounded-lg px-4 py-3 text-sm border border-emerald-500/20 focus:border-emerald-500/50 min-h-[44px]"
                    value={payload.trigger.type}
                    onChange={(e) => setPayload((prev) => ({ ...prev, trigger: { ...prev.trigger, type: e.target.value as TriggerType } }))}
                  >
                    {triggers.map((t) => (
                      <option key={t} value={t}>{triggerLabels[t]}</option>
                    ))}
                  </select>
                  <FieldHint text="Business event that activates the decision" />
                </div>
              </div>

              {/* Trigger Strength */}
              <div className="space-y-2 mt-3">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold uppercase tracking-wider text-gray-300">Trigger Strength</label>
                  <span className="text-sm font-bold text-emerald-400">{ratio.toFixed(2)}x</span>
                </div>
                <div className="relative h-2 glass rounded-full overflow-hidden border border-emerald-500/20">
                  <motion.div
                    className="absolute inset-y-0 left-0 bg-gradient-to-r from-emerald-400 to-cyan-400"
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min((Math.log(ratio + 1) / Math.log(11)) * 100, 100)}%` }}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                  />
                </div>
                <FieldHint text="Observed ÷ Baseline — how strong the signal is relative to normal" />
              </div>
            </div>

            <div className="h-px bg-white/5" />

            {/* Performance group */}
            <div>
              <p className="text-xs text-gray-600 uppercase tracking-widest mb-3 font-medium">Performance</p>
              <div className="grid grid-cols-2 gap-3">
                {numericField("aov", payload.merchant.avg_order_value,
                  (v) => setPayload((p) => ({ ...p, merchant: { ...p.merchant, avg_order_value: v } })),
                  1, 100_000, "Average order value in rupees", "AOV (₹)")}

                {numericField("weekly_orders", payload.merchant.weekly_orders,
                  (v) => setPayload((p) => ({ ...p, merchant: { ...p.merchant, weekly_orders: v } })),
                  1, 50_000, "Total orders placed in the last 7 days", "Weekly Orders")}

                {numericField("observed", payload.trigger.observed_value,
                  (v) => setPayload((p) => ({ ...p, trigger: { ...p.trigger, observed_value: v } })),
                  1, 100_000, "Current metric reading (e.g. orders in last 3 hrs)", "Observed Value")}

                {numericField("baseline", payload.trigger.baseline_value,
                  (v) => setPayload((p) => ({ ...p, trigger: { ...p.trigger, baseline_value: v } })),
                  1, 100_000, "Normal expected value for the same window", "Baseline Value")}
              </div>

              {observedEqualsBaseline && (
                <motion.p
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-2 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2"
                >
                  ⚠ No signal detected — observed equals baseline. Trigger may not fire.
                </motion.p>
              )}
            </div>

            {/* Run Button */}
            <motion.button
              type="button"
              onClick={onRun}
              disabled={loading}
              whileHover={{ scale: loading ? 1 : 1.02, y: loading ? 0 : -1 }}
              whileTap={{ scale: 0.97 }}
              className="btn-primary w-full relative overflow-hidden group py-3 rounded-xl font-semibold text-sm min-h-[48px] disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <div className="absolute inset-0 opacity-0 group-hover:opacity-20 bg-white transition-opacity" />
              {loading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="h-4 w-4 rounded-full border-2 border-dark-bg border-t-white animate-spin" />
                  Computing decision…
                </div>
              ) : (
                "Run Growth Decision"
              )}
            </motion.button>

            {apiError && (
              <motion.p
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-sm text-red-400 bg-red-500/10 rounded-lg px-4 py-3 border border-red-500/20"
              >
                {apiError}
              </motion.p>
            )}
          </div>
        </motion.section>

        {/* ── Right Panel ── */}
        <OutputErrorBoundary>
          <OutputPanel
            output={output}
            loading={loading}
            latencyMs={latencyMs}
            onCopy={onCopyDecision}
            copied={copied}
            triggerStrength={ratio}
            category={payload.category}
            observedValue={payload.trigger.observed_value}
            baselineValue={payload.trigger.baseline_value}
          />
        </OutputErrorBoundary>
      </div>
    </div>
  );
}
