import { AnimatePresence, motion } from 'framer-motion'

interface Props {
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
  label?: string
}

export function Toggle({ checked, onChange, disabled, label }: Props) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={[
        'relative inline-flex h-6 w-11 items-center rounded-full shrink-0',
        'transition-colors duration-250',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-jade focus-visible:ring-offset-2 focus-visible:ring-offset-bg',
        'disabled:opacity-40 disabled:cursor-not-allowed',
        checked
          ? 'bg-gradient-to-br from-[#a899ff] to-[#7c6bff] shadow-[0_0_12px_rgba(157,140,255,0.3)]'
          : 'bg-surface-3 shadow-[0_0_0_1px_rgba(157,140,255,0.1)]',
      ].join(' ')}
    >
      <motion.span
        layout
        transition={{ type: 'spring', duration: 0.28, bounce: 0.1 }}
        className={[
          'absolute h-[18px] w-[18px] rounded-full shadow-md',
          checked
            ? 'left-[26px] bg-white'
            : 'left-[3px] bg-text-dim',
        ].join(' ')}
        style={{ top: '50%', translateY: '-50%' }}
      />

      <span className="absolute inset-0 flex items-center justify-end pr-1.5 pointer-events-none">
        <AnimatePresence initial={false} mode="popLayout">
          {checked && (
            <motion.span
              key="on"
              initial={{ opacity: 0, scale: 0.3, filter: 'blur(3px)' }}
              animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
              exit={{ opacity: 0, scale: 0.3, filter: 'blur(3px)' }}
              transition={{ type: 'spring', duration: 0.26, bounce: 0 }}
              className="text-white"
            >
              <svg width="9" height="9" viewBox="0 0 24 24" fill="currentColor">
                <path d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
              </svg>
            </motion.span>
          )}
        </AnimatePresence>
      </span>
    </button>
  )
}
