import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Required for Vercel: set NEXT_PUBLIC_API_URL to your Render backend URL
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
};

export default nextConfig;
