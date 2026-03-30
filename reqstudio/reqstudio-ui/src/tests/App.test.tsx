import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '../App'

describe('App Smoke Test', () => {
  it('renders without crashing and shows loading state initially (Suspense)', () => {
    render(<App />)
    expect(screen.getByText(/carregando/i)).toBeInTheDocument()
  })
})
