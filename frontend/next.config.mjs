/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Never let lint/type issues block a deploy build on Vercel.
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
