// Where /api/v1 requests are forwarded: BACKEND_URL if set, the live backend on Vercel, else the local one.
const backendUrl = (
  process.env.BACKEND_URL || (process.env.VERCEL ? 'https://gym-ai-backend.vercel.app' : 'http://localhost:8000')
).replace(/\/$/, '');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  async rewrites() {
    return [{ source: '/api/v1/:path*', destination: `${backendUrl}/api/v1/:path*` }];
  },
};

module.exports = nextConfig;
