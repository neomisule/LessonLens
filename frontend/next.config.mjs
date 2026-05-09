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
    const backendUrl =
      process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
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
