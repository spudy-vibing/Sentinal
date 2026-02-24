import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, Briefcase, Check, AlertCircle, FolderOpen } from 'lucide-react'
import { useActivityStore } from '../stores/activityStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface PortfolioSummary {
  portfolio_id: string
  name: string
  aum_usd: number
  holdings_count: number
  top_holding: string
  top_holding_weight: number
}

interface PortfolioSelectorProps {
  value: string | null
  onChange: (portfolioId: string | null) => void
}

export default function PortfolioSelector({ value, onChange }: PortfolioSelectorProps) {
  const { portfolioSelectorOpen, setPortfolioSelectorOpen } = useActivityStore()
  const [portfolios, setPortfolios] = useState<PortfolioSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [highlightedIndex, setHighlightedIndex] = useState(-1)

  const buttonRef = useRef<HTMLButtonElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const itemRefs = useRef<(HTMLButtonElement | null)[]>([])
  const listboxId = 'portfolio-listbox'

  useEffect(() => {
    fetchPortfolios()
  }, [])

  // Sync highlighted index when dropdown opens
  useEffect(() => {
    if (portfolioSelectorOpen) {
      const selectedIndex = portfolios.findIndex((p) => p.portfolio_id === value)
      setHighlightedIndex(selectedIndex >= 0 ? selectedIndex : 0)
    }
  }, [portfolioSelectorOpen, portfolios, value])

  // Focus management when dropdown opens
  useEffect(() => {
    if (portfolioSelectorOpen && itemRefs.current[highlightedIndex]) {
      itemRefs.current[highlightedIndex]?.focus()
    }
  }, [portfolioSelectorOpen, highlightedIndex])

  const fetchPortfolios = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_URL}/api/portfolios/`)
      if (!response.ok) {
        throw new Error(`Failed to fetch portfolios (${response.status})`)
      }
      const data = await response.json()
      setPortfolios(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load portfolios'
      setError(message)
      console.error('Failed to fetch portfolios:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleClose = useCallback(() => {
    setPortfolioSelectorOpen(false)
    setHighlightedIndex(-1)
    buttonRef.current?.focus()
  }, [setPortfolioSelectorOpen])

  const handleSelect = useCallback((portfolioId: string) => {
    onChange(portfolioId)
    handleClose()
  }, [onChange, handleClose])

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (!portfolioSelectorOpen) {
      // Open dropdown on arrow down or enter when closed
      if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
        event.preventDefault()
        setPortfolioSelectorOpen(true)
      }
      return
    }

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault()
        setHighlightedIndex((prev) =>
          prev < portfolios.length - 1 ? prev + 1 : 0
        )
        break
      case 'ArrowUp':
        event.preventDefault()
        setHighlightedIndex((prev) =>
          prev > 0 ? prev - 1 : portfolios.length - 1
        )
        break
      case 'Enter':
      case ' ':
        event.preventDefault()
        if (highlightedIndex >= 0 && portfolios[highlightedIndex]) {
          handleSelect(portfolios[highlightedIndex].portfolio_id)
        }
        break
      case 'Escape':
        event.preventDefault()
        handleClose()
        break
      case 'Tab':
        // Allow tab to close dropdown and move focus
        handleClose()
        break
      case 'Home':
        event.preventDefault()
        setHighlightedIndex(0)
        break
      case 'End':
        event.preventDefault()
        setHighlightedIndex(portfolios.length - 1)
        break
      default:
        // Type-ahead: jump to first matching portfolio
        if (event.key.length === 1 && /[a-zA-Z]/.test(event.key)) {
          const char = event.key.toLowerCase()
          const matchIndex = portfolios.findIndex(
            (p) => p.name.toLowerCase().startsWith(char)
          )
          if (matchIndex >= 0) {
            setHighlightedIndex(matchIndex)
          }
        }
        break
    }
  }, [portfolioSelectorOpen, portfolios, highlightedIndex, handleSelect, handleClose, setPortfolioSelectorOpen])

  // Scroll highlighted item into view
  useEffect(() => {
    if (highlightedIndex >= 0 && itemRefs.current[highlightedIndex]) {
      itemRefs.current[highlightedIndex]?.scrollIntoView({
        block: 'nearest',
        behavior: 'smooth'
      })
    }
  }, [highlightedIndex])

  const selectedPortfolio = portfolios.find((p) => p.portfolio_id === value)

  // Loading skeleton
  const LoadingSkeleton = () => (
    <div className="space-y-2 p-2">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-center gap-3 px-4 py-3 animate-pulse">
          <div className="w-8 h-8 rounded-lg bg-bg-tertiary" />
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-bg-tertiary rounded w-3/4" />
            <div className="h-3 bg-bg-tertiary rounded w-1/2" />
          </div>
        </div>
      ))}
    </div>
  )

  // Error state
  const ErrorState = () => (
    <div className="p-6 text-center">
      <div className="w-12 h-12 rounded-full bg-error-light flex items-center justify-center mx-auto mb-3">
        <AlertCircle className="w-6 h-6 text-error" />
      </div>
      <p className="text-sm font-medium text-text-primary mb-1">Failed to load portfolios</p>
      <p className="text-xs text-text-muted mb-3">{error}</p>
      <button
        onClick={fetchPortfolios}
        className="text-xs text-accent hover:text-accent-light font-medium"
      >
        Try again
      </button>
    </div>
  )

  // Empty state
  const EmptyState = () => (
    <div className="p-6 text-center">
      <div className="w-12 h-12 rounded-full bg-bg-tertiary flex items-center justify-center mx-auto mb-3">
        <FolderOpen className="w-6 h-6 text-text-muted" />
      </div>
      <p className="text-sm font-medium text-text-primary mb-1">No portfolios available</p>
      <p className="text-xs text-text-muted">Create a portfolio to get started</p>
    </div>
  )

  return (
    <div className="relative" onKeyDown={handleKeyDown}>
      <button
        ref={buttonRef}
        onClick={() => setPortfolioSelectorOpen(!portfolioSelectorOpen)}
        aria-haspopup="listbox"
        aria-expanded={portfolioSelectorOpen}
        aria-controls={listboxId}
        aria-label={selectedPortfolio ? `Selected portfolio: ${selectedPortfolio.name}` : 'Select a portfolio'}
        className="flex items-center gap-3 px-3 py-2 rounded-lg bg-bg-tertiary border border-border-subtle hover:border-border-default transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-bg-secondary"
      >
        <div className="w-8 h-8 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center">
          <Briefcase className="w-4 h-4 text-accent" />
        </div>
        <div className="text-left min-w-[140px]">
          {isLoading ? (
            <div className="space-y-1">
              <div className="h-4 bg-bg-tertiary rounded w-24 animate-pulse" />
              <div className="h-3 bg-bg-tertiary rounded w-16 animate-pulse" />
            </div>
          ) : error ? (
            <p className="text-sm font-medium text-error">Error loading</p>
          ) : (
            <>
              <p className="text-sm font-medium text-text-primary">
                {selectedPortfolio?.name || 'Select Portfolio'}
              </p>
              {selectedPortfolio && (
                <p className="text-xs text-text-muted">
                  ${(selectedPortfolio.aum_usd / 1_000_000).toFixed(1)}M AUM
                </p>
              )}
            </>
          )}
        </div>
        <ChevronDown
          className={`w-4 h-4 text-text-muted transition-transform duration-200 ${
            portfolioSelectorOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      <AnimatePresence>
        {portfolioSelectorOpen && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 z-40"
              onClick={handleClose}
              aria-hidden="true"
            />

            {/* Dropdown */}
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="absolute left-0 top-full mt-2 w-80 bg-bg-elevated border border-border-subtle rounded-lg shadow-card-hover z-50 overflow-hidden"
              role="dialog"
              aria-modal="true"
              aria-label="Select portfolio"
            >
              <div className="p-2 border-b border-border-subtle">
                <p className="px-2 py-1 text-xs text-text-muted uppercase tracking-wider font-medium">
                  Available Portfolios
                </p>
              </div>

              {isLoading ? (
                <LoadingSkeleton />
              ) : error ? (
                <ErrorState />
              ) : portfolios.length === 0 ? (
                <EmptyState />
              ) : (
                <div
                  ref={listRef}
                  id={listboxId}
                  role="listbox"
                  aria-label="Portfolios"
                  aria-activedescendant={
                    highlightedIndex >= 0
                      ? `portfolio-option-${portfolios[highlightedIndex]?.portfolio_id}`
                      : undefined
                  }
                  className="max-h-64 overflow-y-auto"
                >
                  {portfolios.map((portfolio, index) => {
                    const isSelected = value === portfolio.portfolio_id
                    const isHighlighted = index === highlightedIndex

                    return (
                      <button
                        key={portfolio.portfolio_id}
                        ref={(el) => (itemRefs.current[index] = el)}
                        id={`portfolio-option-${portfolio.portfolio_id}`}
                        role="option"
                        aria-selected={isSelected}
                        onClick={() => handleSelect(portfolio.portfolio_id)}
                        onMouseEnter={() => setHighlightedIndex(index)}
                        className={`w-full flex items-center gap-3 px-4 py-3 transition-colors outline-none ${
                          isHighlighted
                            ? 'bg-accent/10'
                            : isSelected
                            ? 'bg-accent/5'
                            : 'hover:bg-bg-tertiary'
                        }`}
                      >
                        <div
                          className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
                            isSelected
                              ? 'bg-accent/20 border border-accent/30'
                              : 'bg-bg-tertiary border border-border-subtle'
                          }`}
                        >
                          <Briefcase
                            className={`w-4 h-4 ${
                              isSelected ? 'text-accent' : 'text-text-muted'
                            }`}
                          />
                        </div>

                        <div className="flex-1 text-left min-w-0">
                          <p className="text-sm font-medium text-text-primary truncate">
                            {portfolio.name}
                          </p>
                          <p className="text-xs text-text-muted">
                            ${(portfolio.aum_usd / 1_000_000).toFixed(1)}M •{' '}
                            {portfolio.holdings_count} holdings
                          </p>
                        </div>

                        {isSelected && (
                          <Check className="w-4 h-4 text-accent flex-shrink-0" />
                        )}
                      </button>
                    )
                  })}
                </div>
              )}

              <div className="p-2 border-t border-border-subtle bg-bg-tertiary/50">
                <p className="px-2 py-1 text-xs text-text-muted flex items-center gap-2">
                  <kbd className="px-1.5 py-0.5 text-[10px] bg-bg-secondary border border-border-subtle rounded font-mono">
                    ⌘⇧P
                  </kbd>
                  <span>to quick switch</span>
                  <span className="mx-1">•</span>
                  <kbd className="px-1.5 py-0.5 text-[10px] bg-bg-secondary border border-border-subtle rounded font-mono">
                    ↑↓
                  </kbd>
                  <span>navigate</span>
                </p>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
