import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  experimental: {
    caseSensitiveErrors: true,
  },
};

export default nextConfig;
