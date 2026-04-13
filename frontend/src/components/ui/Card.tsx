import type { HTMLAttributes, ReactNode } from 'react'

interface Props extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  glow?: boolean
  grid?: boolean
}

export function Card({ children, glow, grid, className = '', ...rest }: Props) {
  return (
    <div
      className={[
        'relative rounded-[24px] p-[3px] bg-surface overflow-hidden',
        glow ? 'animate-pulse-jade' : 'shadow-card',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      {...rest}
    >
      {/* Diamond grid texture */}
      {grid && (
        <div
          className="absolute inset-0 rounded-[24px] pointer-events-none opacity-100"
          style={{
            backgroundImage:
              'repeating-linear-gradient(45deg, rgba(255,122,89,0.014) 0px, rgba(255,122,89,0.014) 1px, transparent 1px, transparent 48px), ' +
              'repeating-linear-gradient(-45deg, rgba(255,122,89,0.014) 0px, rgba(255,122,89,0.014) 1px, transparent 1px, transparent 48px)',
          }}
        />
      )}
      <div className="relative rounded-[22px] bg-surface-2 p-4">{children}</div>
    </div>
  )
}
