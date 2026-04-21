// next.config.js
// Configure le proxy vers le backend FastAPI pour éviter les erreurs CORS en dev.
// En production, utiliser un reverse proxy Nginx ou Traefik.

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,

  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        // Toutes les requêtes /api/v1/... sont proxifiées vers FastAPI
        source:      "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
      {
        // Idem pour /auth/...
        source:      "/auth/:path*",
        destination: `${backendUrl}/auth/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
