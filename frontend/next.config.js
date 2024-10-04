/** @type {import('next').NextConfig} */
const nextConfig = {
    basePath: '/PicyShake',
    output: 'export',
    images: {
        domains: ['*'],
        unoptimized: true
      },
      typescript: {
      ignoreBuildErrors: true,
      }
}

module.exports = nextConfig
