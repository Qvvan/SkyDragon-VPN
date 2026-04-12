import { AnimatePresence, motion } from 'framer-motion'
import type { ReactNode } from 'react'
import { useEffect } from 'react'
import {
  modalOverlay,
  modalPanel,
  modalPanelFull,
  spring,
} from '../../lib/motion'

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
    if (!open) return
    const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth
    const header = document.querySelector<HTMLElement>('header[data-sticky]')
    document.body.style.overflow = 'hidden'
    if (scrollbarWidth > 0) {
      document.body.style.paddingRight = `${scrollbarWidth}px`
      if (header) header.style.paddingRight = `${scrollbarWidth}px`
    }
    return () => {
      document.body.style.overflow = ''
      document.body.style.paddingRight = ''
      if (header) header.style.paddingRight = ''
    }
  }, [open])

  const isFull = size === 'full'
  const panelVariants = isFull ? modalPanelFull : modalPanel

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            variants={modalOverlay}
            initial="hidden"
            animate="visible"
            exit="exit"
            transition={{ duration: 0.22, ease: 'easeOut' }}
            className="fixed inset-0 z-40"
            style={{
              background: 'rgba(3,3,9,0.82)',
              backdropFilter: 'blur(18px)',
              WebkitBackdropFilter: 'blur(18px)',
            }}
            onClick={onClose}
          />

          {/* Centering shell */}
          <div className={[
            'fixed z-50 pointer-events-none',
            isFull
              ? 'inset-0 flex items-end sm:items-center justify-center p-0 sm:p-4'
              : 'inset-0 flex items-center justify-center p-3 sm:p-5',
          ].join(' ')}>
            <motion.div
              variants={panelVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              transition={spring.gentle}
              style={{
                willChange: 'transform, opacity',
                border: '1px solid rgba(157,140,255,0.12)',
                background: 'linear-gradient(160deg, #0f0e24 0%, #0c0b1f 60%, #0a0919 100%)',
              }}
              className={[
                'pointer-events-auto w-full relative',
                sizeClasses[size],
                isFull
                  ? 'rounded-t-[28px] sm:rounded-[28px] shadow-modal max-h-[92vh] sm:max-h-[88vh] flex flex-col'
                  : 'rounded-[28px] shadow-modal max-h-[90vh] flex flex-col',
              ].join(' ')}
            >
              {/* Top accent line */}
              <div
                className="absolute top-0 left-8 right-8 h-px rounded-full pointer-events-none"
                style={{ background: 'linear-gradient(90deg, transparent, rgba(157,140,255,0.4), transparent)' }}
              />

              {/* Header */}
              {title && (
                <div className={[
                  'flex items-center justify-between px-6 sm:px-7 py-4 sm:py-5 shrink-0',
                  'border-b border-[rgba(157,140,255,0.07)]',
                ].join(' ')}>
                  <h2 className="font-display text-xl sm:text-2xl font-medium text-text tracking-wide leading-tight">
                    {title}
                  </h2>
                  <button
                    onClick={onClose}
                    className={[
                      'relative flex items-center justify-center size-9 rounded-full ml-4 shrink-0',
                      'text-text-dim hover:text-text',
                      'hover:bg-surface-3',
                      'transition-[background-color,color] duration-150',
                      'after:absolute after:inset-[-6px]',
                    ].join(' ')}
                    aria-label="Close"
                  >
                    <svg width="12" height="12" viewBox="0 0 14 14" fill="none">
                      <path d="M1 1l12 12M13 1L1 13" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
                    </svg>
                  </button>
                </div>
              )}

              {/* Content — scrollable */}
              <div className={[
                'flex-1 overflow-y-auto',
                !title ? 'p-2' : '',
              ].join(' ')}
                style={{ scrollbarWidth: 'none' }}
              >
                {children}
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}
