/** @type {import('next').NextConfig} */
const nextConfig = {
  // Required for @polkadot packages (uses WASM internally)
  webpack: (config) => {
    config.experiments = { ...config.experiments, asyncWebAssembly: true };
    config.ignoreWarnings = [{ module: /node_modules\/@polkadot/ }];
    return config;
  },
  // Next.js 15: opt into stable server external packages handling
  serverExternalPackages: [],
};

export default nextConfig;
