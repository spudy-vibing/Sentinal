import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Shield,
  Link,
  Clock,
  Hash,
  FileText,
  Check,
  AlertTriangle,
  Search,
  Filter,
  ChevronDown,
  ChevronRight,
  Download,
  RefreshCw,
  User,
  Activity,
  Database,
  Loader2,
  X,
  Copy,
  CheckCircle2,
  XCircle,
} from 'lucide-react'
import { useActivityStore } from '../stores/activityStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface AuditBlock {
  id: number
  block_index: number
  event_id: string
  event_type: string
  timestamp: string
  session_id?: string
  actor?: string
  action?: string
  resource?: string
  data?: Record<string, unknown>
  previous_hash?: string
  current_hash: string
  block_hash: string
}

interface AuditStats {
  total_blocks: number
  by_event_type: Record<string, number>
  by_actor: Record<string, number>
  last_24h_count: number
  last_activity: string | null
  decisions_logged: number
}

export default function AuditTrail() {
  const [blocks, setBlocks] = useState<AuditBlock[]>([])
  const [stats, setStats] = useState<AuditStats | null>(null)
  const [eventTypes, setEventTypes] = useState<string[]>([])
  const [actors, setActors] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [selectedEventType, setSelectedEventType] = useState<string>('')
  const [selectedActor, setSelectedActor] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [showFilters, setShowFilters] = useState(false)

  // Detail view
  const [expandedBlock, setExpandedBlock] = useState<string | null>(null)
  const [copiedHash, setCopiedHash] = useState<string | null>(null)

  // Verification
  const [isVerifying, setIsVerifying] = useState(false)
  const [verificationResult, setVerificationResult] = useState<{
    valid: boolean
    blocks_checked: number
  } | null>(null)

  // Real-time blocks from WebSocket
  const { merkleBlocks } = useActivityStore()

  const fetchBlocks = useCallback(async () => {
    setError(null)
    try {
      const params = new URLSearchParams()
      if (selectedEventType) params.append('event_type', selectedEventType)
      if (selectedActor) params.append('actor', selectedActor)
      if (searchQuery) params.append('search', searchQuery)
      params.append('limit', '50')

      const response = await fetch(`${API_URL}/api/audit/blocks?${params}`)
      if (response.ok) {
        const data = await response.json()
        setBlocks(data.blocks)
      } else {
        throw new Error('Failed to fetch audit blocks')
      }
    } catch (err) {
      console.error('Failed to fetch audit blocks:', err)
      setError('Failed to load audit trail')
    } finally {
      setIsLoading(false)
    }
  }, [selectedEventType, selectedActor, searchQuery])

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/audit/stats`)
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    }
  }, [])

  const fetchFilters = useCallback(async () => {
    try {
      const [typesRes, actorsRes] = await Promise.all([
        fetch(`${API_URL}/api/audit/event-types`),
        fetch(`${API_URL}/api/audit/actors`)
      ])

      if (typesRes.ok) setEventTypes(await typesRes.json())
      if (actorsRes.ok) setActors(await actorsRes.json())
    } catch (err) {
      console.error('Failed to fetch filters:', err)
    }
  }, [])

  const verifyChain = async () => {
    setIsVerifying(true)
    try {
      const response = await fetch(`${API_URL}/api/audit/verify`)
      if (response.ok) {
        const data = await response.json()
        setVerificationResult(data)
      }
    } catch (err) {
      console.error('Failed to verify chain:', err)
    } finally {
      setIsVerifying(false)
    }
  }

  const seedDemoData = async () => {
    try {
      await fetch(`${API_URL}/api/audit/seed-demo`, { method: 'POST' })
      fetchBlocks()
      fetchStats()
      fetchFilters()
    } catch (err) {
      console.error('Failed to seed demo data:', err)
    }
  }

  const exportAuditTrail = async () => {
    window.open(`${API_URL}/api/audit/export?format=csv`, '_blank')
  }

  const copyHash = (hash: string) => {
    navigator.clipboard.writeText(hash)
    setCopiedHash(hash)
    setTimeout(() => setCopiedHash(null), 2000)
  }

  useEffect(() => {
    fetchBlocks()
    fetchStats()
    fetchFilters()
  }, [fetchBlocks, fetchStats, fetchFilters])

  // Refresh when filters change
  useEffect(() => {
    fetchBlocks()
  }, [selectedEventType, selectedActor, searchQuery, fetchBlocks])

  // Merge real-time blocks with API blocks
  const displayBlocks = blocks.length > 0 ? blocks : merkleBlocks.map((b, i) => ({
    id: i,
    block_index: i,
    event_id: `ws_${i}`,
    event_type: b.event_type,
    timestamp: b.timestamp,
    current_hash: b.block_hash,
    block_hash: b.block_hash
  }))

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const getEventBadgeClass = (eventType: string): string => {
    if (eventType.includes('approved') || eventType.includes('completed')) return 'badge badge-success'
    if (eventType.includes('error') || eventType.includes('denied') || eventType.includes('rejected')) return 'badge badge-error'
    if (eventType.includes('conflict') || eventType.includes('alert') || eventType.includes('warning')) return 'badge badge-warning'
    return 'badge badge-info'
  }

  const getActorIcon = (actor?: string) => {
    if (!actor) return <Database className="w-4 h-4" />
    if (actor.includes('agent') || actor.includes('drift') || actor.includes('tax')) return <Activity className="w-4 h-4" />
    if (actor.includes('advisor') || actor.includes('user')) return <User className="w-4 h-4" />
    return <Database className="w-4 h-4" />
  }

  const formatEventType = (eventType: string): string => {
    return eventType
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-3">
            <Shield className="w-6 h-6 text-accent" />
            Audit Trail
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Cryptographically verifiable decision log via Merkle chain
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={exportAuditTrail}
            className="btn-ghost p-2"
            title="Export to CSV"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={() => { fetchBlocks(); fetchStats(); }}
            className="btn-ghost p-2"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          {blocks.length === 0 && (
            <button
              onClick={seedDemoData}
              className="btn-ghost text-sm"
              title="Seed demo data"
            >
              Seed Demo
            </button>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-5 gap-4">
        <StatCard
          icon={Hash}
          label="Total Blocks"
          value={stats?.total_blocks?.toString() || displayBlocks.length.toString()}
        />
        <StatCard
          icon={Check}
          label="Verified"
          value={verificationResult?.blocks_checked?.toString() || stats?.total_blocks?.toString() || '0'}
          status={verificationResult?.valid === true ? 'success' : verificationResult?.valid === false ? 'error' : undefined}
        />
        <StatCard
          icon={FileText}
          label="Decisions"
          value={stats?.decisions_logged?.toString() || '0'}
        />
        <StatCard
          icon={Activity}
          label="Last 24h"
          value={stats?.last_24h_count?.toString() || '0'}
        />
        <StatCard
          icon={Clock}
          label="Last Activity"
          value={stats?.last_activity ? formatTimestamp(stats.last_activity) : 'N/A'}
        />
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search audit trail..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-bg-tertiary border border-border-subtle rounded-lg text-sm focus:outline-none focus:border-accent"
            />
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`btn-ghost p-2 ${showFilters ? 'bg-accent/10' : ''}`}
          >
            <Filter className="w-4 h-4" />
          </button>

          {/* Verify Button */}
          <button
            onClick={verifyChain}
            disabled={isVerifying}
            className="btn-ghost flex items-center gap-2"
          >
            {isVerifying ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : verificationResult?.valid ? (
              <CheckCircle2 className="w-4 h-4 text-success" />
            ) : verificationResult?.valid === false ? (
              <XCircle className="w-4 h-4 text-error" />
            ) : (
              <Shield className="w-4 h-4" />
            )}
            Verify Chain
          </button>
        </div>

        {/* Expanded Filters */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="flex items-center gap-4 mt-4 pt-4 border-t border-border-subtle">
                <select
                  value={selectedEventType}
                  onChange={(e) => setSelectedEventType(e.target.value)}
                  className="px-3 py-2 bg-bg-tertiary border border-border-subtle rounded-lg text-sm"
                >
                  <option value="">All Event Types</option>
                  {eventTypes.map(type => (
                    <option key={type} value={type}>{formatEventType(type)}</option>
                  ))}
                </select>

                <select
                  value={selectedActor}
                  onChange={(e) => setSelectedActor(e.target.value)}
                  className="px-3 py-2 bg-bg-tertiary border border-border-subtle rounded-lg text-sm"
                >
                  <option value="">All Actors</option>
                  {actors.map(actor => (
                    <option key={actor} value={actor}>{actor}</option>
                  ))}
                </select>

                {(selectedEventType || selectedActor || searchQuery) && (
                  <button
                    onClick={() => {
                      setSelectedEventType('')
                      setSelectedActor('')
                      setSearchQuery('')
                    }}
                    className="btn-ghost text-sm flex items-center gap-1"
                  >
                    <X className="w-3 h-3" />
                    Clear
                  </button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Chain Visualization */}
      <div className="card p-6">
        <h2 className="text-lg font-medium text-text-primary mb-6 flex items-center gap-2">
          <Link className="w-5 h-5 text-accent" />
          Merkle Chain
          <span className="text-sm font-normal text-text-muted ml-2">
            ({displayBlocks.length} blocks)
          </span>
        </h2>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 text-accent animate-spin" />
            <span className="ml-3 text-text-muted">Loading audit trail...</span>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-12">
            <XCircle className="w-10 h-10 text-error mb-3" />
            <p className="text-text-secondary">{error}</p>
            <button onClick={fetchBlocks} className="btn-ghost mt-4">
              <RefreshCw className="w-4 h-4" /> Retry
            </button>
          </div>
        ) : displayBlocks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12">
            <Database className="w-10 h-10 text-text-muted mb-3" />
            <p className="text-text-secondary">No audit blocks found</p>
            <button onClick={seedDemoData} className="btn-primary mt-4">
              Seed Demo Data
            </button>
          </div>
        ) : (
          <div className="relative">
            {/* Connection Line */}
            <div className="absolute left-6 top-0 bottom-0 w-px bg-gradient-to-b from-accent via-accent/50 to-transparent" />

            {/* Blocks */}
            <div className="space-y-3">
              {displayBlocks.map((block, index) => (
                <motion.div
                  key={block.event_id || `block-${index}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="relative pl-16"
                >
                  {/* Node */}
                  <div className="absolute left-4 top-4 w-4 h-4 rounded-full bg-accent shadow-glow" />

                  {/* Block Content */}
                  <div
                    className={`card p-4 border-l-2 cursor-pointer transition-all ${
                      expandedBlock === block.event_id
                        ? 'border-accent bg-accent/5'
                        : 'border-accent/30 hover:border-accent/60'
                    }`}
                    onClick={() => setExpandedBlock(
                      expandedBlock === block.event_id ? null : block.event_id
                    )}
                  >
                    {/* Header */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span className={getEventBadgeClass(block.event_type)}>
                          {formatEventType(block.event_type)}
                        </span>
                        {block.actor && (
                          <span className="flex items-center gap-1 text-xs text-text-muted">
                            {getActorIcon(block.actor)}
                            {block.actor}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-text-muted">
                          {formatTimestamp(block.timestamp)}
                        </span>
                        {expandedBlock === block.event_id ? (
                          <ChevronDown className="w-4 h-4 text-text-muted" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-text-muted" />
                        )}
                      </div>
                    </div>

                    {/* Summary */}
                    {(block.action || block.resource) && (
                      <div className="text-sm text-text-secondary mb-2">
                        {block.action && <span className="font-medium">{block.action}</span>}
                        {block.action && block.resource && ' → '}
                        {block.resource && <span className="font-mono text-accent">{block.resource}</span>}
                      </div>
                    )}

                    {/* Hash */}
                    <div className="flex items-center gap-2 font-mono text-xs text-text-muted">
                      <span>Hash:</span>
                      <span className="text-accent">{block.block_hash?.slice(0, 16) || block.current_hash?.slice(0, 16)}...</span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          copyHash(block.current_hash || block.block_hash)
                        }}
                        className="p-1 hover:bg-bg-tertiary rounded"
                        title="Copy full hash"
                      >
                        {copiedHash === (block.current_hash || block.block_hash) ? (
                          <Check className="w-3 h-3 text-success" />
                        ) : (
                          <Copy className="w-3 h-3" />
                        )}
                      </button>
                    </div>

                    {/* Expanded Detail */}
                    <AnimatePresence>
                      {expandedBlock === block.event_id && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="overflow-hidden"
                        >
                          <div className="mt-4 pt-4 border-t border-border-subtle space-y-2">
                            <DetailRow label="Event ID" value={block.event_id} mono />
                            <DetailRow label="Block Index" value={block.block_index?.toString()} />
                            <DetailRow label="Timestamp" value={new Date(block.timestamp).toLocaleString()} />
                            {block.session_id && <DetailRow label="Session" value={block.session_id} mono />}
                            {block.previous_hash && (
                              <DetailRow label="Previous Hash" value={block.previous_hash} mono truncate />
                            )}
                            <DetailRow label="Current Hash" value={block.current_hash} mono truncate />
                            {block.data && Object.keys(block.data).length > 0 && (
                              <div className="mt-2">
                                <span className="text-xs text-text-muted">Data Payload:</span>
                                <pre className="mt-1 p-2 bg-bg-tertiary rounded text-xs overflow-x-auto">
                                  {JSON.stringify(block.data, null, 2)}
                                </pre>
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Integrity Check */}
      {verificationResult && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`card p-6 border-l-4 ${
            verificationResult.valid ? 'border-success' : 'border-error'
          }`}
        >
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              verificationResult.valid ? 'bg-success/10' : 'bg-error/10'
            }`}>
              {verificationResult.valid ? (
                <CheckCircle2 className="w-5 h-5 text-success" />
              ) : (
                <XCircle className="w-5 h-5 text-error" />
              )}
            </div>
            <div>
              <h3 className="font-medium text-text-primary">
                {verificationResult.valid ? 'Chain Integrity Verified' : 'Chain Integrity Issues Detected'}
              </h3>
              <p className="text-sm text-text-secondary">
                {verificationResult.blocks_checked} blocks verified.
                {verificationResult.valid
                  ? ' No tampering detected.'
                  : ' Some blocks may have been modified.'}
              </p>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}

interface StatCardProps {
  icon: React.ElementType
  label: string
  value: string
  status?: 'success' | 'error'
}

function StatCard({ icon: Icon, label, value, status }: StatCardProps) {
  return (
    <div className="metric-card">
      <Icon className={`w-5 h-5 mb-2 ${
        status === 'success' ? 'text-success' :
        status === 'error' ? 'text-error' :
        'text-text-muted'
      }`} />
      <div className="metric-value">{value}</div>
      <div className="metric-label">{label}</div>
    </div>
  )
}

interface DetailRowProps {
  label: string
  value?: string
  mono?: boolean
  truncate?: boolean
}

function DetailRow({ label, value, mono, truncate }: DetailRowProps) {
  if (!value) return null
  return (
    <div className="flex items-start gap-2 text-xs">
      <span className="text-text-muted w-24 shrink-0">{label}:</span>
      <span className={`text-text-primary ${mono ? 'font-mono' : ''} ${truncate ? 'truncate max-w-xs' : ''}`}>
        {value}
      </span>
    </div>
  )
}
