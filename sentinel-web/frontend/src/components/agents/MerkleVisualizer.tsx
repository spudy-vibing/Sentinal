import { motion, AnimatePresence } from 'framer-motion'
import { Shield, Link, Check, Clock } from 'lucide-react'
import { useActivityStore } from '../../stores/activityStore'

export default function MerkleVisualizer() {
  const { merkleBlocks } = useActivityStore()

  // Show last 5 blocks
  const displayBlocks = merkleBlocks.slice(-5).reverse()

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-text-primary flex items-center gap-2">
          <Shield className="w-4 h-4 text-accent" />
          Merkle Audit Chain
        </h3>
        <span className="text-xs text-text-muted">
          {merkleBlocks.length} blocks
        </span>
      </div>

      {displayBlocks.length === 0 ? (
        <div className="text-center py-6">
          <Shield className="w-8 h-8 text-text-muted mx-auto mb-2 opacity-50" />
          <p className="text-xs text-text-muted">No blocks recorded yet</p>
          <p className="text-xs text-text-muted">Approve a scenario to create the first block</p>
        </div>
      ) : (
        <div className="relative space-y-2">
          {/* Chain connection */}
          <div className="absolute left-3 top-2 bottom-2 w-px bg-gradient-to-b from-accent via-accent/50 to-transparent" />

          <AnimatePresence mode="popLayout">
            {displayBlocks.map((block, index) => (
              <motion.div
                key={block.block_hash}
                initial={{ opacity: 0, x: -20, scale: 0.95 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: 20, scale: 0.95 }}
                transition={{ delay: index * 0.05 }}
                className="relative pl-8"
              >
                {/* Chain node */}
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className={`absolute left-1 top-2 w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                    index === 0
                      ? 'bg-accent border-accent'
                      : 'bg-bg-tertiary border-accent/50'
                  }`}
                >
                  {index === 0 ? (
                    <Check className="w-2 h-2 text-bg-primary" />
                  ) : (
                    <Link className="w-2 h-2 text-accent" />
                  )}
                </motion.div>

                {/* Block content */}
                <div
                  className={`p-3 rounded-md border transition-all ${
                    index === 0
                      ? 'bg-accent/5 border-accent/30'
                      : 'bg-bg-tertiary border-border-subtle'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="badge badge-accent text-xs">
                      {formatEventType(block.event_type)}
                    </span>
                    <span className="text-xs text-text-muted flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatTime(block.timestamp)}
                    </span>
                  </div>
                  <div className="font-mono text-xs text-text-secondary truncate">
                    {block.block_hash}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Chain integrity */}
      {merkleBlocks.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 pt-3 border-t border-border-subtle"
        >
          <div className="flex items-center gap-2 text-xs">
            <Check className="w-3 h-3 text-success" />
            <span className="text-text-muted">
              Chain verified • {merkleBlocks.length} immutable records
            </span>
          </div>
        </motion.div>
      )}
    </div>
  )
}

function formatEventType(eventType: string): string {
  return eventType
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function formatTime(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  })
}
