import { motion } from 'framer-motion'
import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
type Size = 'sm' | 'md' | 'lg'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
  staticPress?: boolean
  children: ReactNode
}

const variantClasses: Record<Variant, string> = {
  secondary: [
    'bg-surface-3 font-mono text-text-dim',
    'shadow-[0_0_0_1px_rgba(157,140,255,0.12)]',
    'hover:shadow-[0_0_0_1px_rgba(157,140,255,0.28)] hover:text-text',
    'transition-[box-shadow,color] duration-200',
  ].join(' '),
  primary: [
    'relative overflow-hidden font-mono font-medium',
    'bg-gradient-to-br from-[#a899ff] to-[#7c6bff]',
    'text-white',
    'shadow-[0_1px_0_rgba(255,255,255,0.15)_inset,0_-1px_0_rgba(0,0,0,0.2)_inset]',
    'hover:brightness-110',
    'transition-[filter,opacity] duration-200',
    // inner shine
    'before:absolute before:inset-0 before:rounded-[inherit]',
    'before:bg-gradient-to-b before:from-white/[0.1] before:to-transparent',
    'before:pointer-events-none',
  ].join(' '),
  ghost: [
    'bg-transparent font-mono',
    'text-text-dim hover:text-text',
    'shadow-[0_0_0_1px_rgba(157,140,255,0.18)]',
    'hover:shadow-[0_0_0_1px_rgba(157,140,255,0.35),0_0_12px_rgba(157,140,255,0.08)]',
    'hover:bg-jade-dim',
    'transition-[box-shadow,background-color,color] duration-200',
  ].join(' '),
  danger: [
    'bg-ember-dim font-mono text-ember',
    'shadow-[0_0_0_1px_rgba(248,113,113,0.2)]',
    'hover:shadow-[0_0_0_1px_rgba(248,113,113,0.4)]',
    'transition-[box-shadow] duration-200',
  ].join(' '),
}

const sizeClasses: Record<Size, string> = {
  sm: 'h-8 px-3.5 text-xs rounded-xl min-w-[44px]',
  md: 'h-10 px-5 text-sm rounded-[14px] min-w-[44px]',
  lg: 'h-12 px-7 text-[15px] rounded-2xl min-w-[44px]',
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  staticPress = false,
  className = '',
  children,
  disabled,
  ...rest
}: Props) {
  const isDisabled = disabled || loading

  return (
    <motion.button
      whileTap={staticPress || isDisabled ? undefined : { scale: 0.96 }}
      transition={{ type: 'spring', stiffness: 500, damping: 38, mass: 0.5 }}
      className={[
        'inline-flex items-center justify-center gap-2 cursor-pointer select-none',
        'disabled:opacity-40 disabled:cursor-not-allowed',
        variantClasses[variant],
        sizeClasses[size],
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      style={{ willChange: 'transform' }}
      disabled={isDisabled}
      {...(rest as Record<string, unknown>)}
    >
      {loading ? (
        <>
          <span className="size-4 rounded-full border-[1.5px] border-current border-t-transparent animate-spin" />
          <span>{children}</span>
        </>
      ) : (
        children
      )}
    </motion.button>
  )
}
