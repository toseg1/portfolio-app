/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {
    // Pin the workspace root explicitly — otherwise Turbopack's root
    // detection can pick up an unrelated lockfile in a parent directory.
    root: __dirname,
  },
};

module.exports = nextConfig;
