import { useMemo } from 'react'
import type { Message } from '@/services/sessionsApi'

interface Props {
  messages: Message[]
}

export function SessionTelemetryWidget({ messages }: Props) {
  // Sum up tokens and cost memoized
  const { totalInput, totalOutput, totalCost, totalLatency, lastModel } = useMemo(() => {
    let input = 0
    let output = 0
    let cost = 0
    let latency = 0
    let model = ''

    messages.forEach((msg) => {
      if (msg.role === 'assistant') {
        input += msg.input_tokens || 0
        output += msg.output_tokens || 0
        cost += msg.cost_usd || 0
        latency += msg.latency_ms || 0
        if (msg.model) {
          model = msg.model
        }
      }
    })

    return { totalInput: input, totalOutput: output, totalCost: cost, totalLatency: latency, lastModel: model }
  }, [messages])

  const totalTokens = totalInput + totalOutput

  if (totalTokens === 0) {
    return null
  }

  const formatCost = (val: number) => {
    if (val === 0) return '$0.00'
    if (val < 0.001) return `<$0.01` 
    return `$${val.toFixed(2)}`
  }

  const formatTokens = (val: number) => {
    return val >= 1000 ? `${(val / 1000).toFixed(1)}k` : val.toString()
  }

  return (
    <div className="relative group flex items-center">
      <div 
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm cursor-default transition-colors hover:bg-black/5 dark:hover:bg-white/5"
        style={{ border: '1px solid var(--border)', color: 'var(--rs-text-secondary)', background: 'var(--rs-surface)' }}
      >
        <span>💰</span>
        <span className="font-medium" style={{ color: 'var(--rs-text-primary)' }}>{formatCost(totalCost)}</span>
        <span className="text-xs opacity-50">•</span>
        <span>{formatTokens(totalTokens)} tokens</span>
      </div>

      {/* Expandable Tooltip */}
      <div 
        className="absolute top-full right-0 mt-2 w-64 p-3 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 text-sm pointer-events-none"
        style={{ background: 'var(--rs-surface)', border: '1px solid var(--border)', color: 'var(--rs-text-secondary)' }}
      >
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span>Input Tokens:</span>
            <span className="font-medium" style={{ color: 'var(--rs-text-primary)' }}>{totalInput.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center">
            <span>Output Tokens:</span>
            <span className="font-medium" style={{ color: 'var(--rs-text-primary)' }}>{totalOutput.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center">
            <span>Custo Total:</span>
            <span className="font-medium" style={{ color: 'var(--rs-text-primary)' }}>${totalCost.toFixed(4)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span>Latência Total:</span>
            <span className="font-medium" style={{ color: 'var(--rs-text-primary)' }}>{(totalLatency / 1000).toFixed(2)}s</span>
          </div>
          {lastModel && (
            <div className="flex justify-between items-center pt-2 mt-2 border-t" style={{ borderColor: 'var(--border)' }}>
              <span>Modelo Atual:</span>
              <span className="font-medium text-xs font-mono px-1.5 py-0.5 rounded bg-black/5 dark:bg-white/5" style={{ color: 'var(--rs-text-primary)' }}>
                {lastModel}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
