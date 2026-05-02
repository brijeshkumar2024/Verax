"use client";

import { useMemo, useState } from "react";
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

export default function ComposeSimulator() {
  const [payload, setPayload] = useState<ComposePayload>(initialPayload);
  const [output, setOutput] = useState<ComposeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ratio = useMemo(() => {
    if (payload.trigger.baseline_value <= 0) return "0.00";
    return (payload.trigger.observed_value / payload.trigger.baseline_value).toFixed(2);
  }, [payload.trigger.baseline_value, payload.trigger.observed_value]);

  async function onRun() {
    setLoading(true);
    setError(null);
    try {
      const res = await runCompose(payload);
      setOutput(res);
    } catch (err) {
      console.error("API ERROR:", err);
      setOutput(null);
      setError("Connection timeout. Check backend is running and retry.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Left Panel - Compose Simulator */}
        <motion.section
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="glass rounded-2xl p-6 md:p-8 border border-emerald-500/10"
        >
          <h2 className="text-2xl font-bold text-white mb-2">Compose Simulator</h2>
          <p className="text-sm text-gray-400 mb-6">
            Set merchant context and trigger. Runtime is fully rule-based, no random generation.
          </p>

          <div className="space-y-5">
            {/* Category and Trigger Row */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-gray-300">
                  {categoryIcons[payload.category] || "📍"} Category
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
              </div>

              <div className="space-y-2">
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
                      {t}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Trigger Strength Bar */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-300">
                  📊 Trigger Strength
                </label>
                <span className="text-sm font-bold text-emerald-400">{ratio}x</span>
              </div>
              <div className="relative h-2 glass rounded-full overflow-hidden border border-emerald-500/20">
                <motion.div
                  className="absolute inset-y-0 left-0 bg-gradient-to-r from-emerald-400 to-cyan-400"
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(parseFloat(ratio) * 30, 100)}%` }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                />
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-300">
                  💰 AOV (Rs)
                </label>
                <input
                  type="number"
                  className="w-full"
                  value={payload.merchant.avg_order_value}
                  onChange={(e) =>
                    setPayload((prev) => ({
                      ...prev,
                      merchant: {
                        ...prev.merchant,
                        avg_order_value: Math.min(100_000, Math.max(0, Number(e.target.value))),
                      },
                    }))
                  }
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-300">
                  📈 Weekly Orders
                </label>
                <input
                  type="number"
                  className="w-full"
                  value={payload.merchant.weekly_orders}
                  onChange={(e) =>
                    setPayload((prev) => ({
                      ...prev,
                      merchant: {
                        ...prev.merchant,
                        weekly_orders: Math.min(50_000, Math.max(0, Number(e.target.value))),
                      },
                    }))
                  }
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-300">
                  📊 Observed
                </label>
                <input
                  type="number"
                  className="w-full"
                  value={payload.trigger.observed_value}
                  onChange={(e) =>
                    setPayload((prev) => ({
                      ...prev,
                      trigger: {
                        ...prev.trigger,
                        observed_value: Math.min(100_000, Math.max(0, Number(e.target.value))),
                      },
                    }))
                  }
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-300">
                  📍 Baseline
                </label>
                <input
                  type="number"
                  className="w-full"
                  value={payload.trigger.baseline_value}
                  onChange={(e) =>
                    setPayload((prev) => ({
                      ...prev,
                      trigger: {
                        ...prev.trigger,
                        baseline_value: Math.min(100_000, Math.max(1, Number(e.target.value))),
                      },
                    }))
                  }
                />
              </div>
            </div>

            {/* Run Button */}
            <motion.button
              type="button"
              onClick={onRun}
              disabled={loading}
              whileHover={{ scale: 1.05, y: -2 }}
              whileTap={{ scale: 0.95 }}
              className="btn-primary w-full relative overflow-hidden group"
            >
              <div className="absolute inset-0 opacity-0 group-hover:opacity-20 bg-white transition-opacity" />
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 rounded-full border-2 border-dark-bg border-t-white animate-spin" />
                  Composing...
                </div>
              ) : (
                "Run Compose Decision"
              )}
            </motion.button>

            {error && (
              <motion.p
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-sm text-red-400 bg-red-500/10 rounded-lg px-4 py-2 border border-red-500/20"
              >
                {error}
              </motion.p>
            )}
          </div>
        </motion.section>

        {/* Right Panel - Output */}
        <OutputPanel output={output} loading={loading} />
      </div>
    </div>
  );
}
