/** @type {import('next').NextConfig} */
const nextConfig = {
  // Point API calls to the backend — set NEXT_PUBLIC_API_URL in Vercel env vars
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
}

module.exports = nextConfig
