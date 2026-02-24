import { motion } from 'framer-motion'
import { AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface Holding {
  ticker: string
  market_value: number
  portfolio_weight: number
  unrealized_gain_loss: number
  sector: string
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
      <div className="p-4 border-b border-border-subtle flex items-center justify-between">
        <div>
          <h3 className="font-medium text-text-primary">{portfolio.name}</h3>
          <p className="text-sm text-text-muted">
            AUM: ${(portfolio.aum_usd / 1_000_000).toFixed(1)}M
          </p>
        </div>
        <span className="text-xs text-text-muted">
          Concentration Limit: {(portfolio.concentration_limit * 100).toFixed(0)}%
        </span>
      </div>

      {/* Holdings Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border-subtle">
              <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">
                Ticker
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">
                Sector
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-text-muted uppercase tracking-wider">
                Market Value
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-text-muted uppercase tracking-wider">
                Weight
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-text-muted uppercase tracking-wider">
                P&L
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-text-muted uppercase tracking-wider">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle">
            {portfolio.holdings.map((holding, index) => {
              const isOverConcentrated = holding.portfolio_weight > portfolio.concentration_limit
              const plPercent = (holding.unrealized_gain_loss / (holding.market_value - holding.unrealized_gain_loss)) * 100

              return (
                <motion.tr
                  key={holding.ticker}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`${isOverConcentrated ? 'bg-warning/5' : ''} hover:bg-bg-tertiary transition-colors`}
                >
                  <td className="px-4 py-3">
                    <span className="font-mono font-medium text-text-primary">
                      {holding.ticker}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-text-secondary">{holding.sector}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="font-mono text-text-primary">
                      ${(holding.market_value / 1_000_000).toFixed(2)}M
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 h-1.5 bg-bg-tertiary rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            isOverConcentrated ? 'bg-warning' : 'bg-accent'
                          }`}
                          style={{ width: `${Math.min(holding.portfolio_weight * 100, 100)}%` }}
                        />
                      </div>
                      <span className={`font-mono text-sm ${isOverConcentrated ? 'text-warning' : 'text-text-primary'}`}>
                        {(holding.portfolio_weight * 100).toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      {holding.unrealized_gain_loss > 0 ? (
                        <TrendingUp className="w-3 h-3 text-success" />
                      ) : holding.unrealized_gain_loss < 0 ? (
                        <TrendingDown className="w-3 h-3 text-error" />
                      ) : (
                        <Minus className="w-3 h-3 text-text-muted" />
                      )}
                      <span className={`font-mono text-sm ${
                        holding.unrealized_gain_loss > 0
                          ? 'text-success'
                          : holding.unrealized_gain_loss < 0
                          ? 'text-error'
                          : 'text-text-muted'
                      }`}>
                        {holding.unrealized_gain_loss >= 0 ? '+' : ''}
                        {plPercent.toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {isOverConcentrated ? (
                      <span className="badge-warning">
                        <AlertTriangle className="w-3 h-3" />
                        Over Limit
                      </span>
                    ) : (
                      <span className="badge-success">OK</span>
                    )}
                  </td>
                </motion.tr>
              )
            })}
          </tbody>
        </table>
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
