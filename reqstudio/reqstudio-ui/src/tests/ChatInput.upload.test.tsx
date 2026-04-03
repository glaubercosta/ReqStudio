/**
 * Unit tests for ChatInput upload functionality (Story 5.5-4).
 *
 * Tests are purely unit-level:
 *   - uploadDocument is mocked via vi.mock
 *   - No real network calls or file system access
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { ChatInput } from '@/components/chat/ChatInput'

// ── Mocks ────────────────────────────────────────────────────────────────────

vi.mock('@/services/documentsApi', () => ({
  uploadDocument: vi.fn(),
}))

import { uploadDocument } from '@/services/documentsApi'
const mockUpload = uploadDocument as ReturnType<typeof vi.fn>

// ── Helpers ───────────────────────────────────────────────────────────────────

const PROJECT_ID = 'proj-123'

function makeFile(name: string, sizeBytes: number, type = 'application/pdf'): File {
  const content = new Uint8Array(sizeBytes)
  return new File([content], name, { type })
}

function renderChatInput(overrides: Partial<React.ComponentProps<typeof ChatInput>> = {}) {
  const onSend = vi.fn()
  const onUploadSuccess = vi.fn()
  const result = render(
    <ChatInput
      onSend={onSend}
      projectId={PROJECT_ID}
      onUploadSuccess={onUploadSuccess}
      {...overrides}
    />,
  )
  return { ...result, onSend, onUploadSuccess }
}

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('ChatInput — Upload (Story 5.5-4)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── AC 1 & 6: Button visibility ──

  it('renders the upload button when projectId is provided', () => {
    renderChatInput()
    expect(screen.getByRole('button', { name: /anexar documento/i })).toBeInTheDocument()
  })

  it('does NOT render the upload button when projectId is absent', () => {
    renderChatInput({ projectId: undefined })
    expect(screen.queryByRole('button', { name: /anexar documento/i })).not.toBeInTheDocument()
  })

  it('upload button is disabled when disabled=true', () => {
    renderChatInput({ disabled: true })
    const btn = screen.getByRole('button', { name: /anexar documento/i })
    expect(btn).toBeDisabled()
  })

  it('upload button is enabled when not disabled and not uploading', () => {
    renderChatInput()
    const btn = screen.getByRole('button', { name: /anexar documento/i })
    expect(btn).not.toBeDisabled()
  })

  // ── AC 3: Client-side validation ──

  it('shows inline error for files exceeding 10 MB', () => {
    renderChatInput()
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const bigFile = makeFile('huge.pdf', 11 * 1024 * 1024)

    fireEvent.change(input, { target: { files: [bigFile] } })

    expect(screen.getByRole('alert')).toHaveTextContent('10 MB')
    expect(mockUpload).not.toHaveBeenCalled()
  })

  it('shows inline error for unsupported extensions (.xlsx)', () => {
    renderChatInput()
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const xlsFile = makeFile('budget.xlsx', 1024, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    fireEvent.change(input, { target: { files: [xlsFile] } })

    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(mockUpload).not.toHaveBeenCalled()
  })

  it('shows inline error for unsupported extensions (.doc)', () => {
    renderChatInput()
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const docFile = makeFile('contract.doc', 1024, 'application/msword')

    fireEvent.change(input, { target: { files: [docFile] } })

    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(mockUpload).not.toHaveBeenCalled()
  })

  // ── AC 2: Successful upload ──

  it('calls uploadDocument with projectId and file on valid selection', async () => {
    mockUpload.mockResolvedValueOnce({ data: { id: 'doc-1', filename: 'spec.pdf' } })
    const { onUploadSuccess } = renderChatInput()

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const validFile = makeFile('spec.pdf', 1 * 1024 * 1024)

    fireEvent.change(input, { target: { files: [validFile] } })

    await waitFor(() => {
      expect(mockUpload).toHaveBeenCalledWith(PROJECT_ID, validFile)
    })
    expect(onUploadSuccess).toHaveBeenCalledWith('spec.pdf')
  })

  it('accepts .txt files as valid', async () => {
    mockUpload.mockResolvedValueOnce({ data: { id: 'doc-2', filename: 'notes.txt' } })
    const { onUploadSuccess } = renderChatInput()

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const txtFile = makeFile('notes.txt', 500 * 1024, 'text/plain')

    fireEvent.change(input, { target: { files: [txtFile] } })

    await waitFor(() => expect(onUploadSuccess).toHaveBeenCalledWith('notes.txt'))
  })

  // ── AC 4: API error ──

  it('shows inline error when uploadDocument throws', async () => {
    mockUpload.mockRejectedValueOnce(new Error('Network error'))
    renderChatInput()

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const validFile = makeFile('spec.pdf', 500 * 1024)

    fireEvent.change(input, { target: { files: [validFile] } })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Tente novamente')
    })
  })

  // ── AC 5: Uploading state disables buttons ──

  it('disables upload button during upload', async () => {
    // Never-resolving promise simulates ongoing upload
    mockUpload.mockReturnValueOnce(new Promise(() => {}))
    renderChatInput()

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const validFile = makeFile('spec.pdf', 500 * 1024)

    fireEvent.change(input, { target: { files: [validFile] } })

    const uploadBtn = screen.getByRole('button', { name: /anexar documento/i })
    await waitFor(() => expect(uploadBtn).toBeDisabled())
  })

  it('disables send button and textarea during upload (AC 5 full)', async () => {
    // Never-resolving promise simulates ongoing upload
    mockUpload.mockReturnValueOnce(new Promise(() => {}))
    renderChatInput()

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const validFile = makeFile('spec.pdf', 500 * 1024)

    fireEvent.change(input, { target: { files: [validFile] } })

    const sendBtn = screen.getByRole('button', { name: /enviar mensagem/i })
    const textarea = screen.getByRole('textbox')
    await waitFor(() => {
      expect(sendBtn).toBeDisabled()
      expect(textarea).toBeDisabled()
    })
  })

  // ── Error auto-clear on typing ──

  it('clears upload error when user types in textarea', async () => {
    renderChatInput()
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const bigFile = makeFile('huge.pdf', 11 * 1024 * 1024)

    fireEvent.change(input, { target: { files: [bigFile] } })
    expect(screen.getByRole('alert')).toBeInTheDocument()

    const textarea = screen.getByRole('textbox')
    await userEvent.type(textarea, 'h')

    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
