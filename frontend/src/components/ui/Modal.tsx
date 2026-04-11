import { AnimatePresence, motion } from 'framer-motion'
import type { ReactNode } from 'react'
import { useEffect } from 'react'

type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | 'full'

interface Props {
  open: boolean
  onClose: () => void
  title?: string
  children: ReactNode
  size?: ModalSize
}

const sizeClasses: Record<ModalSize, string> = {
  sm:   'max-w-sm',
  md:   'max-w-md',
  lg:   'max-w-2xl',
  xl:   'max-w-4xl',
  full: 'max-w-full mx-3',
}

export function Modal({ open, onClose, title, children, size = 'md' }: Props) {
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [open, onClose])

  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [open])

  const isFull = size === 'full'

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="fixed inset-0 z-40"
            style={{
              background: 'rgba(4,4,10,0.72)',
              backdropFilter: 'blur(12px)',
              WebkitBackdropFilter: 'blur(12px)',
            }}
            onClick={onClose}
          />

          <div className={[
            'fixed z-50 pointer-events-none',
            isFull
              ? 'inset-0 flex items-end sm:items-center justify-center p-0 sm:p-4'
              : 'inset-0 flex items-center justify-center p-4',
          ].join(' ')}>
            <motion.div
              initial={{ opacity: 0, y: isFull ? 40 : 18, scale: isFull ? 1 : 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: isFull ? 24 : 10, scale: isFull ? 1 : 0.97 }}
              transition={{ type: 'spring', duration: 0.42, bounce: 0 }}
              className={[
                'pointer-events-auto w-full',
                sizeClasses[size],
                isFull
                  ? 'rounded-t-[28px] sm:rounded-[24px] bg-surface shadow-modal max-h-[92vh] sm:max-h-[88vh] flex flex-col'
                  : 'rounded-[24px] bg-surface shadow-modal',
              ].join(' ')}
              style={{ border: '1px solid rgba(157,140,255,0.1)' }}
            >
              {/* Header */}
              {title && (
                <div className={[
                  'flex items-center justify-between px-6 py-4 shrink-0',
                  'border-b border-[rgba(157,140,255,0.07)]',
                  isFull ? '' : 'rounded-t-[24px]',
                ].join(' ')}>
                  <h2 className="font-display text-[17px] font-medium text-text tracking-wide">{title}</h2>
                  <button
                    onClick={onClose}
                    className={[
                      'relative flex items-center justify-center size-8 rounded-full',
                      'text-text-dim hover:text-text',
                      'hover:bg-surface-3',
                      'transition-[background-color,color] duration-150',
                      'after:absolute after:inset-[-6px]',
                    ].join(' ')}
                    aria-label="Close"
                  >
                    <svg width="11" height="11" viewBox="0 0 14 14" fill="none">
                      <path d="M1 1l12 12M13 1L1 13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
                    </svg>
                  </button>
                </div>
              )}

              {/* Content */}
              <div className={[
                isFull ? 'flex-1 overflow-y-auto' : '',
                !title ? 'p-2' : '',
              ].join(' ')}>
                {children}
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}
