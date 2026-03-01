import { create } from 'zustand'
import { useActivityStore } from './activityStore'

interface Message {
  role: 'user' | 'assistant'
  content: string
  isStreaming?: boolean
}

interface ChatState {
  messages: Message[]
  isLoading: boolean
  error: string | null
  streamingContent: string

  addMessage: (message: Message) => void
  updateLastMessage: (content: string) => void
  finalizeLastMessage: () => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearMessages: () => void
  sendMessage: (content: string) => Promise<void>
  sendMessageStreaming: (content: string) => Promise<void>
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  error: null,
  streamingContent: '',

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  updateLastMessage: (content) =>
    set((state) => {
      const messages = [...state.messages]
      if (messages.length > 0 && messages[messages.length - 1].role === 'assistant') {
        messages[messages.length - 1] = {
          ...messages[messages.length - 1],
          content,
        }
      }
      return { messages, streamingContent: content }
    }),

  finalizeLastMessage: () =>
    set((state) => {
      const messages = [...state.messages]
      if (messages.length > 0) {
        messages[messages.length - 1] = {
          ...messages[messages.length - 1],
          isStreaming: false,
        }
      }
      return { messages, streamingContent: '' }
    }),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),

  clearMessages: () => set({ messages: [], streamingContent: '' }),

  // Non-streaming version (fallback)
  sendMessage: async (content: string) => {
    const { addMessage, setLoading, setError, messages } = get()
    const portfolioId = useActivityStore.getState().selectedPortfolioId

    addMessage({ role: 'user', content })
    setLoading(true)
    setError(null)

    try {
      const history = messages.slice(-10).map((m) => ({
        role: m.role,
        content: m.content,
      }))

      const response = await fetch(`${API_URL}/api/chat/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          history,
          portfolio_id: portfolioId || 'portfolio_a',
          include_context: true,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      addMessage({ role: 'assistant', content: data.response })
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message'
      setError(errorMessage)
      addMessage({
        role: 'assistant',
        content: `I'm sorry, I encountered an error: ${errorMessage}. Please try again.`,
      })
    } finally {
      setLoading(false)
    }
  },

  // Streaming version (preferred)
  sendMessageStreaming: async (content: string) => {
    const { addMessage, updateLastMessage, finalizeLastMessage, setLoading, setError, messages } = get()
    const portfolioId = useActivityStore.getState().selectedPortfolioId

    addMessage({ role: 'user', content })
    addMessage({ role: 'assistant', content: '', isStreaming: true })
    setLoading(true)
    setError(null)

    let fullContent = ''

    try {
      const history = messages.slice(-10).map((m) => ({
        role: m.role,
        content: m.content,
      }))

      const response = await fetch(`${API_URL}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          history,
          portfolio_id: portfolioId || 'portfolio_a',
          include_context: true,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.text) {
                fullContent += data.text
                updateLastMessage(fullContent)
              }
              if (data.done) {
                finalizeLastMessage()
              }
            } catch {
              // Ignore JSON parse errors for incomplete chunks
            }
          }
        }
      }

      finalizeLastMessage()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message'
      setError(errorMessage)
      updateLastMessage(`I'm sorry, I encountered an error: ${errorMessage}. Please try again.`)
      finalizeLastMessage()
    } finally {
      setLoading(false)
    }
  },
}))
