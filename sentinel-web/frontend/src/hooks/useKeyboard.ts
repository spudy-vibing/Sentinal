import { useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useActivityStore } from '../stores/activityStore'

interface KeyboardShortcut {
  key: string
  ctrl?: boolean
  meta?: boolean
  shift?: boolean
  description: string
  action: () => void
}

export function useKeyboardShortcuts() {
  const navigate = useNavigate()
  const { setChatOpen, chatOpen, togglePortfolioSelector } = useActivityStore()

  const shortcuts: KeyboardShortcut[] = [
    // Navigation
    {
      key: '1',
      meta: true,
      description: 'Go to Dashboard',
      action: () => navigate('/'),
    },
    {
      key: '2',
      meta: true,
      description: 'Go to Scenarios',
      action: () => navigate('/scenarios'),
    },
    {
      key: '3',
      meta: true,
      description: 'Go to War Room',
      action: () => navigate('/war-room'),
    },
    {
      key: '4',
      meta: true,
      description: 'Go to Audit Trail',
      action: () => navigate('/audit'),
    },

    // Actions
    {
      key: 'p',
      meta: true,
      shift: true,
      description: 'Toggle Portfolio Selector',
      action: () => togglePortfolioSelector(),
    },
    {
      key: 'k',
      meta: true,
      description: 'Toggle Chat Panel',
      action: () => setChatOpen(!chatOpen),
    },
    {
      key: '/',
      description: 'Focus Chat Input',
      action: () => {
        setChatOpen(true)
        setTimeout(() => {
          const input = document.querySelector('input[placeholder*="Ask"]') as HTMLInputElement
          input?.focus()
        }, 100)
      },
    },
    {
      key: 'Escape',
      description: 'Close Chat Panel',
      action: () => setChatOpen(false),
    },
  ]

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      const target = event.target as HTMLElement
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        // Allow Escape to still work
        if (event.key !== 'Escape') {
          return
        }
      }

      const matchingShortcut = shortcuts.find((shortcut) => {
        const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase()
        const ctrlMatch = shortcut.ctrl ? event.ctrlKey : true
        const metaMatch = shortcut.meta ? event.metaKey || event.ctrlKey : true
        const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey

        return (
          keyMatch &&
          ctrlMatch &&
          (shortcut.meta ? metaMatch : !event.metaKey && !event.ctrlKey) &&
          shiftMatch
        )
      })

      if (matchingShortcut) {
        event.preventDefault()
        matchingShortcut.action()
      }
    },
    [shortcuts]
  )

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  return shortcuts
}

// Hook for displaying keyboard shortcut hints
export function useShortcutHint(key: string, meta = false): string {
  const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform)

  if (meta) {
    return isMac ? `⌘${key.toUpperCase()}` : `Ctrl+${key.toUpperCase()}`
  }
  return key.toUpperCase()
}

// Component to display keyboard shortcuts help
export function getShortcutsList() {
  return [
    { keys: '⌘1', description: 'Dashboard' },
    { keys: '⌘2', description: 'Scenarios' },
    { keys: '⌘3', description: 'War Room' },
    { keys: '⌘4', description: 'Audit Trail' },
    { keys: '⌘⇧P', description: 'Switch Portfolio' },
    { keys: '⌘K', description: 'Toggle Chat' },
    { keys: '/', description: 'Focus Chat' },
    { keys: 'Esc', description: 'Close Panel' },
  ]
}
