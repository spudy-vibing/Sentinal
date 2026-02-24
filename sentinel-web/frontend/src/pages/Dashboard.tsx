import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Activity,
  DollarSign,
  PieChart,
  Wifi,
  WifiOff,
  Briefcase,
} from 'lucide-react'
import ProgressTimeline from '../components/ProgressTimeline'
import ActiveAgentDisplay from '../components/ActiveAgentDisplay'
import EventInjector from '../components/EventInjector'
import PortfolioMetrics from '../components/PortfolioMetrics'
import ScenarioPreview from '../components/ScenarioPreview'
import DebateDisplay from '../components/DebateDisplay'
import { useActivityStore } from '../stores/activityStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Portfolio {
  portfolio_id: string
  name: string
  aum_usd: number
  holdings: Array<{
    ticker: string
    market_value: number
    portfolio_weight: number
    unrealized_gain_loss: number
  }>
  concentration_limit: number
}

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const { isConnected, activeAgents, selectedPortfolioId } = useActivityStore()

  useEffect(() => {
    if (selectedPortfolioId) {
      fetchPortfolio(selectedPortfolioId)
    } else {
      setPortfolio(null)
    }
  }, [selectedPortfolioId])

  const fetchPortfolio = async (portfolioId: string) => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/portfolios/${portfolioId}`)
      if (response.ok) {
        const data = await response.json()
        setPortfolio(data)
      }
    } catch (err) {
      console.error('Failed to fetch portfolio:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const concentrationRisks = portfolio?.holdings.filter(
    (h) => h.portfolio_weight > (portfolio?.concentration_limit || 0.15)
  ) || []

  // Show portfolio selection prompt if no portfolio selected
  if (!selectedPortfolioId) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-md"
        >
          <div className="w-16 h-16 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center mx-auto mb-6">
            <Briefcase className="w-8 h-8 text-accent" />
          </div>
          <h2 className="text-xl font-semibold text-text-primary mb-2">
            Select a Portfolio
          </h2>
          <p className="text-text-secondary mb-6">
            Choose a portfolio from the dropdown above to view holdings, run analysis, and get AI-powered recommendations.
          </p>
          <div className="flex items-center justify-center gap-2 text-sm text-text-muted">
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
            Waiting for portfolio selection...
          </div>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Portfolio Intelligence</h1>
          <p className="text-sm text-text-secondary mt-1">
            Multi-agent analysis and recommendations
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* Connection Status */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
            isConnected
              ? 'bg-success-light text-success'
              : 'bg-error-light text-error'
          }`}>
            {isConnected ? (
              <>
                <Wifi className="w-3.5 h-3.5" />
                Connected
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5" />
                Disconnected
              </>
            )}
          </div>
          <EventInjector />
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          icon={DollarSign}
          label="Total AUM"
          value={portfolio ? `$${(portfolio.aum_usd / 1_000_000).toFixed(1)}M` : '--'}
          trend={null}
        />
        <MetricCard
          icon={PieChart}
          label="Holdings"
          value={portfolio?.holdings.length.toString() || '--'}
          trend={null}
        />
        <MetricCard
          icon={AlertTriangle}
          label="Concentration Risks"
          value={concentrationRisks.length.toString()}
          trend={concentrationRisks.length > 0 ? 'warning' : 'success'}
        />
        <MetricCard
          icon={Activity}
          label="Active Agents"
          value={activeAgents.length.toString()}
          trend={activeAgents.length > 0 ? 'up' : null}
        />
      </div>

      {/* Active Agent Display - Prominent when agents are thinking */}
      <ActiveAgentDisplay />

      {/* Debate Display - Shows when agents are debating */}
      <DebateDisplay />

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-12 gap-6">
        {/* Left Column - Portfolio & Scenarios */}
        <div className="col-span-8 space-y-6">
          <PortfolioMetrics portfolio={portfolio} isLoading={isLoading} />
          <ScenarioPreview />
        </div>

        {/* Right Column - Progress Timeline */}
        <div className="col-span-4">
          <div className="sticky top-6">
            <ProgressTimeline />
          </div>
        </div>
      </div>
    </div>
  )
}

interface MetricCardProps {
  icon: React.ElementType
  label: string
  value: string
  trend: 'up' | 'down' | 'warning' | 'success' | null
}

function MetricCard({ icon: Icon, label, value, trend }: MetricCardProps) {
  const getTrendColor = () => {
    switch (trend) {
      case 'up':
      case 'success':
        return 'text-success'
      case 'down':
        return 'text-error'
      case 'warning':
        return 'text-warning'
      default:
        return 'text-accent'
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="metric-card"
    >
      <div className="flex items-center justify-between mb-2">
        <Icon className={`w-5 h-5 ${getTrendColor()}`} />
        {trend === 'up' && <TrendingUp className="w-4 h-4 text-success" />}
        {trend === 'down' && <TrendingDown className="w-4 h-4 text-error" />}
      </div>
      <div className="metric-value">{value}</div>
      <div className="metric-label">{label}</div>
    </motion.div>
  )
}
