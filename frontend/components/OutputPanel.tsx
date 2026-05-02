"use client";

import { motion } from "framer-motion";
import { ComposeResponse } from "../lib/types";
import { LoadingSkeleton } from "./UIComponents";

interface OutputPanelProps {
  output: ComposeResponse | null;
  loading?: boolean;
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.max(0, Math.min(10, Math.round(value))) * 10;
  const color = pct >= 80 ? "from-emerald-400 to-cyan-400" : pct >= 50 ? "from-amber-400 to-yellow-300" : "from-red-400 to-orange-400";
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

function confidenceLabel(score: number): { label: string; color: string } {
  if (score >= 75) return { label: "High Confidence", color: "text-emerald-400" };
  if (score >= 50) return { label: "Moderate Confidence", color: "text-amber-400" };
  return { label: "Low Confidence", color: "text-red-400" };
}

function highlightNumbers(text: string) {
  return text.replace(/(\d+%|₹[\d,]+|\d[\d,]*\s*users?)/gi, (m) =>
    `<span class="font-bold text-emerald-300">${m}</span>`
  );
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

  const { label: confLabel, color: confColor } = confidenceLabel(output.decision_score);
  const [actionLine, impactLine] = output.message.split("\n");

  return (
    <motion.section
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.6, delay: 0.2 }}
      className="glass rounded-2xl p-6 md:p-8 border border-emerald-500/10"
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-white">Decision Output</h2>
          <p className="text-xs text-gray-500 mt-0.5">Deterministic · Explainable · Auditable</p>
        </div>
        <div className="text-right">
          <div className={`text-2xl font-extrabold ${confColor}`}>{output.decision_score}</div>
          <div className={`text-xs font-medium ${confColor}`}>{confLabel}</div>
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
        {/* ACTION */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="gradient-border rounded-xl p-5 space-y-3"
        >
          <p className="text-xs font-semibold uppercase tracking-widest text-emerald-400">Recommended Action</p>
          {actionLine && (
            <p
              className="text-base text-white leading-relaxed"
              dangerouslySetInnerHTML={{ __html: highlightNumbers(actionLine) }}
            />
          )}
          <div className="pt-1 border-t border-white/5">
            <p className="text-xs text-gray-400 mb-1 uppercase tracking-wider">Call to Action</p>
            <p className="text-sm font-medium text-white">{output.cta}</p>
          </div>
        </motion.div>

        {/* IMPACT */}
        {impactLine && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            className="glass rounded-xl p-4 border border-cyan-500/20 space-y-1"
          >
            <p className="text-xs font-semibold uppercase tracking-widest text-cyan-400">Expected Impact <span className="normal-case tracking-normal font-normal text-gray-500">(Estimated)</span></p>
            <p
              className="text-sm text-gray-200 leading-relaxed"
              dangerouslySetInnerHTML={{ __html: highlightNumbers(impactLine) }}
            />
          </motion.div>
        )}

        {/* WHY */}
        {output.rationale && output.rationale.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass rounded-xl p-4 border border-emerald-500/20 space-y-3"
          >
            <p className="text-xs font-semibold uppercase tracking-widest text-gray-400">Why This Decision</p>
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

        {/* CONFIDENCE BREAKDOWN */}
        {output.score_components && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.45 }}
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

        {/* META */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="space-y-2 px-1"
        >
          <p className="text-xs text-gray-500 leading-relaxed">
            Decision computed using trigger intensity, merchant performance, and category benchmarks.
          </p>
          <div className="flex items-center justify-between text-xs text-gray-600">
            <span>Persona: <span className="text-gray-400">{output.send_as}</span></span>
            <span className="font-mono">{output.suppression_key}</span>
          </div>
        </motion.div>
      </div>
    </motion.section>
  );
}
