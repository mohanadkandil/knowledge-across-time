/** @type {import('next').NextConfig} */
const nextConfig = {
  outputFileTracingIncludes: {
    '/api/lens': ['./app/data/**'],
  },
};

export default nextConfig;
