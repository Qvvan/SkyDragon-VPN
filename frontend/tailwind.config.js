/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg:          '#07070f',
        surface:     '#0d0c1f',
        'surface-2': '#131228',
        'surface-3': '#1c1a38',
        // Primary accent — soft aether violet
        jade:        '#9d8cff',
        'jade-dim':  'rgba(157,140,255,0.09)',
        'jade-glow': 'rgba(157,140,255,0.18)',
        // Danger — soft rose
        ember:       '#f87171',
        'ember-dim': 'rgba(248,113,113,0.12)',
        // Secondary — champagne gold
        gold:        '#e2b96e',
        'gold-dim':  'rgba(226,185,110,0.09)',
        muted:       '#4a478e',
        text:        '#eeeeff',
        'text-dim':  '#7875a8',
        'text-faint':'#3a3864',
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', 'serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        card:       '0 0 0 1px rgba(157,140,255,0.1), 0 2px 20px rgba(0,0,0,0.45)',
        'card-hover':'0 0 0 1px rgba(157,140,255,0.24), 0 8px 40px rgba(157,140,255,0.1), 0 2px 8px rgba(0,0,0,0.3)',
        modal:      '0 0 0 1px rgba(157,140,255,0.14), 0 24px 80px rgba(0,0,0,0.8)',
        'jade-glow':'0 0 32px rgba(157,140,255,0.35)',
        'ember-glow':'0 0 32px rgba(248,113,113,0.3)',
        'gold-glow': '0 0 32px rgba(226,185,110,0.3)',
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
          '0%, 100%': { boxShadow: '0 0 0 1px rgba(157,140,255,0.16), 0 0 14px rgba(157,140,255,0.07)' },
          '50%':      { boxShadow: '0 0 0 1px rgba(157,140,255,0.4),  0 0 30px rgba(157,140,255,0.22)' },
        },
        pulseGold: {
          '0%, 100%': { boxShadow: '0 0 0 1px rgba(226,185,110,0.16), 0 0 12px rgba(226,185,110,0.06)' },
          '50%':      { boxShadow: '0 0 0 1px rgba(226,185,110,0.4),  0 0 24px rgba(226,185,110,0.2)'  },
        },
        pulseRose: {
          '0%, 100%': { boxShadow: '0 0 0 1px rgba(248,113,113,0.16), 0 0 12px rgba(248,113,113,0.06)' },
          '50%':      { boxShadow: '0 0 0 1px rgba(248,113,113,0.4),  0 0 24px rgba(248,113,113,0.2)'  },
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
