import { AnimatePresence, motion } from 'framer-motion'
import { useUIStore } from '../../stores/ui.store'

export function ToastContainer() {
  const { toasts, removeToast } = useUIStore()

  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, x: 20, scale: 0.95 }}
            animate={{ opacity: 1, x: 0,  scale: 1    }}
            exit={{ opacity: 0, x: 8,   scale: 0.97 }}
            transition={{ type: 'spring', stiffness: 280, damping: 26, mass: 0.7 }}
            style={{ willChange: 'transform, opacity' }}
            className={[
              'pointer-events-auto flex items-center gap-3',
              'rounded-2xl px-4 py-3 max-w-xs',
              'font-mono text-[13px]',
              'bg-surface-2',
              toast.type === 'success' && 'shadow-[0_0_0_1px_rgba(157,140,255,0.22),0_8px_32px_rgba(0,0,0,0.5)]',
              toast.type === 'error'   && 'shadow-[0_0_0_1px_rgba(248,113,113,0.3),0_8px_32px_rgba(0,0,0,0.5)]',
              toast.type === 'info'    && 'shadow-[0_0_0_1px_rgba(157,140,255,0.14),0_8px_32px_rgba(0,0,0,0.5)]',
            ]
              .filter(Boolean)
              .join(' ')}
          >
            {/* Status dot */}
            <span
              className={[
                'size-2 rounded-full shrink-0 ring-4',
                toast.type === 'success' && 'bg-jade ring-jade-dim',
                toast.type === 'error'   && 'bg-ember ring-ember-dim',
                toast.type === 'info'    && 'bg-muted ring-[rgba(74,71,142,0.18)]',
              ]
                .filter(Boolean)
                .join(' ')}
            />
            <span className="text-text flex-1">{toast.message}</span>
            <button
              onClick={() => removeToast(toast.id)}
              className="ml-1 text-text-faint hover:text-text-dim transition-colors duration-150 relative after:absolute after:inset-[-8px]"
              aria-label="Dismiss"
            >
              <svg width="10" height="10" viewBox="0 0 14 14" fill="none">
                <path d="M1 1l12 12M13 1L1 13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              </svg>
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
