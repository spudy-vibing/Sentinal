import { useMemo } from 'react'
import {
    Radar,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    ResponsiveContainer,
    Tooltip,
} from 'recharts'

interface ScenarioMetrics {
    risk_reduction: number
    tax_savings: number
    goal_alignment: number
    transaction_cost: number
    urgency: number
}

interface RiskRadarChartProps {
    metrics: ScenarioMetrics
}

export default function RiskRadarChart({ metrics }: RiskRadarChartProps) {
    const data = useMemo(() => {
        return [
            { subject: 'Risk Reduction', A: metrics.risk_reduction, fullMark: 10 },
            { subject: 'Tax Savings', A: metrics.tax_savings, fullMark: 10 },
            { subject: 'Goal Alignment', A: metrics.goal_alignment, fullMark: 10 },
            { subject: 'Cost Efficiency', A: 10 - metrics.transaction_cost, fullMark: 10 }, // Inverted so higher is better
            { subject: 'Urgency', A: metrics.urgency, fullMark: 10 },
        ]
    }, [metrics])

    return (
        <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
                    <PolarGrid stroke="var(--border-subtle)" />
                    <PolarAngleAxis
                        dataKey="subject"
                        tick={{ fill: 'var(--text-secondary)', fontSize: 11, fontFamily: 'Inter' }}
                    />
                    <PolarRadiusAxis
                        angle={30}
                        domain={[0, 10]}
                        tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
                        axisLine={false}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: 'var(--bg-elevated)',
                            borderColor: 'var(--border-subtle)',
                            borderRadius: '8px',
                            fontFamily: 'Inter',
                            boxShadow: 'var(--shadow-md)',
                            fontSize: '12px'
                        }}
                        itemStyle={{ color: 'var(--accent)' }}
                        formatter={(value: number) => [value.toFixed(1), 'Score']}
                    />
                    <Radar
                        name="Scenario Score"
                        dataKey="A"
                        stroke="var(--accent)"
                        strokeWidth={2}
                        fill="var(--accent-glow)"
                        fillOpacity={0.6}
                        activeDot={{ r: 4, fill: 'var(--accent)', stroke: 'var(--bg-secondary)' }}
                    />
                </RadarChart>
            </ResponsiveContainer>
        </div>
    )
}
