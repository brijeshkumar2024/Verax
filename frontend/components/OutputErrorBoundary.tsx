"use client";

import { Component, ReactNode } from "react";

interface Props { children: ReactNode; }
interface State { hasError: boolean; }

export class OutputErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: unknown) {
    console.error("OutputPanel render error:", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="glass rounded-2xl p-6 md:p-8 border border-amber-500/20 space-y-3">
          <p className="text-sm font-semibold text-amber-400">Best estimate available</p>
          <p className="text-sm text-gray-400">
            Unable to render exact output — the decision engine returned a valid result but the display encountered an issue.
            Try running the decision again.
          </p>
          <button
            className="text-xs text-emerald-400 underline"
            onClick={() => this.setState({ hasError: false })}
          >
            Retry display
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
