import { useEffect } from 'react'
import ReactFlow, {
    Background,
    Controls,
    Edge,
    Node,
    useNodesState,
    useEdgesState,
    MarkerType,
    Handle,
    Position,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Brain, Shield, Clock, AlertTriangle, Scale } from 'lucide-react'

// Custom Node Component for Agents
const AgentNode = ({ data }: { data: any }) => {
    const Icon = data.icon
    return (
        <div className={`px-4 py-3 shadow-glow rounded-xl bg-bg-secondary border-2 ${data.borderColor} flex items-center gap-3 min-w-[200px]`}>
            <Handle type="source" position={Position.Bottom} className="opacity-0" />
            <Handle type="target" position={Position.Top} className="opacity-0" />

            <div className={`p-2 rounded-lg ${data.bgColor}`}>
                <Icon className={`w-5 h-5 ${data.iconColor}`} />
            </div>
            <div>
                <div className="text-sm font-bold text-text-primary">{data.label}</div>
                <div className="text-xs text-text-muted mt-0.5">{data.status}</div>
            </div>
            {data.isThinking && (
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-accent rounded-full animate-ping" />
            )}
        </div>
    )
}

// Custom Node Component for the Coordinator
const CoordinatorNode = ({ data }: { data: any }) => {
    return (
        <div className="px-6 py-4 shadow-glow-lg rounded-2xl bg-gradient-to-br from-accent-dim to-bg-secondary border-2 border-accent flex flex-col items-center gap-2 min-w-[240px]">
            <Handle type="target" position={Position.Top} className="opacity-0" />
            <Handle type="source" position={Position.Bottom} className="opacity-0" />

            <div className="p-3 rounded-xl bg-accent/20">
                <Brain className="w-8 h-8 text-accent animate-pulse" />
            </div>
            <div className="text-center">
                <div className="text-base font-bold text-text-primary">{data.label}</div>
                <div className="text-xs text-text-secondary mt-1 max-w-[200px] leading-tight">
                    {data.status}
                </div>
            </div>
        </div>
    )
}

const nodeTypes = {
    agent: AgentNode,
    coordinator: CoordinatorNode,
}

interface AgentDebateGraphProps {
    debatePhase: 'idle' | 'opening' | 'debate' | 'consensus'
    activeAgents: string[]
    recentMessage?: { agent_id: string; message: string }
}

export default function AgentDebateGraph({ debatePhase, activeAgents, recentMessage }: AgentDebateGraphProps) {
    const [nodes, setNodes, onNodesChange] = useNodesState([])
    const [edges, setEdges, onEdgesChange] = useEdgesState([])

    // Initialize graph topology
    useEffect(() => {
        const initialNodes: Node[] = [
            {
                id: 'coordinator',
                type: 'coordinator',
                position: { x: 300, y: 250 },
                data: {
                    label: 'Sentinal Core',
                    status: 'Waiting for topic...'
                }
            },
            {
                id: 'drift',
                type: 'agent',
                position: { x: 50, y: 50 },
                data: {
                    label: 'Drift Agent',
                    status: 'Idle',
                    icon: AlertTriangle,
                    borderColor: 'border-info',
                    bgColor: 'bg-info/10',
                    iconColor: 'text-info',
                    isThinking: false
                }
            },
            {
                id: 'tax',
                type: 'agent',
                position: { x: 550, y: 50 },
                data: {
                    label: 'Tax Agent',
                    status: 'Idle',
                    icon: Clock,
                    borderColor: 'border-success',
                    bgColor: 'bg-success/10',
                    iconColor: 'text-success',
                    isThinking: false
                }
            },
            {
                id: 'compliance',
                type: 'agent',
                position: { x: 300, y: 50 },
                data: {
                    label: 'Compliance Agent',
                    status: 'Idle',
                    icon: Shield,
                    borderColor: 'border-warning',
                    bgColor: 'bg-warning/10',
                    iconColor: 'text-warning',
                    isThinking: false
                }
            },
            {
                id: 'scenario',
                type: 'agent',
                position: { x: 550, y: 450 },
                data: {
                    label: 'Scenario Agent',
                    status: 'Idle',
                    icon: Scale,
                    borderColor: 'border-accent',
                    bgColor: 'bg-accent/10',
                    iconColor: 'text-accent',
                    isThinking: false
                }
            },
        ]

        const initialEdges: Edge[] = [
            { id: 'e-drift', source: 'drift', target: 'coordinator', animated: false, style: { stroke: 'var(--border-default)' } },
            { id: 'e-tax', source: 'tax', target: 'coordinator', animated: false, style: { stroke: 'var(--border-default)' } },
            { id: 'e-comp', source: 'compliance', target: 'coordinator', animated: false, style: { stroke: 'var(--border-default)' } },
            { id: 'e-scen', source: 'scenario', target: 'coordinator', animated: false, style: { stroke: 'var(--border-default)' } },
        ]

        setNodes(initialNodes)
        setEdges(initialEdges)
    }, [])

    // Update nodes and edges based on debate state
    useEffect(() => {
        setNodes((nds) =>
            nds.map((node) => {
                if (node.id === 'coordinator') {
                    let status = 'Waiting for topic...'
                    if (debatePhase === 'opening') status = 'Initiating Debate...'
                    else if (debatePhase === 'debate') status = 'Synthesizing Arguments...'
                    else if (debatePhase === 'consensus') status = 'Consensus Reached'

                    return { ...node, data: { ...node.data, status } }
                }

                const isThinking = activeAgents.includes(node.id) || (recentMessage && recentMessage.agent_id === node.id)
                let status = 'Idle'

                if (isThinking) {
                    status = 'Analyzing...'
                } else if (debatePhase === 'consensus') {
                    status = 'Agreed'
                }

                return {
                    ...node,
                    data: { ...node.data, isThinking, status }
                }
            })
        )

        setEdges((eds) =>
            eds.map((edge) => {
                const sourceAgent = edge.source
                const isActive = activeAgents.includes(sourceAgent) || (recentMessage && recentMessage.agent_id === sourceAgent)

                let strokeColor = 'var(--border-default)'
                if (isActive) {
                    if (sourceAgent === 'drift') strokeColor = 'var(--info)'
                    if (sourceAgent === 'tax') strokeColor = 'var(--success)'
                    if (sourceAgent === 'compliance') strokeColor = 'var(--warning)'
                    if (sourceAgent === 'scenario') strokeColor = 'var(--accent)'
                }

                return {
                    ...edge,
                    animated: isActive || debatePhase === 'debate',
                    style: {
                        stroke: strokeColor,
                        strokeWidth: isActive ? 3 : 1
                    },
                    markerEnd: {
                        type: MarkerType.ArrowClosed,
                        color: strokeColor,
                    }
                }
            })
        )

    }, [debatePhase, activeAgents, recentMessage])

    return (
        <div className="h-[500px] w-full bg-bg-tertiary/20 rounded-xl border border-border-subtle overflow-hidden relative">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                nodeTypes={nodeTypes}
                fitView
                attributionPosition="bottom-right"
                className="touch-none"
            >
                <Background color="var(--border-default)" gap={16} />
                <Controls showInteractive={false} className="bg-bg-secondary border-border-subtle fill-text-secondary" />
            </ReactFlow>

            {/* Floating Gradient Overlay for Depth */}
            <div className="absolute inset-0 pointer-events-none rounded-xl shadow-[inset_0_0_60px_rgba(0,0,0,0.05)] dark:shadow-[inset_0_0_60px_rgba(255,255,255,0.02)]" />
        </div>
    )
}
