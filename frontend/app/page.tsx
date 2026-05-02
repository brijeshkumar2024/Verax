import ComposeSimulator from "../components/ComposeSimulator";
import { Header } from "@/components/Header";

export default function Home() {
  return (
    <>
      <Header />

      {/* Hero — product clarity above the fold */}
      <div className="mx-auto max-w-7xl px-4 pt-10 pb-2">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-2">
            <h2 className="text-2xl md:text-3xl font-bold text-white leading-snug">
              Real-time growth decisions for merchants.{" "}
              <span className="bg-gradient-to-r from-emerald-300 to-cyan-400 bg-clip-text text-transparent">
                No guesswork. No randomness.
              </span>
            </h2>
            <p className="text-gray-400 text-sm md:text-base max-w-2xl leading-relaxed">
              VERAX analyses live business signals — demand spikes, rating drops, competitor moves — and produces a
              structured, explainable growth recommendation. Every decision is deterministic: same inputs always
              produce the same output, making every recommendation auditable and trustworthy.
            </p>
          </div>
          <div className="flex items-center lg:justify-end gap-6">
            {[
              { value: "100%", label: "Deterministic" },
              { value: "<300ms", label: "Decision latency" },
              { value: "8", label: "Trigger types" },
            ].map(({ value, label }) => (
              <div key={label} className="text-center">
                <div className="text-xl font-bold text-emerald-400">{value}</div>
                <div className="text-xs text-gray-500 mt-0.5">{label}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="mt-6 h-px bg-gradient-to-r from-emerald-500/30 via-cyan-500/20 to-transparent" />
      </div>

      <ComposeSimulator />
    </>
  );
}
