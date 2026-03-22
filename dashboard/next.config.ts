import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // API proxy to Python backend
  async rewrites() {
    return [
      {
        source: "/api/pipeline/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
