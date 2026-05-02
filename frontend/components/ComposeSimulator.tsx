"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { runCompose } from "../lib/api";
import { Category, ComposePayload, ComposeResponse, TriggerType } from "../lib/types";
import OutputPanel from "./OutputPanel";

const categories: Category[] = ["restaurant", "gym", "salon", "dentist", "pharmacy"];
const triggers: TriggerType[] = [
  "spike",
  "drop",
  "high_cart_abandon",
  "low_repeat_rate",
  "new_competitor",
  "rating_dip",
  "inventory_expiry",
  "weekend_opportunity",
];

const categoryIcons: Record<Category, string> = {
  restaurant: "🍽️",
  gym: "💪",
  salon: "✨",
  dentist: "🦷",
  pharmacy: "💊",
};

const triggerLabels: Record<TriggerType, string> = {
  spike: "Demand Spike",
  drop: "Order Drop",
  high_cart_abandon: "High Cart Abandon",
  low_repeat_rate: "Low Repeat Rate",
  new_competitor: "New Competitor",
  rating_dip: "Rating Dip",
  inventory_expiry: "Inventory Expiry",
  weekend_opportunity: "Weekend Opportunity",
};

function initialPayload(): ComposePayload {
  return {
    category: "restaurant",
    merchant: {
      merchant_id: "m_1021",
      name: "Biryani House",
      category: "restaurant",
      city: "Bengaluru",
      avg_order_value: 320,
      weekly_orders: 1400,
      conversion_rate: 0.19,
      repeat_customer_rate: 0.27,
      rating: 4.1,
      margin_pct: 0.28,
    },
    trigger: {
      type: "spike",
      observed_value: 240,
      baseline_value: 150,
      window_minutes: 180,
      timestamp_utc: "2026-05-02T14:00:00Z",
    },
    customer: {
      customer_id: "c_991",
      loyalty_tier: "gold",
      visits_last_30d: 5,
      spend_last_30d: 2100,
      last_engagement_days: 4,
    },
  };
}

function validate(payload: ComposePayload): Record<string, string> {
  const e: Record<string, string> = {};
  if (payload.merchant.avg_order_value <= 0) e.aov = "AOV must be greater than 0";
  if (payload.merchant.weekly_orders <= 0) e.weekly_orders = "Weekly orders must be greater than 0";
  if (payload.trigger.observed_value <= 0) e.observed = "Observed value must be greater than 0";
  if (payload.trigger.baseline_value <= 0) e.baseline = "Baseline must be greater than 0";
  return e;
}

function FieldHint({ text }: { text: string }) {
  return <p className="text-xs text-gray-500 mt-1">{text}</p>;
}

function FieldError({ text }: { text: string }) {
  return <p className="text-xs text-red-400 mt-1">{text}</p>;
}

