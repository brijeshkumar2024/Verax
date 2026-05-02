"use client";

import { motion } from "framer-motion";

interface CircularProgressProps {
  value: number;
  size?: number;
  strokeWidth?: number;
}

export function CircularProgress({ value, size = 140, strokeWidth = 6 }: CircularProgressProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  const getColor = () => {
    if (value < 50) return "#FF4D5D";
    if (value < 75) return "#FFB84D";
    return "#21D978";
  };

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(33, 217, 120, 0.1)"
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor()}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          strokeLinecap="round"
          filter="drop-shadow(0 0 6px rgba(33, 217, 120, 0.3))"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <motion.span
          className="text-3xl font-bold"
          style={{ color: getColor() }}
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3, duration: 0.4 }}
        >
          {value}
        </motion.span>
        <span className="text-xs text-gray-400 font-medium">Score</span>
      </div>
    </div>
  );
}

interface RationaleChipProps {
  text: string;
  index: number;
}

export function RationaleChip({ text, index }: RationaleChipProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.4 }}
      className="glass rounded-lg px-4 py-3 text-sm border border-emerald-500/20 hover:border-emerald-500/40 transition-all"
    >
      <div className="flex items-start gap-3">
        <div className="mt-1 h-1.5 w-1.5 rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400 flex-shrink-0" />
        <p className="text-gray-200 leading-relaxed">{text}</p>
      </div>
    </motion.div>
  );
}

export function LoadingSkeleton() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-4"
    >
      <div className="h-20 glass rounded-xl shimmer" />
      <div className="grid grid-cols-3 gap-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-16 glass rounded-lg shimmer" />
        ))}
      </div>
      <div className="h-24 glass rounded-lg shimmer" />
    </motion.div>
  );
}
