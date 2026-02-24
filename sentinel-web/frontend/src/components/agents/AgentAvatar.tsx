import { motion } from 'framer-motion'
import {
  TrendingUp,
  Calculator,
  Shield,
  GitBranch,
  Cpu,
  Brain,
  Zap
} from 'lucide-react'

type AgentType = 'coordinator' | 'drift' | 'tax' | 'compliance' | 'scenario' | 'system'

interface AgentAvatarProps {
  type: AgentType
  name?: string
  size?: 'sm' | 'md' | 'lg'
  isActive?: boolean
  isThinking?: boolean
  showPulse?: boolean
}

const AGENT_CONFIG: Record<AgentType, {
  icon: React.ElementType
  color: string
  bgColor: string
  borderColor: string
  label: string
}> = {
  coordinator: {
    icon: Cpu,
    color: 'text-text-primary',
    bgColor: 'bg-text-primary/10',
    borderColor: 'border-text-primary/30',
    label: 'Coordinator',
  },
  drift: {
    icon: TrendingUp,
    color: 'text-info',
    bgColor: 'bg-info/10',
    borderColor: 'border-info/30',
    label: 'Drift Agent',
  },
  tax: {
    icon: Calculator,
    color: 'text-success',
    bgColor: 'bg-success/10',
    borderColor: 'border-success/30',
    label: 'Tax Agent',
  },
  compliance: {
    icon: Shield,
    color: 'text-warning',
    bgColor: 'bg-warning/10',
    borderColor: 'border-warning/30',
    label: 'Compliance',
  },
  scenario: {
    icon: GitBranch,
    color: 'text-accent',
    bgColor: 'bg-accent/10',
    borderColor: 'border-accent/30',
    label: 'Scenario Agent',
  },
  system: {
    icon: Zap,
    color: 'text-text-muted',
    bgColor: 'bg-text-muted/10',
    borderColor: 'border-text-muted/30',
    label: 'System',
  },
}

const SIZES = {
  sm: { container: 'w-8 h-8', icon: 'w-4 h-4' },
  md: { container: 'w-10 h-10', icon: 'w-5 h-5' },
  lg: { container: 'w-14 h-14', icon: 'w-7 h-7' },
}

export default function AgentAvatar({
  type,
  name,
  size = 'md',
  isActive = false,
  isThinking = false,
  showPulse = false,
}: AgentAvatarProps) {
  const config = AGENT_CONFIG[type] || AGENT_CONFIG.system
  const Icon = isThinking ? Brain : config.icon
  const sizeClasses = SIZES[size]

  return (
    <div className="relative">
      {/* Pulse ring */}
      {(showPulse || isActive) && (
        <motion.div
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.5, 0, 0.5],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
          className={`absolute inset-0 rounded-full ${config.bgColor}`}
        />
      )}

      {/* Glow effect for active state */}
      {isActive && (
        <motion.div
          animate={{
            boxShadow: [
              '0 0 0 rgba(0, 229, 204, 0)',
              '0 0 20px rgba(0, 229, 204, 0.3)',
              '0 0 0 rgba(0, 229, 204, 0)',
            ],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
          className={`absolute inset-0 rounded-full`}
        />
      )}

      {/* Avatar */}
      <motion.div
        animate={isActive ? { scale: [1, 1.05, 1] } : {}}
        transition={{ duration: 0.5, repeat: isActive ? Infinity : 0 }}
        className={`
          relative ${sizeClasses.container} rounded-full
          ${config.bgColor} border ${config.borderColor}
          flex items-center justify-center
          ${isActive ? 'shadow-glow' : ''}
        `}
      >
        <Icon
          className={`
            ${sizeClasses.icon} ${config.color}
            ${isThinking ? 'animate-pulse' : ''}
          `}
        />

        {/* Thinking indicator */}
        {isThinking && (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            className="absolute inset-0 rounded-full border-2 border-transparent border-t-accent"
          />
        )}
      </motion.div>

      {/* Status dot */}
      {isActive && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-accent border-2 border-bg-primary"
        />
      )}
    </div>
  )
}

export function AgentAvatarWithLabel({
  type,
  name,
  size = 'md',
  isActive = false,
  isThinking = false,
}: AgentAvatarProps) {
  const config = AGENT_CONFIG[type] || AGENT_CONFIG.system

  return (
    <div className="flex items-center gap-3">
      <AgentAvatar
        type={type}
        size={size}
        isActive={isActive}
        isThinking={isThinking}
      />
      <div>
        <p className={`font-medium ${isActive ? 'text-accent' : config.color}`}>
          {name || config.label}
        </p>
        {isThinking && (
          <p className="text-xs text-accent animate-pulse">Thinking...</p>
        )}
      </div>
    </div>
  )
}
