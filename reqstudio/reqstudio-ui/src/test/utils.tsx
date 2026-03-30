/**
 * Test utilities — wrapper com todos os providers necessários.
 *
 * Uso: import { render, screen } from '@/test/utils'
 * Substitui o render do @testing-library/react com QueryClient fresco.
 */
import { type ReactElement } from 'react'
import { render, type RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

// Cria um QueryClient novo por teste (sem compartilhar cache)
function makeQC() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  })
}

interface WrapperProps {
  children: React.ReactNode
  initialEntries?: string[]
}

function AllProviders({ children, initialEntries = ['/'] }: WrapperProps) {
  const qc = makeQC()
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={initialEntries}>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'> & { initialEntries?: string[] },
) => {
  const { initialEntries, ...rest } = options ?? {}
  return render(ui, {
    wrapper: ({ children }) => (
      <AllProviders initialEntries={initialEntries}>{children}</AllProviders>
    ),
    ...rest,
  })
}

export * from '@testing-library/react'
export { customRender as render }
