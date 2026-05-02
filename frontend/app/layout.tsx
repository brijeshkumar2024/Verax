import type { Metadata } from "next";
import { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "VERAX",
  description: "Deterministic merchant growth decision engine",
  icons: {
    icon: "/icon.png",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <div className="grid-bg" />
        <div className="relative z-10">{children}</div>
      </body>
    </html>
  );
}
