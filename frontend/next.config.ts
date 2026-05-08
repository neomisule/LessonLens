import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for minimal Docker images
  output: "standalone",

  // Compress responses
  compress: true,

  images: {
    remotePatterns: [
      { protocol: "https", hostname: "img.youtube.com" },
      { protocol: "https", hostname: "i.ytimg.com" },
    ],
    // Enable lazy loading by default (Next.js default; explicit for clarity)
    unoptimized: false,
  },

  // Proxy API requests to the backend; avoids CORS in production
  async rewrites() {
    const backendUrl =
      process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },

  // Security headers (also defined in vercel.json for Vercel; keep both)
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options",  value: "nosniff"       },
          { key: "X-Frame-Options",          value: "DENY"          },
          { key: "Referrer-Policy",          value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },
};

export default nextConfig;
