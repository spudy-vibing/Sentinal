import { useMemo } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'

interface Holding {
    ticker: string
    market_value: number
    portfolio_weight: number
}

interface AssetAllocationChartProps {
    holdings: Holding[]
}

const COLORS = [
    '#1E40AF', // accent (Navy)
    '#3B82F6', // accent-light (Blue)
    '#0284C7', // info (Light Blue)
    '#059669', // success (Green)
    '#D97706', // warning (Amber)
    '#DC2626', // error (Red)
    '#475569', // text-secondary (Slate)
    '#94A3B8', // text-muted (Light Slate)
]

export default function AssetAllocationChart({ holdings }: AssetAllocationChartProps) {
    const data = useMemo(() => {
        // Sort by weight descending
        const sorted = [...holdings].sort((a, b) => b.portfolio_weight - a.portfolio_weight)

        // Group small holdings into "Other" to avoid cluttered charts
        const threshold = 0.02 // 2%
        let otherWeight = 0
        let otherValue = 0
        const processedData: any[] = []

        sorted.forEach((h) => {
            if (h.portfolio_weight < threshold && sorted.length > 5) {
                otherWeight += h.portfolio_weight
                otherValue += h.market_value
            } else {
                processedData.push({
                    name: h.ticker,
                    value: h.market_value,
                    weight: h.portfolio_weight * 100 // Convert to percentage for display
                })
            }
        })

        if (otherWeight > 0) {
            processedData.push({
                name: 'Other',
                value: otherValue,
                weight: otherWeight * 100
            })
        }

        return processedData
    }, [holdings])

    const formatTooltip = (value: number, name: string, props: any) => {
        return [
            `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
            `${name} (${props.payload.weight.toFixed(1)}%)`
        ]
    }

    if (data.length === 0) return null

    return (
        <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                    <Tooltip
                        formatter={formatTooltip as any}
                        contentStyle={{
                            backgroundColor: 'var(--bg-elevated)',
                            borderColor: 'var(--border-subtle)',
                            borderRadius: '8px',
                            fontFamily: 'Inter, sans-serif',
                            fontSize: '12px',
                            boxShadow: 'var(--shadow-md)'
                        }}
                        itemStyle={{ color: 'var(--text-primary)' }}
                    />
                    <Legend
                        verticalAlign="middle"
                        align="right"
                        layout="vertical"
                        iconType="circle"
                        wrapperStyle={{
                            fontFamily: 'Inter, sans-serif',
                            fontSize: '12px',
                            color: 'var(--text-secondary)'
                        }}
                    />
                    <Pie
                        data={data}
                        cx="40%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                    >
                        {data.map((_entry, index) => (
                            <Cell
                                key={`cell-${index}`}
                                fill={COLORS[index % COLORS.length]}
                                stroke="var(--bg-secondary)"
                                strokeWidth={2}
                            />
                        ))}
                    </Pie>
                </PieChart>
            </ResponsiveContainer>
        </div>
    )
}
