/**
 * TypingIndicator — "Refletindo..." com 3 dots animados (Story 5.7, UX-DR17).
 */

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-3" style={{ marginBottom: 'var(--space-3)' }}>
      {/* Avatar */}
      <div
        className="shrink-0 flex items-center justify-center rounded-full"
        style={{
          width: 32,
          height: 32,
          background: 'var(--rs-primary)',
          color: 'white',
          fontSize: 'var(--text-body-sm)',
          fontWeight: 'var(--font-weight-semibold)',
        }}
      >
        IA
      </div>

      {/* Dots */}
      <div
        className="flex items-center gap-1 px-4 py-3 rounded-2xl"
        style={{
          background: 'var(--rs-surface)',
          border: '1px solid var(--border)',
          borderRadius: '20px 20px 20px 4px',
        }}
      >
        <span
          className="text-body-sm"
          style={{ color: 'var(--rs-text-muted)', marginRight: 'var(--space-2)' }}
        >
          Refletindo
        </span>
        <span className="typing-dot" style={{ animationDelay: '0ms' }} />
        <span className="typing-dot" style={{ animationDelay: '200ms' }} />
        <span className="typing-dot" style={{ animationDelay: '400ms' }} />
      </div>
    </div>
  )
}

export default TypingIndicator
