import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  
  // API 프록시 설정
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  },
};

export default nextConfig;
