import { useMemo } from 'react'
import {
    createColumnHelper,
    flexRender,
    getCoreRowModel,
    getSortedRowModel,
    useReactTable,
} from '@tanstack/react-table'
import { ArrowUpDown } from 'lucide-react'

interface Holding {
    ticker: string
    market_value: number
    portfolio_weight: number
    unrealized_gain_loss: number
    sector?: string
}

interface HoldingsTableProps {
    holdings: Holding[]
    concentrationLimit: number
}

const columnHelper = createColumnHelper<Holding>()

// Simple SVG sparkline component
function Sparkline({ isPositive }: { isPositive: boolean }) {
    const colorClass = isPositive ? 'stroke-success fill-success/10' : 'stroke-error fill-error/10'
    const pathData = isPositive
        ? 'M0 30 L10 25 L20 28 L40 15 L60 20 L80 5 L100 0'
        : 'M0 0 L20 10 L40 8 L60 20 L80 15 L100 30'

    return (
        <svg className={`w-16 h-6 ${colorClass}`} viewBox="0 0 100 30" preserveAspectRatio="none">
            <path d={pathData} strokeWidth="2" vectorEffect="non-scaling-stroke" />
        </svg>
    )
}

export default function HoldingsTable({ holdings, concentrationLimit }: HoldingsTableProps) {
    const columns = useMemo(
        () => [
            columnHelper.accessor('ticker', {
                header: 'Asset',
                cell: (info) => (
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded bg-bg-secondary border border-border-default flex items-center justify-center font-bold text-xs">
                            {info.getValue()}
                        </div>
                        <div>
                            <div className="text-sm font-bold text-text-primary">{info.getValue()}</div>
                            <div className="text-xs text-text-muted">{info.row.original.sector}</div>
                        </div>
                    </div>
                ),
            }),
            columnHelper.accessor('market_value', {
                header: 'Market Value',
                cell: (info) => (
                    <div className="text-right font-mono text-sm">
                        ${(info.getValue() / 1_000_000).toFixed(2)}M
                    </div>
                ),
            }),
            columnHelper.display({
                id: 'trend',
                header: '7-Day Trend',
                cell: (info) => (
                    <div className="flex justify-end pr-4">
                        <Sparkline isPositive={info.row.original.unrealized_gain_loss >= 0} />
                    </div>
                ),
            }),
            columnHelper.accessor('portfolio_weight', {
                header: 'Weight',
                cell: (info) => {
                    const weight = info.getValue()
                    const isOverConcentrated = weight > concentrationLimit
                    const widthPercent = Math.min(weight * 100, 100)

                    return (
                        <div className="text-right flex flex-col items-end">
                            <div className={`font-mono text-sm font-bold mb-1 ${isOverConcentrated ? 'text-error' : 'text-text-primary'}`}>
                                {(weight * 100).toFixed(1)}%
                            </div>
                            <div className="h-1.5 w-24 bg-bg-tertiary rounded-full overflow-hidden flex">
                                <div
                                    className={`h-full ${isOverConcentrated ? 'bg-error animate-pulse' : 'bg-accent'}`}
                                    style={{ width: `${widthPercent}%` }}
                                />
                            </div>
                        </div>
                    )
                },
            }),
            columnHelper.accessor('unrealized_gain_loss', {
                header: 'Unrealized G/L',
                cell: (info) => {
                    const val = info.getValue()
                    const isPos = val > 0
                    const isNeg = val < 0
                    const plPercent = (val / (info.row.original.market_value - val)) * 100

                    return (
                        <div className="text-right flex flex-col items-end">
                            <span className={`font-mono text-sm ${isPos ? 'text-success' : isNeg ? 'text-error' : 'text-text-muted'}`}>
                                {isPos ? '+' : ''}{plPercent.toFixed(1)}%
                            </span>
                            <span className={`badge ${isPos ? 'badge-success' : isNeg ? 'badge-error' : 'bg-bg-tertiary text-text-muted'} mt-1 text-[10px] py-0.5 px-1.5`}>
                                ${Math.abs(val / 1000).toFixed(1)}k
                            </span>
                        </div>
                    )
                },
            }),
        ],
        [concentrationLimit]
    )

    const table = useReactTable({
        data: holdings,
        columns,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
    })

    return (
        <div className="w-full overflow-x-auto shadow-card rounded-lg border border-border-default">
            <table className="w-full text-left border-collapse">
                <thead className="bg-bg-tertiary/50">
                    {table.getHeaderGroups().map((headerGroup) => (
                        <tr key={headerGroup.id} className="border-b border-border-subtle">
                            {headerGroup.headers.map((header) => {
                                const isSorted = header.column.getIsSorted()
                                return (
                                    <th
                                        key={header.id}
                                        className="px-4 py-3 text-xs font-medium text-text-muted uppercase tracking-wider select-none"
                                        style={{ textAlign: header.column.id === 'ticker' ? 'left' : 'right' }}
                                    >
                                        <div
                                            {...{
                                                className: header.column.getCanSort()
                                                    ? 'cursor-pointer select-none flex items-center justify-end gap-1 hover:text-text-primary transition-colors'
                                                    : '',
                                                onClick: header.column.getToggleSortingHandler(),
                                                style: { justifyContent: header.column.id === 'ticker' ? 'flex-start' : 'flex-end' }
                                            }}
                                        >
                                            {flexRender(
                                                header.column.columnDef.header,
                                                header.getContext()
                                            )}
                                            {header.column.getCanSort() && (
                                                <ArrowUpDown className={`w-3 h-3 ${isSorted ? 'text-accent' : 'opacity-50'}`} />
                                            )}
                                        </div>
                                    </th>
                                )
                            })}
                        </tr>
                    ))}
                </thead>
                <tbody className="divide-y divide-border-subtle bg-bg-secondary">
                    {table.getRowModel().rows.map((row) => {
                        const isOverConcentrated = row.original.portfolio_weight > concentrationLimit
                        return (
                            <tr
                                key={row.id}
                                className={`${isOverConcentrated ? 'bg-error/5 hover:bg-error/10' : 'hover:bg-bg-tertiary'} transition-colors duration-150`}
                            >
                                {row.getVisibleCells().map((cell) => (
                                    <td key={cell.id} className="px-4 py-3 align-middle">
                                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                    </td>
                                ))}
                            </tr>
                        )
                    })}
                </tbody>
            </table>
        </div>
    )
}
