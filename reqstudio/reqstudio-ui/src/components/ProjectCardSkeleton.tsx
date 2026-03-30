/**
 * ProjectCardSkeleton — loading state pulsante (UX-DR17, Story 3.2).
 */

export function ProjectCardSkeleton() {
  return (
    <div className="rounded-[var(--radius-lg)] border border-border bg-card p-[var(--space-4)] flex flex-col gap-[var(--space-3)]">
      {/* Icon */}
      <div className="w-9 h-9 rounded-[var(--radius-md)] bg-muted animate-pulse" />
      {/* Title */}
      <div className="space-y-2">
        <div className="h-4 w-3/4 rounded bg-muted animate-pulse" />
        <div className="h-3 w-1/3 rounded bg-muted animate-pulse" />
        <div className="h-3 w-full rounded bg-muted animate-pulse" />
      </div>
      {/* Progress */}
      <div className="space-y-1.5">
        <div className="flex justify-between">
          <div className="h-3 w-16 rounded bg-muted animate-pulse" />
          <div className="h-3 w-8 rounded bg-muted animate-pulse" />
        </div>
        <div className="h-1.5 rounded-full bg-muted animate-pulse" />
      </div>
      {/* Footer */}
      <div className="h-3 w-1/2 rounded bg-muted animate-pulse pt-[var(--space-1)] border-t border-border" />
    </div>
  )
}
