import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Zap, TrendingDown, TrendingUp, Building, ChevronDown, Play, X } from 'lucide-react'
import { useActivityStore } from '../stores/activityStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Access clearActivities from store

const eventPresets = [
  {
    id: 'tech_crash',
    name: 'Tech Sector Crash',
    description: 'NVDA drops 4%, triggering concentration and risk alerts',
    icon: TrendingDown,
    color: 'text-error',
    bgColor: 'bg-error/10',
    magnitude: -0.04,
  },
  {
    id: 'earnings_beat',
    name: 'Earnings Beat',
    description: 'NVDA beats earnings by 8%, stock surges',
    icon: TrendingUp,
    color: 'text-success',
    bgColor: 'bg-success/10',
    magnitude: 0.08,
  },
  {
    id: 'fed_rate',
    name: 'Fed Rate Decision',
    description: 'Interest rates concern, bond values shift',
    icon: Building,
    color: 'text-info',
    bgColor: 'bg-info/10',
    magnitude: -0.02,
  },
]

export default function EventInjector() {
  const [isOpen, setIsOpen] = useState(false)
  const [isInjecting, setIsInjecting] = useState(false)
  const [selectedEvent, setSelectedEvent] = useState<string | null>(null)
  const { selectedPortfolioId, clearActivities } = useActivityStore()

  const handleInject = async (eventId: string) => {
    if (!selectedPortfolioId) return

    setIsInjecting(true)
    setSelectedEvent(eventId)

    const preset = eventPresets.find((e) => e.id === eventId)
    if (!preset) return

    // Clear previous analysis state
    clearActivities()

    try {
      const response = await fetch(`${API_URL}/api/events/inject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_type: preset.id,
          portfolio_id: selectedPortfolioId,
          magnitude: preset.magnitude,
          enable_debate: true,
          enable_thinking: true,
          enable_chain_reaction: true,
        }),
      })

      if (response.ok) {
        setIsOpen(false)
      }
    } catch (err) {
      console.error('Failed to inject event:', err)
    } finally {
      setIsInjecting(false)
      setSelectedEvent(null)
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => selectedPortfolioId && setIsOpen(!isOpen)}
        disabled={!selectedPortfolioId}
        className="btn-primary"
        title={!selectedPortfolioId ? 'Select a portfolio first' : 'Inject market event'}
      >
        <Zap className="w-4 h-4" />
        Inject Event
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />

            {/* Dropdown */}
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              className="absolute right-0 top-full mt-2 w-80 bg-bg-elevated border border-border-subtle rounded-lg shadow-card-hover z-50"
            >
              <div className="p-4 border-b border-border-subtle">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-text-primary">Market Event Simulator</h3>
                  <button onClick={() => setIsOpen(false)} className="btn-ghost p-1">
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-xs text-text-muted mt-1">
                  Inject events to see real-time agent response
                </p>
              </div>

              <div className="p-2 space-y-2">
                {eventPresets.map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() => handleInject(preset.id)}
                    disabled={isInjecting}
                    className={`w-full text-left p-3 rounded-md transition-colors ${
                      isInjecting && selectedEvent === preset.id
                        ? 'bg-accent/10 border border-accent/30'
                        : 'hover:bg-bg-tertiary'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-md ${preset.bgColor}`}>
                        <preset.icon className={`w-4 h-4 ${preset.color}`} />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-text-primary text-sm">
                            {preset.name}
                          </span>
                          {isInjecting && selectedEvent === preset.id ? (
                            <span className="terminal-cursor" />
                          ) : (
                            <Play className="w-3 h-3 text-text-muted" />
                          )}
                        </div>
                        <p className="text-xs text-text-muted mt-0.5">
                          {preset.description}
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              <div className="p-3 border-t border-border-subtle">
                <p className="text-xs text-text-muted text-center">
                  Events trigger real agent analysis via WebSocket
                </p>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
