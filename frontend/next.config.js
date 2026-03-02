/** @type {import('next').NextConfig} */
const nextConfig = {
  // Backend API URL is baked in at Docker build time for Cloud Run.
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
};

module.exports = nextConfig;
