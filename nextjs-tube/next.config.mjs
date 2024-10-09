import nextPWA from 'next-pwa';

/** @type {import('next').NextConfig} */
const withPWA = nextPWA({
  dest: 'public',
});

const nextConfig = {
  reactStrictMode: true,
  // Disable ESLint
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: {
    domains: ['img.youtube.com'],
  },

  // Add any other Next.js config options here
};

export default withPWA(nextConfig);