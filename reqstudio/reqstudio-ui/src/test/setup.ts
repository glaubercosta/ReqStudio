/// <reference types="vitest/globals" />
import '@testing-library/jest-dom'

// jsdom não implementa window.matchMedia — necessário para ThemeContext
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,          // assume light mode nos testes
    media: query,
    onchange: null,
    addListener: () => {},   // deprecated mas necessário para compatibilidade
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})

// Silencia erros de console esperados (ex: React act() warnings)
const originalError = console.error.bind(console)
beforeAll(() => {
  console.error = (msg: unknown, ...args: unknown[]) => {
    if (
      typeof msg === 'string' &&
      (msg.includes('act(') || msg.includes('ReactDOM.render'))
    ) return
    originalError(msg, ...args)
  }
})
afterAll(() => { console.error = originalError })
