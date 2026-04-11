import type { InputHTMLAttributes, ReactNode } from 'react'

type OmitConflicts = Omit<InputHTMLAttributes<HTMLInputElement>, 'prefix'>

interface Props extends OmitConflicts {
  label?: string
  error?: string
  prefix?: ReactNode
  suffix?: ReactNode
}

export function Input({ label, error, prefix, suffix, className = '', id, ...rest }: Props) {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label
          htmlFor={inputId}
          className="font-mono text-[10px] text-text-dim uppercase tracking-[0.12em]"
        >
          {label}
        </label>
      )}
      <div
        className={[
          'flex items-center gap-2.5 rounded-2xl px-4 h-12',
          'bg-surface-2',
          'shadow-[0_0_0_1px_rgba(157,140,255,0.12)]',
          'transition-shadow duration-200',
          'focus-within:shadow-[0_0_0_1px_rgba(157,140,255,0.45),0_0_0_4px_rgba(157,140,255,0.07)]',
          error && 'shadow-[0_0_0_1px_rgba(248,113,113,0.45)] focus-within:shadow-[0_0_0_1px_rgba(248,113,113,0.6),0_0_0_4px_rgba(248,113,113,0.07)]',
        ]
          .filter(Boolean)
          .join(' ')}
      >
        {prefix && <span className="text-text-faint shrink-0">{prefix}</span>}
        <input
          id={inputId}
          className={[
            'flex-1 bg-transparent outline-none font-mono text-sm text-text',
            'placeholder:text-text-faint',
            className,
          ]
            .filter(Boolean)
            .join(' ')}
          {...rest}
        />
        {suffix && <span className="text-text-faint shrink-0">{suffix}</span>}
      </div>
      {error && (
        <p className="font-mono text-[11px] text-ember flex items-center gap-1.5">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>
          </svg>
          {error}
        </p>
      )}
    </div>
  )
}
