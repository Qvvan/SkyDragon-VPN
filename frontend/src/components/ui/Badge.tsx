import type { ReactNode } from 'react'

type Variant = 'jade' | 'ember' | 'amber' | 'muted' | 'trial' | 'green'

interface Props {
  children: ReactNode
  variant?: Variant
}

const variantClasses: Record<Variant, string> = {
  jade:  'bg-jade-dim text-jade shadow-[0_0_0_1px_rgba(157,140,255,0.2)]',
  green: 'bg-[rgba(74,222,128,0.1)] text-[#4ade80] shadow-[0_0_0_1px_rgba(74,222,128,0.22)]',
  ember: 'bg-ember-dim text-ember shadow-[0_0_0_1px_rgba(248,113,113,0.22)]',
  amber: 'bg-gold-dim text-gold shadow-[0_0_0_1px_rgba(226,185,110,0.22)]',
  muted: 'bg-[rgba(74,71,142,0.18)] text-text-dim shadow-[0_0_0_1px_rgba(74,71,142,0.32)]',
  trial: 'bg-[rgba(129,140,248,0.1)] text-[#a5b4fc] shadow-[0_0_0_1px_rgba(129,140,248,0.22)]',
}

export function Badge({ children, variant = 'jade' }: Props) {
  return (
    <span
      className={[
        'inline-flex items-center rounded-full px-2.5 py-0.5',
        'font-mono text-[11px] font-medium tracking-wide',
        variantClasses[variant],
      ].join(' ')}
    >
      {children}
    </span>
  )
}
