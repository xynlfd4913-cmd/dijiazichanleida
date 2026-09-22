const isDevelopment = process.env.NODE_ENV === "development";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // A running `next start` reads immutable build assets from `.next`. Keeping
  // the dev compiler in a separate directory prevents `next dev` from
  // replacing those files and leaving the production page without CSS.
  distDir: isDevelopment ? ".next-dev" : ".next",
};

export default nextConfig;
