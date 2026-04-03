import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ChatInput } from '@/components/chat/ChatInput'

describe('ChatInput Behavior', () => {
  it('calls onSend when Enter is pressed without Shift', () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} />)
    
    const textarea = screen.getByLabelText('Mensagem para a IA')
    fireEvent.change(textarea, { target: { value: 'Olá mundo' } })
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter', shiftKey: false })
    
    expect(onSend).toHaveBeenCalledWith('Olá mundo')
  })

  it('does NOT call onSend when Shift+Enter is pressed', () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} />)
    
    const textarea = screen.getByLabelText('Mensagem para a IA')
    fireEvent.change(textarea, { target: { value: 'Nova linha' } })
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter', shiftKey: true })
    
    expect(onSend).not.toHaveBeenCalled()
  })

  it('trims whitespace and clears input after sending', () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} />)
    
    const textarea = screen.getByLabelText('Mensagem para a IA') as HTMLTextAreaElement
    fireEvent.change(textarea, { target: { value: '  texto com espaços   ' } })
    
    const sendButton = screen.getByLabelText('Enviar mensagem')
    fireEvent.click(sendButton)
    
    expect(onSend).toHaveBeenCalledWith('texto com espaços')
    expect(textarea.value).toBe('')
  })

  it('disables send button when input is empty or only whitespace', () => {
    render(<ChatInput onSend={vi.fn()} />)
    
    const textarea = screen.getByLabelText('Mensagem para a IA')
    const sendButton = screen.getByLabelText('Enviar mensagem') as HTMLButtonElement
    
    // Initially empty
    expect(sendButton.disabled).toBe(true)
    
    // Only whitespace
    fireEvent.change(textarea, { target: { value: '   ' } })
    expect(sendButton.disabled).toBe(true)
    
    // Valid text
    fireEvent.change(textarea, { target: { value: 'a' } })
    expect(sendButton.disabled).toBe(false)
  })
})
