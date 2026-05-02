"use client";

import { motion } from "framer-motion";
import { ComposeResponse } from "../lib/types";
import { CircularProgress, RationaleChip, LoadingSkeleton } from "./UIComponents";

interface OutputPanelProps {
  output: ComposeResponse | null;
  loading?: boolean;
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
        <h2 className="text-2xl font-bold text-white mb-6">Decision Output</h2>
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
        <div className="text-center space-y-4">
          <div className="text-6xl opacity-50">✨</div>
          <h3 className="text-lg font-semibold text-gray-300">No decision yet</h3>
          <p className="text-sm text-gray-400">
            Configure merchant context and trigger a compose on the left panel to see AI decision output here.
          </p>
        </div>
      </motion.section>
    );
  }

  const highlightNumber = (text: string) => {
    return text.replace(/(\d+%|₹\d+[,\d]*|₹[\d.]+[KMB]?)/g, (match) => {
      return `<span class="font-bold text-emerald-300">${match}</span>`;
    });
  };

  const scoreColorClass =
    output.decision_score > 75 ? "text-emerald-400" : output.decision_score >= 50 ? "text-amber-400" : "text-red-400";

  const renderScoreBar = (label: string, value: number) => {
    const v = Math.max(0, Math.min(10, Math.round(value)));
    const filled = "█".repeat(v);
    const empty = "░".repeat(10 - v);
    return (
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-300">{label}:</span>
        <span className="font-mono text-gray-100">{filled}{empty} {v}</span>
      </div>
    );
  };

  return (
    <motion.section
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.6, delay: 0.2 }}
      className="glass rounded-2xl p-6 md:p-8 border border-emerald-500/10"
    >
      <h2 className="text-2xl font-bold text-white mb-2">Decision Output</h2>
      <p className="text-sm text-gray-400 mb-6">Deterministic variant scoring and selection</p>

      <div className="space-y-6">
        {/* Suppression Status Badge */}
        {output.suppressed && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-warning-yellow/10 border border-warning-yellow/30 rounded-lg p-3 flex items-start gap-3"
          >
            <div className="text-warning-yellow text-xl flex-shrink-0">⚠️</div>
            <div>
              <p className="font-semibold text-warning-yellow text-sm">Suppression Active</p>
              <p className="text-xs text-gray-300 mt-1">
                Message is valid but flagged as duplicate in suppression window. Review window before sending.
              </p>
            </div>
          </motion.div>
        )}

        {/* Message Hero Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.4 }}
          className="gradient-border rounded-2xl p-6 space-y-4"
        >
          <div className="text-sm font-semibold uppercase tracking-wider text-emerald-400">
            📨 Recommended Message
          </div>
          <div className="text-lg leading-relaxed text-white">
            {output.message.split("\n").map((line, i) => (
              <div
                key={i}
                dangerouslySetInnerHTML={{
                  __html: highlightNumber(line),
                }}
              />
            ))}
          </div>
        </motion.div>

        {/* CTA + Send As + Score Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.4 }}
            className="glass rounded-lg p-4 border border-emerald-500/20"
          >
            <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">
              ❓ Call to Action
            </div>
            <p className="text-white font-medium">{output.cta}</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.45, duration: 0.4 }}
            className="glass rounded-lg p-4 border border-emerald-500/20"
          >
            <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">
              👤 Persona
            </div>
            <p className="text-white font-medium">{output.send_as}</p>
          </motion.div>
        </div>

        {/* Score Indicator */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5, duration: 0.4 }}
          className="glass rounded-lg p-5 border border-emerald-500/20 space-y-4"
        >
          <div className="flex items-end justify-between">
            <div className="text-sm uppercase tracking-wider text-gray-400">Decision Score</div>
            <div className={`text-5xl font-extrabold ${scoreColorClass}`}>{output.decision_score}</div>
          </div>
          <div className="flex justify-center">
            <CircularProgress value={output.decision_score} />
          </div>
          {output.score_components && (
            <div className="space-y-2">
              {renderScoreBar("Decision Quality", output.score_components.decision_quality)}
              {renderScoreBar("Specificity", output.score_components.specificity)}
              {renderScoreBar("Category Fit", output.score_components.category_fit)}
              {renderScoreBar("Merchant Fit", output.score_components.merchant_fit)}
              {renderScoreBar("Engagement", output.score_components.engagement)}
            </div>
          )}
        </motion.div>

        {/* Suppression Key */}
        {output.suppression_key && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.55, duration: 0.4 }}
            className="glass rounded-lg p-4 border border-cyan-500/20 space-y-2"
          >
            <div className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
              🔐 Suppression Key
            </div>
            <p className="text-xs text-gray-300 font-mono break-all">{output.suppression_key}</p>
          </motion.div>
        )}

        {/* Rationale Section */}
        {output.rationale && output.rationale.length > 0 && (
          <div className="space-y-3">
            <div className="text-sm font-semibold uppercase tracking-wider text-gray-300">
              📋 Decision Rationale
            </div>
            <div className="space-y-2">
              {output.rationale.map((reason, idx) => (
                <RationaleChip key={idx} text={reason} index={idx} />
              ))}
            </div>
          </div>
        )}
      </div>
    </motion.section>
  );
}
