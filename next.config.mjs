const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? process.env.BASE_PATH ?? '/noema';
export default {
  output: 'export',
  distDir: process.env.NODE_ENV === 'development' ? '.next-dev' : '.next',
  trailingSlash: true,
  basePath,
  env: { NEXT_PUBLIC_BASE_PATH: basePath },
  images: { unoptimized: true },
  poweredByHeader: false,
  devIndicators: false,
};
