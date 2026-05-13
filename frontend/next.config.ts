import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    // Local dev only: proxy /api/v1/* → FastAPI running at localhost:8000
    // On Vercel, vercel.json routes /api/v1/* → api/backend.py (no rewrite needed here)
    if (process.env.NODE_ENV !== "development") return [];

    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
