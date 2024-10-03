/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'export',
    images: {
        domains: ['*'],
      },
      typescript: {
      ignoreBuildErrors: true,
      }
}

module.exports = nextConfig
