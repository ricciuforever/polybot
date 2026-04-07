/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a0a0c',
        card: '#16161a',
        primary: '#4f46e5',
        neon: '#00f2ff',
        accent: '#ff00d9',
      },
      boxShadow: {
        'neon': '0 0 10px rgba(0, 242, 255, 0.5)',
        'accent': '0 0 10px rgba(255, 0, 217, 0.5)',
      },
      backgroundImage: {
        'glass': 'linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%)',
      }
    },
  },
  plugins: [],
}
