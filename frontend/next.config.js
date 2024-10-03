/** @type {import('next').NextConfig} */
const nextConfig = {
    images: {
        domains: ['*'],
      },
      typescript: {
      ignoreBuildErrors: true,
      }
}

module.exports = nextConfig