export default function ComposeSimulator() {
  const [payload, setPayload] = useState<ComposePayload>(initialPayload);
  const [output, setOutput] = useState<ComposeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [hasAutoRun, setHasAutoRun] = useState(false);

  const ratio = useMemo(() => {
    if (payload.trigger.baseline_value <= 0) return "0.00";
    return (payload.trigger.observed_value / payload.trigger.baseline_value).toFixed(2);
  }, [payload.trigger.baseline_value, payload.trigger.observed_value]);

  async function runDecision(p: ComposePayload) {
    setLoading(true);
    setError(null);
    try {
      const res = await runCompose(p);
      setOutput(res);
    } catch (err) {
      console.error("API ERROR:", err);
      setOutput(null);
      setError("Unable to reach the decision engine. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  // Auto-run on mount
  useEffect(() => {
    if (!hasAutoRun) {
      setHasAutoRun(true);
      runDecision(initialPayload());
    }
  }, [hasAutoRun]);

  function onRun() {
    const errs = validate(payload);
    if (Object.keys(errs).length > 0) {
      setFieldErrors(errs);
      return;
    }
    setFieldErrors({});
    runDecision(payload);
  }

  function numericInput(
    value: number,
    onChange: (v: number) => void,
    min: number,
    max: number
  ) {
    return (
      <input
        type="number"
        className="w-full"
        value={value}
        min={min}
        max={max}
        onChange={(e) => onChange(Math.min(max, Math.max(min, Number(e.target.value))))}
      />
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Left Panel */}
        <motion.section
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="glass rounded-2xl p-6 md:p-8 border border-emerald-500/10"
        >
          <h2 className="text-xl font-bold text-white mb-1">Decision Inputs</h2>
          <p className="text-sm text-gray-400 mb-6">
            Set merchant context and trigger signal. The engine is fully rule-based — same inputs always produce the same decision.
          </p>

          <div className="space-y-5">
            {/* Category + Trigger */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-gray-300">
                  {categoryIcons[payload.category]} Category
                </label>
                <select
                  className="w-full glass rounded-lg px-4 py-3 text-sm border border-emerald-500/20 focus:border-emerald-500/50"
                  value={payload.category}
                  onChange={(e) => {
                    const category = e.target.value as Category;
                    setPayload((prev) => ({
                      ...prev,
                      category,
                      merchant: { ...prev.merchant, category },
                    }));
                  }}
                >
                  {categories.map((c) => (
                    <option key={c} value={c}>
                      {categoryIcons[c]} {c}
                    </option>
                  ))}
                </select>
                <FieldHint text="Business type of the merchant" />
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-gray-300">
                  ⚡ Trigger
                </label>
                <select
                  className="w-full glass rounded-lg px-4 py-3 text-sm border border-emerald-500/20 focus:border-emerald-500/50"
                  value={payload.trigger.type}
                  onChange={(e) =>
                    setPayload((prev) => ({
                      ...prev,
                      trigger: { ...prev.trigger, type: e.target.value as TriggerType },
                    }))
                  }
                >
                  {triggers.map((t) => (
                    <option key={t} value={t}>
                      {triggerLabels[t]}
                    </option>
                  ))}
                </select>
                <FieldHint text="Business event that activates the decision" />
              </div>
            </div>

            {/* Trigger Strength Bar */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-300">
                  Trigger Strength
                </label>
                <span className="text-sm font-bold text-emerald-400">{ratio}x</span>
              </div>
              <div className="relative h-2 glass rounded-full overflow-hidden border border-emerald-500/20">
                <motion.div
                  className="absolute inset-y-0 left-0 bg-gradient-to-r from-emerald-400 to-cyan-400"
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(parseFloat(ratio) * 15, 100)}%` }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                />
              </div>
              <FieldHint text="Observed ÷ Baseline — how strong the signal is relative to normal" />
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-300">
                  AOV (₹)
                </label>
                {numericInput(
                  payload.merchant.avg_order_value,
                  (v) => setPayload((p) => ({ ...p, merchant: { ...p.merchant, avg_order_value: v } })),
                  1, 100_000
                )}
                <FieldHint text="Average order value in rupees" />
                {fieldErrors.aov && <FieldError text={fieldErrors.aov} />}
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-300">
                  Weekly Orders
                </label>
                {numericInput(
                  payload.merchant.weekly_orders,
                  (v) => setPayload((p) => ({ ...p, merchant: { ...p.merchant, weekly_orders: v } })),
                  1, 50_000
                )}
                <FieldHint text="Total orders placed in the last 7 days" />
                {fieldErrors.weekly_orders && <FieldError text={fieldErrors.weekly_orders} />}
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-300">
                  Observed Value
                </label>
                {numericInput(
                  payload.trigger.observed_value,
                  (v) => setPayload((p) => ({ ...p, trigger: { ...p.trigger, observed_value: v } })),
                  1, 100_000
                )}
                <FieldHint text="Current metric reading (e.g. orders in last 3 hrs)" />
                {fieldErrors.observed && <FieldError text={fieldErrors.observed} />}
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-300">
                  Baseline Value
                </label>
                {numericInput(
                  payload.trigger.baseline_value,
                  (v) => setPayload((p) => ({ ...p, trigger: { ...p.trigger, baseline_value: v } })),
                  1, 100_000
                )}
                <FieldHint text="Normal expected value for the same window" />
                {fieldErrors.baseline && <FieldError text={fieldErrors.baseline} />}
              </div>
            </div>

            {/* Run Button */}
            <motion.button
              type="button"
              onClick={onRun}
              disabled={loading}
              whileHover={{ scale: 1.03, y: -1 }}
              whileTap={{ scale: 0.97 }}
              className="btn-primary w-full relative overflow-hidden group py-3 rounded-xl font-semibold text-sm"
            >
              <div className="absolute inset-0 opacity-0 group-hover:opacity-20 bg-white transition-opacity" />
              {loading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="h-4 w-4 rounded-full border-2 border-dark-bg border-t-white animate-spin" />
                  Running decision…
                </div>
              ) : (
                "Run Growth Decision"
              )}
            </motion.button>

            {error && (
              <motion.p
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-sm text-red-400 bg-red-500/10 rounded-lg px-4 py-3 border border-red-500/20"
              >
                {error}
              </motion.p>
            )}
          </div>
        </motion.section>

        {/* Right Panel */}
        <OutputPanel output={output} loading={loading} />
      </div>
    </div>
  );
}
