/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: '#040408',
          deep: '#0A0E1A',
          cyan: '#00F0FF',
          magenta: '#FF00E5',
          gold: '#FFD700',
          text: '#F4F4F5',
          muted: '#A1A1AA',
          border: 'rgba(167, 139, 250, 0.15)',
          glow: 'rgba(167, 139, 250, 0.35)',
        }
      },
      fontFamily: {
        heading: ['Orbitron', 'Rajdhani', 'sans-serif'],
        subheading: ['Space Grotesk', 'sans-serif'],
        body: ['Outfit', 'sans-serif']
      },
      animation: {
        'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-pulse': 'glow 2s ease-in-out infinite alternate',
        'fade-up': 'fadeUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(0, 240, 255, 0.2), 0 0 10px rgba(0, 240, 255, 0.2)' },
          '100%': { boxShadow: '0 0 15px rgba(0, 240, 255, 0.6), 0 0 25px rgba(0, 240, 255, 0.4)' }
        },
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        }
      }
    },
  },
  plugins: [],
}
