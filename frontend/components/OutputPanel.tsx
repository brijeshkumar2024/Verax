"use client";

import { motion } from "framer-motion";
import { ComposeResponse } from "../lib/types";
import { LoadingSkeleton } from "./UIComponents";

interface OutputPanelProps {
  output: ComposeResponse | null;
  loading?: boolean;
}

// Format large INR values for Indian context
function formatINR(n: number): string {
  if (isNaN(n) || !isFinite(n)) return "₹—";
  if (n >= 10_00_000) return `₹${(n / 10_00_000).toFixed(1)}Cr`;
  if (n >= 1_00_000) return `₹${(n / 1_00_000).toFixed(1)}L`;
  if (n >= 10_000) return `₹${(n / 1_000).toFixed(0)}K`;
  return `₹${n.toLocaleString("en-IN")}`;
}

function formatMessageNumbers(text: string): string {
  // Replace bare ₹NNNN with formatted version, keep % and user counts highlighted
  return text
    .replace(/₹([\d,]+)/g, (_, num) => {
      const n = parseInt(num.replace(/,/g, ""), 10);
      return `<span class="font-bold text-emerald-300">${formatINR(n)}</span>`;
    })
    .replace(/(\d[\d,]*)\s*(users?|buyers?|people)/gi, (_, count, unit) =>
      `<span class="font-bold text-emerald-300">${count} ${unit}</span>`
    )
    .replace(/(\d+)%/g, (m) => `<span class="font-bold text-emerald-300">${m}</span>`);
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.max(0, Math.min(10, Math.round(value))) * 10;
  const color =
    pct >= 80 ? "from-emerald-400 to-cyan-400"
    : pct >= 50 ? "from-amber-400 to-yellow-300"
    : "from-red-400 to-orange-400";
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-gray-400">
        <span>{label}</span>
        <span className="font-semibold text-gray-200">{value}/10</span>
      </div>
      <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
        <motion.div
          className={`h-full rounded-full bg-gradient-to-r ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

function confidenceLabel(score: number): { label: string; color: string; bg: string } {
  if (score >= 75) return { label: "High Confidence", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/30" };
  if (score >= 50) return { label: "Moderate Confidence", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/30" };
  return { label: "Low Confidence", color: "text-red-400", bg: "bg-red-500/10 border-red-500/30" };
}

// Extract trigger type from rationale for context card
function extractTriggerContext(rationale: string[]): { trigger: string; opportunity: string; strategy: string } {
  const triggerLine = rationale.find((r) => r.startsWith("🎯")) ?? "";
  const oppLine = rationale.find((r) => r.startsWith("⚡")) ?? "";
  const stratLine = rationale.find((r) => r.startsWith("💡")) ?? "";
  return {
    trigger: triggerLine.replace("🎯 Trigger: ", "").trim(),
    opportunity: oppLine.replace("⚡ Opportunity: ", "").trim(),
    strategy: stratLine.replace("💡 Strategy: ", "").trim(),
  };
}

// Map trigger type string to a plain-English business context sentence
function triggerContextSentence(triggerRaw: string): string {
  const t = triggerRaw.toLowerCase();
  if (t.includes("spike") || t.includes("demand surge")) return "A demand surge has been detected above your normal baseline. This is a high-intent window where buyers are actively searching — acting now captures revenue that would otherwise be missed.";
  if (t.includes("drop")) return "Order volume has fallen below your normal baseline. A targeted recovery push now can reverse the trend before it compounds into a longer slump.";
  if (t.includes("cart")) return "A high proportion of customers are abandoning carts without completing purchase. A timely nudge with a small incentive can recover a significant share of this lost revenue.";
  if (t.includes("repeat") || t.includes("retention")) return "Repeat customer rate is below healthy levels. Retaining an existing customer costs far less than acquiring a new one — a loyalty push now protects long-term revenue.";
  if (t.includes("competitor")) return "A new competitor has entered your area. Proactive engagement with your existing customer base now reduces the risk of churn to the new entrant.";
  if (t.includes("rating") || t.includes("trust")) return "A recent rating drop is eroding customer trust. Addressing this proactively with a recovery campaign prevents further conversion loss.";
  if (t.includes("inventory") || t.includes("expiry")) return "Inventory is approaching expiry. Converting stock into revenue now avoids waste and protects margin.";
  if (t.includes("weekend")) return "Weekend demand patterns show elevated intent. This is a predictable high-conversion window — a targeted push now maximises the opportunity.";
  return "A business signal has been detected that warrants a targeted growth action.";
}

export default function OutputPanel({ output, loading = false }: OutputPanelProps) {
  if (loading) {
    return (
      <motion.section
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="glass rounded-2xl p-6 md:p-8 border border-emerald-500/10"
      >
        <h2 className="text-xl font-bold text-white mb-6">Decision Output</h2>
        <LoadingSkeleton />
      </motion.section>
    );
  }

  if (!output) {
    return (
      <motion.section
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="glass rounded-2xl p-6 md:p-8 border border-emerald-500/10 flex flex-col items-center justify-center min-h-96"
      >
        <div className="text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto">
            <span className="text-emerald-400 text-xl">→</span>
          </div>
          <p className="text-gray-300 font-medium">Awaiting decision</p>
          <p className="text-sm text-gray-500 max-w-xs">
            Configure the merchant context on the left and run a growth decision.
          </p>
        </div>
      </motion.section>
    );
  }

  const { label: confLabel, color: confColor, bg: confBg } = confidenceLabel(output.decision_score);
  const lines = output.message.split("\n").filter(Boolean);
  const actionLine = lines[0] ?? "";
  const { trigger, opportunity, strategy } = extractTriggerContext(output.rationale ?? []);
  const triggerContext = triggerContextSentence(trigger);

  // Extract revenue from message or CTA — resilient fallback
  const revenueMatch = output.message.match(/₹(\d[\d,]*)/) ?? output.cta.match(/₹(\d[\d,]*)/);
  const revenueRaw = revenueMatch ? parseInt(revenueMatch[1].replace(/,/g, ""), 10) : null;
  // Only show impact card if revenue is meaningful (>1000 = not a promo %)
  const revenueFormatted = revenueRaw && revenueRaw > 1000 ? formatINR(revenueRaw) : null;

  return (
    <motion.section
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.6, delay: 0.2 }}
      className="glass rounded-2xl p-6 md:p-8 border border-emerald-500/10"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h2 className="text-xl font-bold text-white">Decision Output</h2>
          <p className="text-xs text-gray-500 mt-0.5">Deterministic · Explainable · Auditable</p>
          <p className="text-xs text-gray-600 mt-1">Decision computed using trigger intensity, merchant performance, and category benchmarks.</p>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-semibold ${confBg} ${confColor}`}>
          <span className="h-1.5 w-1.5 rounded-full bg-current" />
          {confLabel} · {output.decision_score}/100
        </div>
      </div>

      {output.suppressed && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 bg-amber-500/10 border border-amber-500/30 rounded-xl p-3 flex gap-3 items-start"
        >
          <span className="text-amber-400 text-sm mt-0.5">⚠</span>
          <div>
            <p className="text-amber-400 text-sm font-semibold">Suppression Active</p>
            <p className="text-xs text-gray-400 mt-0.5">This message was already sent in the current window. Review before re-sending.</p>
          </div>
        </motion.div>
      )}

      <div className="space-y-4">

        {/* 1. WHY THIS TRIGGER MATTERS */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass rounded-xl p-4 border border-cyan-500/20 space-y-2"
        >
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-widest text-cyan-400">Why This Trigger Matters</p>
            {trigger && (
              <span className="text-xs text-gray-500 font-mono bg-white/5 px-2 py-0.5 rounded">
                {trigger.split(" ")[0]}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-300 leading-relaxed">{triggerContext}</p>
          {opportunity && (
            <p className="text-xs text-gray-500">Signal: <span className="text-gray-400">{opportunity}</span></p>
          )}
        </motion.div>

        {/* 2. RECOMMENDED ACTION */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.28 }}
          className="gradient-border rounded-xl p-5 space-y-3"
        >
          <p className="text-xs font-semibold uppercase tracking-widest text-emerald-400">Recommended Action</p>
          <p
            className="text-base text-white leading-relaxed"
            dangerouslySetInnerHTML={{ __html: formatMessageNumbers(actionLine) }}
          />
          <div className="pt-2 border-t border-white/5 flex items-start gap-3">
            <div className="flex-1">
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Next Step</p>
              <p className="text-sm font-medium text-white">{output.cta}</p>
            </div>
            {strategy && (
              <div className="text-right flex-shrink-0">
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Strategy</p>
                <p className="text-xs text-emerald-400 font-mono">{strategy.split("→")[0].trim()}</p>
              </div>
            )}
          </div>
        </motion.div>

        {/* 3. EXPECTED IMPACT */}
        {revenueFormatted && (
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.36 }}
            className="glass rounded-xl p-4 border border-emerald-500/20"
          >
            <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-3">
              Expected Impact{" "}
              <span className="normal-case tracking-normal font-normal text-gray-600">(Estimated)</span>
            </p>
            <div className="flex items-center gap-6">
              <div>
                <div className="text-2xl font-bold text-emerald-300">{revenueFormatted}</div>
                <div className="text-xs text-gray-500 mt-0.5">Estimated revenue opportunity</div>
              </div>
              <div className="h-10 w-px bg-white/10" />
              <div className="text-xs text-gray-400 leading-relaxed max-w-xs">
                Based on reachable buyers in your area, your average order value, and the applied offer discount.
                Actual results will vary.
              </div>
            </div>
          </motion.div>
        )}

        {/* 4. HOW TO EXECUTE */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.42 }}
          className="glass rounded-xl p-4 border border-emerald-500/20 space-y-2"
        >
          <p className="text-xs font-semibold uppercase tracking-widest text-gray-400">How to Execute</p>
          <ol className="space-y-1.5 text-sm text-gray-300">
            <li className="flex items-start gap-2.5">
              <span className="flex-shrink-0 w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-400 text-xs flex items-center justify-center font-bold mt-0.5">1</span>
              <span>Review the recommended message and confirm it fits your current context.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="flex-shrink-0 w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-400 text-xs flex items-center justify-center font-bold mt-0.5">2</span>
              <span>Send via your preferred channel — push notification, WhatsApp, or in-app message.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="flex-shrink-0 w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-400 text-xs flex items-center justify-center font-bold mt-0.5">3</span>
              <span>Monitor order volume over the next 3 hours. VERAX suppresses repeat messages automatically.</span>
            </li>
          </ol>
        </motion.div>

        {/* 5. WHY THIS DECISION (rationale) */}
        {output.rationale && output.rationale.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.48 }}
            className="glass rounded-xl p-4 border border-emerald-500/20 space-y-3"
          >
            <p className="text-xs font-semibold uppercase tracking-widest text-gray-400">Decision Reasoning</p>
            <div className="space-y-2">
              {output.rationale.map((r, i) => (
                <div key={i} className="flex items-start gap-2.5 text-sm text-gray-300">
                  <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-emerald-500 flex-shrink-0" />
                  <span>{r}</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* 6. CONFIDENCE BREAKDOWN */}
        {output.score_components && (
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.52 }}
            className="glass rounded-xl p-4 border border-emerald-500/20 space-y-3"
          >
            <p className="text-xs font-semibold uppercase tracking-widest text-gray-400">Confidence Breakdown</p>
            <div className="space-y-2.5">
              <ScoreBar label="Decision Quality" value={output.score_components.decision_quality} />
              <ScoreBar label="Specificity" value={output.score_components.specificity} />
              <ScoreBar label="Category Fit" value={output.score_components.category_fit} />
              <ScoreBar label="Merchant Fit" value={output.score_components.merchant_fit} />
              <ScoreBar label="Engagement" value={output.score_components.engagement} />
            </div>
          </motion.div>
        )}

        {/* Footer credibility */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.56 }}
          className="space-y-1.5 px-1"
        >
          <p className="text-xs text-gray-500 leading-relaxed">
            Decision computed using trigger intensity, merchant performance, and category benchmarks. No randomness — identical inputs always produce identical outputs.
          </p>
          <div className="flex items-center justify-between text-xs text-gray-600">
            <span>Persona: <span className="text-gray-400">{output.send_as}</span></span>
            <span className="font-mono">{output.suppression_key}</span>
          </div>
          <p className="text-xs text-gray-600 italic">
            Try adjusting trigger strength or baseline to simulate alternative outcomes.
          </p>
        </motion.div>

      </div>
    </motion.section>
  );
}
