import type { NextConfig } from "next";

const API_URL = process.env.MISCONAI_API_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Self-contained server bundle for the Docker image.
  output: "standalone",
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  // Model calls can take well over the default 30s proxy timeout.
  experimental: {
    proxyTimeout: 180_000,
  },
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
};

export default nextConfig;
