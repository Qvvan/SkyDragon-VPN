interface Props {
  className?: string
  lines?: number
}

export function Skeleton({ className = '' }: Props) {
  return (
    <div
      className={[
        'rounded-xl overflow-hidden relative',
        'bg-surface-3',
        'skeleton-shimmer',
        className,
      ].join(' ')}
    />
  )
}

export function SkeletonCard() {
  return (
    <div className="rounded-[24px] p-[3px] bg-surface shadow-card">
      <div className="rounded-[22px] bg-surface-2 p-5 space-y-3.5">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-3/4" />
        <div className="flex gap-2.5 pt-1.5">
          <Skeleton className="h-8 w-20 rounded-xl" />
          <Skeleton className="h-8 w-20 rounded-xl" />
        </div>
      </div>
    </div>
  )
}
