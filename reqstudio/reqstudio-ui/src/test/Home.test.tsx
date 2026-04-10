/**
 * Home.tsx — testes da landing page (Design System showcase).
 *
 * Cobre: renderização, elementos de texto, botões, design tokens.
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Home from '@/pages/Home'
import { ThemeProvider } from '@/contexts/ThemeContext'

function renderHome() {
  return render(
    <ThemeProvider>
      <Home />
    </ThemeProvider>,
  )
}

describe('Home page', () => {
  it('renders the ReqStudio header', () => {
    renderHome()
    expect(screen.getByText('ReqStudio')).toBeInTheDocument()
  })

  it('renders the version badge', () => {
    renderHome()
    expect(screen.getByText('v0.1.0')).toBeInTheDocument()
  })

  it('renders the hero heading', () => {
    renderHome()
    const headings = screen.getAllByRole('heading', { level: 1 })
    expect(headings.length).toBeGreaterThanOrEqual(1)
  })

  it('renders the hero description', () => {
    renderHome()
    expect(
      screen.getByText(/Traduza seu conhecimento de domínio/),
    ).toBeInTheDocument()
  })

  it('renders Novo Projeto button', () => {
    renderHome()
    expect(
      screen.getByRole('button', { name: /Novo Projeto/i }),
    ).toBeInTheDocument()
  })

  it('renders Ver Documetação button', () => {
    renderHome()
    expect(
      screen.getByRole('button', { name: /Ver Documetação/i }),
    ).toBeInTheDocument()
  })

  it('renders Design System section', () => {
    renderHome()
    expect(
      screen.getByText('Design System — Tokens'),
    ).toBeInTheDocument()
  })

  it('renders color swatches', () => {
    renderHome()
    expect(screen.getByText('Primary')).toBeInTheDocument()
    expect(screen.getByText('Success')).toBeInTheDocument()
    expect(screen.getByText('Error')).toBeInTheDocument()
  })

  it('renders typography scale section', () => {
    renderHome()
    expect(screen.getByText('Escala Tipográfica')).toBeInTheDocument()
    expect(screen.getByText(/Display — 30px/)).toBeInTheDocument()
  })
})
