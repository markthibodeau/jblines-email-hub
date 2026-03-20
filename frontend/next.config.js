/** @type {import('next').NextConfig} */
const nextConfig = {
  // standalone output is only needed for Docker/Render deployments
  // set NEXT_STANDALONE=1 in Docker build to enable it
  ...(process.env.NEXT_STANDALONE === "1" && { output: "standalone" }),
  // Point API calls to the backend — set NEXT_PUBLIC_API_URL in env vars
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
}

module.exports = nextConfig
