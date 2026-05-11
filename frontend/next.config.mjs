/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  compress: true,

  images: {
    remotePatterns: [
      { protocol: "https", hostname: "img.youtube.com" },
      { protocol: "https", hostname: "i.ytimg.com" },
    ],
    unoptimized: false,
  },

  async rewrites() {
    // BACKEND_URL is the Docker-internal hostname (http://backend:8000).
    // NEXT_PUBLIC_API_URL is the browser-facing URL and resolves to localhost
    // inside the container, so it must NOT be used for server-side rewrites.
    const backendUrl =
      process.env.BACKEND_URL ??
      process.env.NEXT_PUBLIC_API_URL ??
      "http://localhost:8000";
    return {
      // beforeFiles rewrites run before Next.js's own trailing-slash redirect,
      // so /api/v1/subjects (no slash) is proxied directly — no 307 back to the browser.
      beforeFiles: [
        {
          source: "/api/:path*/",
          destination: `${backendUrl}/api/:path*/`,
        },
        {
          source: "/api/:path*",
          destination: `${backendUrl}/api/:path*/`,
        },
      ],
    };
  },

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
