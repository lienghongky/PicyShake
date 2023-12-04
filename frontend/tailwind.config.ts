import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
      backgroundColor: {
        'black-opactiy-10': 'rgba(0,0,0,0.1)',
        'black-opactiy-20': 'rgba(0,0,0,0.2)',
        'black-opactiy-30': 'rgba(0,0,0,0.3)',
        'black-opactiy-50': 'rgba(0,0,0,0.5)',
        'black-opactiy-70': 'rgba(0,0,0,0.7)',
        'black-opactiy-80': 'rgba(0,0,0,0.8)',
        'black-opactiy-90': 'rgba(0,0,0,0.9)',


      },
    },
  },
  plugins: [require("daisyui")],
}
export default config
