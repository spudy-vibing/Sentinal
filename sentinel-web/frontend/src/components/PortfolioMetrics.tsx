import { PieChart } from 'lucide-react'
import AssetAllocationChart from './charts/AssetAllocationChart'
import HoldingsTable from './tables/HoldingsTable'

interface Holding {
  ticker: string
  market_value: number
  portfolio_weight: number
  unrealized_gain_loss: number
  sector?: string
}

interface Portfolio {
  portfolio_id: string
  name: string
  aum_usd: number
  holdings: Holding[]
  concentration_limit: number
}

interface PortfolioMetricsProps {
  portfolio: Portfolio | null
  isLoading: boolean
}

export default function PortfolioMetrics({ portfolio, isLoading }: PortfolioMetricsProps) {
  if (isLoading) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-center py-12">
          <div className="terminal-cursor" />
          <span className="ml-3 text-text-muted">Loading portfolio...</span>
        </div>
      </div>
    )
  }

  if (!portfolio) {
    return (
      <div className="card p-6">
        <div className="text-center py-12">
          <p className="text-text-muted">No portfolio data available</p>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="p-5 border-b border-border-subtle flex flex-col md:flex-row gap-6">
        <div className="flex-1 w-full flex flex-col justify-between">
          <div>
            <h3 className="font-medium text-text-primary text-lg">{portfolio.name}</h3>
            <p className="text-text-muted mt-1">
              AUM: ${(portfolio.aum_usd / 1_000_000).toFixed(1)}M
            </p>
          </div>
          <div className="mt-4">
            <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-bg-tertiary text-text-secondary border border-border-subtle">
              Concentration Limit: {(portfolio.concentration_limit * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        <div className="w-full md:w-2/3 lg:w-1/2">
          <div className="bg-bg-tertiary/30 rounded-lg border border-border-subtle p-3">
            <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2 flex items-center gap-2">
              <PieChart className="w-3.5 h-3.5 text-accent" />
              Asset Allocation
            </h4>
            <AssetAllocationChart holdings={portfolio.holdings} />
          </div>
        </div>
      </div>

      <div className="p-4">
        <HoldingsTable holdings={portfolio.holdings} concentrationLimit={portfolio.concentration_limit} />
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-border-subtle bg-bg-tertiary/50">
        <div className="flex items-center justify-between text-sm">
          <span className="text-text-muted">
            {portfolio.holdings.filter(h => h.portfolio_weight > portfolio.concentration_limit).length} positions over concentration limit
          </span>
          <span className="text-text-muted">
            Total: {portfolio.holdings.length} holdings
          </span>
        </div>
      </div>
    </div>
  )
}
