import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Send, Sparkles } from 'lucide-react'
import { useChatStore } from '../stores/chatStore'

interface ChatPanelProps {
  isOpen: boolean
  onClose: () => void
}

const suggestions = [
  "Why is NVDA flagged as a concentration risk?",
  "Explain the wash sale conflict",
  "What are my tax-loss harvesting opportunities?",
  "Compare the top two scenarios for me",
]

export default function ChatPanel({ isOpen, onClose }: ChatPanelProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const { messages, isLoading, sendMessage } = useChatStore()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus()
    }
  }, [isOpen])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const message = input.trim()
    setInput('')
    await sendMessage(message)
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion)
    inputRef.current?.focus()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.aside
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="fixed right-0 top-0 bottom-0 w-[420px] bg-bg-secondary border-l border-border-subtle flex flex-col z-50"
        >
          {/* Header */}
          <div className="h-16 flex items-center justify-between px-4 border-b border-border-subtle">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-accent" />
              <span className="font-medium">Sentinel AI</span>
            </div>
            <button
              onClick={onClose}
              className="btn-ghost p-2"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center py-8">
                <div className="w-12 h-12 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center mx-auto mb-4">
                  <Sparkles className="w-6 h-6 text-accent" />
                </div>
                <p className="text-text-secondary text-sm mb-6">
                  Ask me about your portfolio, risks, or recommendations.
                </p>
                <div className="space-y-2">
                  {suggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="w-full text-left px-3 py-2 text-sm text-text-secondary bg-bg-tertiary rounded-md hover:bg-bg-elevated hover:text-text-primary transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`${
                    message.role === 'user'
                      ? 'chat-bubble-user'
                      : 'chat-bubble-assistant'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                </motion.div>
              ))
            )}

            {isLoading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="chat-bubble-assistant"
              >
                <div className="flex items-center gap-2">
                  <span className="terminal-cursor" />
                  <span className="text-sm text-text-muted">Thinking...</span>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form
            onSubmit={handleSubmit}
            className="p-4 border-t border-border-subtle"
          >
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask Sentinel..."
                disabled={isLoading}
                className="input flex-1"
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="btn-primary p-2"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>
        </motion.aside>
      )}
    </AnimatePresence>
  )
}
