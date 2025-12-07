/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        slack: {
          purple: '#611f69',
          green: '#2BAC76',
          blue: '#1264A3',
          red: '#E01E5A',
          yellow: '#ECB22E',
        },
      },
    },
  },
  plugins: [],
}
