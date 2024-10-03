/** @type {import('next').NextConfig} */
const nextConfig = {
    basePath: '/PicyShake',
    output: 'export',
    images: {
        domains: ['*'],
      },
      typescript: {
      ignoreBuildErrors: true,
      }
}

module.exports = nextConfig
