import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Send, Sparkles, AlertTriangle, TrendingDown, Calculator, GitCompare, Loader2, Bot, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { useChatStore } from '../stores/chatStore'
import { useActivityStore } from '../stores/activityStore'

interface ChatPanelProps {
  isOpen: boolean
  onClose: () => void
}

const suggestions = [
  {
    text: "What's my concentration risk?",
    icon: AlertTriangle,
    color: "text-warning"
  },
  {
    text: "Explain the wash sale issue",
    icon: TrendingDown,
    color: "text-error"
  },
  {
    text: "Tax-loss harvesting opportunities?",
    icon: Calculator,
    color: "text-success"
  },
  {
    text: "Compare my scenarios",
    icon: GitCompare,
    color: "text-info"
  },
]

export default function ChatPanel({ isOpen, onClose }: ChatPanelProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const { selectedPortfolioId } = useActivityStore()

  const { messages, isLoading, sendMessageStreaming, clearMessages } = useChatStore()

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
    await sendMessageStreaming(message)
  }

  const handleSuggestionClick = async (suggestion: string) => {
    if (isLoading) return
    await sendMessageStreaming(suggestion)
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          {/* Panel */}
          <motion.aside
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 bottom-0 w-[480px] bg-bg-primary border-l border-border-subtle flex flex-col z-50 shadow-2xl"
          >
            {/* Header */}
            <div className="h-16 flex items-center justify-between px-5 border-b border-border-subtle bg-bg-secondary">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent to-accent-600 flex items-center justify-center shadow-lg">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  {isLoading && (
                    <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-success rounded-full border-2 border-bg-secondary animate-pulse" />
                  )}
                </div>
                <div>
                  <span className="font-semibold text-text-primary">Sentinel AI</span>
                  <p className="text-xs text-text-muted">
                    {isLoading ? (
                      <span className="text-accent">Thinking...</span>
                    ) : selectedPortfolioId ? (
                      `Portfolio: ${selectedPortfolioId.replace('_', ' ')}`
                    ) : (
                      'Ready to help'
                    )}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {messages.length > 0 && (
                  <button
                    onClick={clearMessages}
                    className="text-xs text-text-muted hover:text-text-primary px-2 py-1 rounded hover:bg-bg-tertiary transition-colors"
                  >
                    Clear
                  </button>
                )}
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg hover:bg-bg-tertiary transition-colors"
                >
                  <X className="w-5 h-5 text-text-muted" />
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto">
              {messages.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-6"
                >
                  <div className="text-center mb-8">
                    <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-accent/20 to-accent/5 border border-accent/20 flex items-center justify-center mx-auto mb-4">
                      <Sparkles className="w-10 h-10 text-accent" />
                    </div>
                    <h3 className="font-semibold text-text-primary text-lg mb-1">Ask Sentinel</h3>
                    <p className="text-text-secondary text-sm">
                      Get AI-powered insights about your portfolio
                    </p>
                  </div>

                  {/* Suggestions */}
                  <div className="space-y-2">
                    <p className="text-xs text-text-muted uppercase tracking-wider mb-3">Suggested Questions</p>
                    {suggestions.map((suggestion) => (
                      <button
                        key={suggestion.text}
                        onClick={() => handleSuggestionClick(suggestion.text)}
                        disabled={isLoading}
                        className="w-full flex items-center gap-3 px-4 py-3 text-sm text-left bg-bg-secondary rounded-xl hover:bg-bg-tertiary border border-transparent hover:border-border-default transition-all group disabled:opacity-50"
                      >
                        <div className={`p-2 rounded-lg bg-bg-tertiary ${suggestion.color} group-hover:scale-110 transition-transform`}>
                          <suggestion.icon className="w-4 h-4" />
                        </div>
                        <span className="text-text-secondary group-hover:text-text-primary">
                          {suggestion.text}
                        </span>
                      </button>
                    ))}
                  </div>
                </motion.div>
              ) : (
                <div className="p-4 space-y-4">
                  {messages.map((message, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                    >
                      {/* Avatar */}
                      <div className={`shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${
                        message.role === 'user'
                          ? 'bg-accent text-white'
                          : 'bg-bg-tertiary text-accent'
                      }`}>
                        {message.role === 'user' ? (
                          <User className="w-4 h-4" />
                        ) : (
                          <Bot className="w-4 h-4" />
                        )}
                      </div>

                      {/* Message Content */}
                      <div className={`flex-1 min-w-0 ${message.role === 'user' ? 'text-right' : ''}`}>
                        <div className={`inline-block max-w-full text-left rounded-2xl px-4 py-3 ${
                          message.role === 'user'
                            ? 'bg-accent text-white rounded-tr-md'
                            : 'bg-bg-secondary border border-border-subtle rounded-tl-md'
                        }`}>
                          {message.role === 'assistant' && message.isStreaming && !message.content ? (
                            <div className="flex items-center gap-2">
                              <Loader2 className="w-4 h-4 animate-spin text-accent" />
                              <span className="text-sm text-text-muted">Analyzing...</span>
                            </div>
                          ) : message.role === 'assistant' ? (
                            <div className="prose prose-sm prose-invert max-w-none">
                              <ReactMarkdown
                                components={{
                                  p: ({ children }) => <p className="text-sm text-text-primary mb-2 last:mb-0">{children}</p>,
                                  strong: ({ children }) => <strong className="font-semibold text-accent">{children}</strong>,
                                  ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-2">{children}</ul>,
                                  ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 mb-2">{children}</ol>,
                                  li: ({ children }) => <li className="text-sm text-text-secondary">{children}</li>,
                                  h1: ({ children }) => <h1 className="text-base font-semibold text-text-primary mb-2">{children}</h1>,
                                  h2: ({ children }) => <h2 className="text-sm font-semibold text-text-primary mb-2">{children}</h2>,
                                  h3: ({ children }) => <h3 className="text-sm font-medium text-text-primary mb-1">{children}</h3>,
                                  code: ({ children }) => <code className="px-1.5 py-0.5 bg-bg-tertiary rounded text-xs font-mono text-accent">{children}</code>,
                                  blockquote: ({ children }) => <blockquote className="border-l-2 border-accent pl-3 italic text-text-secondary">{children}</blockquote>,
                                }}
                              >
                                {message.content}
                              </ReactMarkdown>
                              {message.isStreaming && (
                                <span className="inline-block w-2 h-4 ml-0.5 bg-accent animate-pulse rounded-sm" />
                              )}
                            </div>
                          ) : (
                            <p className="text-sm">{message.content}</p>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}

                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>

            {/* Quick Actions */}
            {messages.length > 0 && !isLoading && (
              <div className="px-4 py-3 border-t border-border-subtle bg-bg-secondary/50">
                <div className="flex gap-2 overflow-x-auto scrollbar-hide">
                  <button
                    onClick={() => handleSuggestionClick("Tell me more about this")}
                    className="px-3 py-1.5 text-xs bg-bg-tertiary text-text-secondary rounded-full hover:bg-accent hover:text-white transition-colors whitespace-nowrap"
                  >
                    Tell me more
                  </button>
                  <button
                    onClick={() => handleSuggestionClick("What should I do next?")}
                    className="px-3 py-1.5 text-xs bg-bg-tertiary text-text-secondary rounded-full hover:bg-accent hover:text-white transition-colors whitespace-nowrap"
                  >
                    What next?
                  </button>
                  <button
                    onClick={() => handleSuggestionClick("Explain this simply for a client")}
                    className="px-3 py-1.5 text-xs bg-bg-tertiary text-text-secondary rounded-full hover:bg-accent hover:text-white transition-colors whitespace-nowrap"
                  >
                    Simplify for client
                  </button>
                  <button
                    onClick={() => handleSuggestionClick("Show me the numbers")}
                    className="px-3 py-1.5 text-xs bg-bg-tertiary text-text-secondary rounded-full hover:bg-accent hover:text-white transition-colors whitespace-nowrap"
                  >
                    Show numbers
                  </button>
                </div>
              </div>
            )}

            {/* Input */}
            <form
              onSubmit={handleSubmit}
              className="p-4 border-t border-border-subtle bg-bg-secondary"
            >
              <div className="flex items-center gap-3 bg-bg-tertiary rounded-xl px-4 py-2 border border-border-subtle focus-within:border-accent transition-colors">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={isLoading ? "Sentinel is thinking..." : "Ask anything about your portfolio..."}
                  disabled={isLoading}
                  className="flex-1 bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="p-2 rounded-lg bg-accent text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent-600 transition-colors"
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </button>
              </div>
              <p className="text-xs text-text-muted mt-2 text-center">
                Powered by Claude AI
              </p>
            </form>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}
