/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      { protocol: "http", hostname: "localhost" },
      { protocol: "https", hostname: "**.b-cdn.net" }, // Bunny Stream CDN (I-03)
    ],
  },
  // PWA (NF-04): production'da next-pwa yoki Serwist bilan kengaytiriladi
};

module.exports = nextConfig;
