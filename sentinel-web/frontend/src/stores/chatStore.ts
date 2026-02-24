import { create } from 'zustand'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface ChatState {
  messages: Message[]
  isLoading: boolean
  error: string | null

  addMessage: (message: Message) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearMessages: () => void
  sendMessage: (content: string) => Promise<void>
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  error: null,

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),

  clearMessages: () => set({ messages: [] }),

  sendMessage: async (content: string) => {
    const { addMessage, setLoading, setError, messages } = get()

    // Add user message
    addMessage({ role: 'user', content })
    setLoading(true)
    setError(null)

    try {
      // Build history from existing messages (last 10)
      const history = messages.slice(-10).map((m) => ({
        role: m.role,
        content: m.content,
      }))

      const response = await fetch(`${API_URL}/api/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          history,
          portfolio_id: 'portfolio_a',
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
}))
