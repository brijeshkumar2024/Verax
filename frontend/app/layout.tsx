"use client";

import { ReactNode } from "react";
import "./globals.css";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>VERAX Control Room</title>
        <meta name="description" content="Deterministic merchant growth decision simulator" />
      </head>
      <body>
        <div className="grid-bg" />
        <div className="relative z-10">{children}</div>
      </body>
    </html>
  );
}
