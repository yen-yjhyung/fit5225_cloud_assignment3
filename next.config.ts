import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: 'export', // Tells Next to output static HTML
  trailingSlash: true, // Needed for S3 to serve correct paths (e.g., /about/index.html)
  images: {
    unoptimized: true // disables next/image optimization (which is SSR-based)
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
