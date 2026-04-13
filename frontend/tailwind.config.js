/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg:          '#09070d',
        surface:     '#141019',
        'surface-2': '#1b1622',
        'surface-3': '#241d2f',
        // Primary accent — dragon flame
        jade:        '#ff7a59',
        'jade-dim':  'rgba(255,122,89,0.11)',
        'jade-glow': 'rgba(255,122,89,0.2)',
        // Danger — ember red
        ember:       '#ff5c5c',
        'ember-dim': 'rgba(255,92,92,0.14)',
        // Secondary — forged gold
        gold:        '#f3c677',
        'gold-dim':  'rgba(243,198,119,0.12)',
        muted:       '#6a4d82',
        text:        '#f8f4ef',
        'text-dim':  '#b29eb8',
        'text-faint':'#7c667f',
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', 'serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        card:       '0 0 0 1px rgba(255,122,89,0.14), 0 12px 34px rgba(6,4,10,0.65)',
        'card-hover':'0 0 0 1px rgba(255,122,89,0.28), 0 18px 48px rgba(0,0,0,0.55)',
        modal:      '0 0 0 1px rgba(255,122,89,0.2), 0 24px 80px rgba(0,0,0,0.82)',
        'jade-glow':'0 0 32px rgba(255,122,89,0.35)',
        'ember-glow':'0 0 32px rgba(255,92,92,0.32)',
        'gold-glow': '0 0 32px rgba(243,198,119,0.32)',
      },
      animation: {
        'pulse-jade':  'pulseViolet 3s ease-in-out infinite',
        'pulse-amber': 'pulseGold 3s ease-in-out infinite',
        'pulse-ember': 'pulseRose 3s ease-in-out infinite',
        'float':       'float 7s ease-in-out infinite',
        'spin-slow':   'spin 18s linear infinite',
        'shimmer':     'shimmer 2.2s ease-in-out infinite',
        'aurora':      'aurora 10s ease-in-out infinite',
        'drift-up':    'driftUp linear infinite',
      },
      keyframes: {
        pulseViolet: {
          '0%, 100%': { boxShadow: '0 0 0 1px rgba(255,122,89,0.2), 0 0 14px rgba(255,122,89,0.09)' },
          '50%':      { boxShadow: '0 0 0 1px rgba(255,122,89,0.46),  0 0 30px rgba(255,122,89,0.24)' },
        },
        pulseGold: {
          '0%, 100%': { boxShadow: '0 0 0 1px rgba(243,198,119,0.2), 0 0 12px rgba(243,198,119,0.1)' },
          '50%':      { boxShadow: '0 0 0 1px rgba(243,198,119,0.46),  0 0 24px rgba(243,198,119,0.22)'  },
        },
        pulseRose: {
          '0%, 100%': { boxShadow: '0 0 0 1px rgba(255,92,92,0.2), 0 0 12px rgba(255,92,92,0.08)' },
          '50%':      { boxShadow: '0 0 0 1px rgba(255,92,92,0.44),  0 0 24px rgba(255,92,92,0.22)'  },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-14px)' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-600px 0' },
          '100%': { backgroundPosition: '600px 0'  },
        },
        aurora: {
          '0%, 100%': { opacity: '0.45', transform: 'scale(1) rotate(0deg)' },
          '33%':      { opacity: '0.7',  transform: 'scale(1.1) rotate(2.5deg)'  },
          '66%':      { opacity: '0.55', transform: 'scale(0.95) rotate(-2deg)' },
        },
        driftUp: {
          '0%':   { transform: 'translateY(0) translateX(0)',             opacity: '0'   },
          '8%':   { opacity: '0.55'                                                       },
          '92%':  { opacity: '0.35'                                                       },
          '100%': { transform: 'translateY(-100vh) translateX(var(--drift,20px))', opacity: '0' },
        },
      },
    },
  },
  plugins: [],
}
