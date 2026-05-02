"use client";

import Image from "next/image";
import { motion } from "framer-motion";

export function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-emerald-500/10">
      <div className="glass">
        <div className="mx-auto max-w-7xl px-4 py-5 md:py-6">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="flex items-center gap-4"
          >
            <Image
              src="/logo.png"
              alt="VERAX Logo"
              width={48}
              height={48}
              priority
              className="w-10 h-10 md:w-12 md:h-12 rounded-md shadow-[0_0_20px_rgba(33,217,120,0.35)] hover:scale-105 transition-transform duration-200"
            />
            <div className="space-y-0.5">
              <div className="flex items-baseline gap-3">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-300 via-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                  VERAX
                </h1>
                <span className="text-xs font-semibold uppercase tracking-widest text-emerald-500/70">
                  v1.0
                </span>
              </div>
              <p className="text-sm text-gray-400 font-light">
                Merchant Growth Decision Engine &mdash; fully deterministic, zero randomness, every output is explainable and auditable.
              </p>
            </div>
          </motion.div>
          <div className="mt-3 h-px w-24 bg-gradient-to-r from-emerald-500 to-cyan-500 opacity-60" />
        </div>
      </div>
    </header>
  );
}
