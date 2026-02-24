import { useCallback, useRef } from 'react'
import { useActivityStore } from '../stores/activityStore'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/activity'

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const {
    setConnected,
    addActivity,
    addActiveAgent,
    removeActiveAgent,
    addThought,
    clearThinking,
    addDebateMessage,
    addMerkleBlock,
    clearActivities,
    clearAllThinking,
    setScenarios,
    setDebatePhase,
  } = useActivityStore()

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)

        switch (data.type) {
          case 'agent_activity':
            addActivity(data.data)
            // Update active agents based on status
            if (['analyzing', 'thinking', 'active'].includes(data.data.status)) {
              addActiveAgent({
                name: data.data.agent_name,
                type: data.data.agent_type,
                status: data.data.status,
              })
            } else if (['complete', 'idle', 'error'].includes(data.data.status)) {
              removeActiveAgent(data.data.agent_name)
            }
            break

          case 'thinking':
            if (data.data.is_complete) {
              clearThinking(data.data.agent_name)
            } else {
              // Use addThought instead of appendThinking - stores individual thoughts
              const thought = data.data.chunk || data.data.content || ''
              if (thought.trim()) {
                addThought(data.data.agent_name, thought.trim())
              }
            }
            break

          case 'debate_message':
            console.log('Debate message received:', data.data)
            addDebateMessage(data.data)
            break

          case 'merkle_block':
            addMerkleBlock(data.data)
            break

          case 'connection':
            console.log('WebSocket connection established:', data.data)
            break

          case 'scenarios':
            console.log('Scenarios received:', data.data)
            setScenarios(data.data)
            break

          case 'debate_phase':
            console.log('Debate phase:', data.data)
            setDebatePhase(data.data.phase, data.data.question || data.data.topic)
            break

          case 'debate_consensus':
            console.log('Debate consensus:', data.data)
            // Consensus message - can be handled by UI components listening to debate state
            break

          case 'scenario_approved':
            console.log('Scenario approved:', data.data)
            // Could trigger a notification or update UI state
            break

          case 'what_if_result':
            console.log('What-if result:', data.data)
            // Could be used to update scenario scores in UI
            break

          default:
            console.log('Unknown message type:', data.type)
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err)
      }
    },
    [
      addActivity,
      addActiveAgent,
      removeActiveAgent,
      addThought,
      clearThinking,
      addDebateMessage,
      addMerkleBlock,
      setScenarios,
      setDebatePhase,
    ]
  )

  const connect = useCallback(() => {
    return new Promise<void>((resolve, reject) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      try {
        const ws = new WebSocket(WS_URL)

        ws.onopen = () => {
          console.log('WebSocket connected')
          setConnected(true)
          resolve()
        }

        ws.onclose = () => {
          console.log('WebSocket disconnected')
          setConnected(false)
          wsRef.current = null

          // Attempt to reconnect after 3 seconds
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...')
            connect().catch(console.error)
          }, 3000)
        }

        ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          reject(error)
        }

        ws.onmessage = handleMessage

        wsRef.current = ws
      } catch (err) {
        reject(err)
      }
    })
  }, [handleMessage, setConnected])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  return { connect, disconnect, send }
}
