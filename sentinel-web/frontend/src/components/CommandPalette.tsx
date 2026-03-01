import { useEffect, useState } from 'react'
import { Command } from 'cmdk'
import { Search, Monitor, GitBranch, Crosshair, Users, Settings } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface CommandPaletteProps {
    onNavigate: (route: string) => void
}

export default function CommandPalette({ onNavigate }: CommandPaletteProps) {
    const [open, setOpen] = useState(false)

    // Toggle the menu when ⌘K is pressed
    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
                e.preventDefault()
                setOpen((open) => !open)
            }
        }

        document.addEventListener('keydown', down)
        return () => document.removeEventListener('keydown', down)
    }, [])

    const handleSelect = (route: string) => {
        onNavigate(route)
        setOpen(false)
    }

    return (
        <AnimatePresence>
            {open && (
                <Command.Dialog
                    open={open}
                    onOpenChange={setOpen}
                    label="Global Command Menu"
                    className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] bg-black/40 backdrop-blur-sm"
                >
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: -20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: -20 }}
                        className="w-full max-w-xl mx-4 overflow-hidden rounded-xl bg-bg-secondary border border-border-default shadow-[0_0_50px_-12px_rgba(59,130,246,0.3)] font-sans"
                    >
                        <div className="flex items-center px-4 border-b border-border-subtle text-text-muted">
                            <Search className="w-5 h-5 ml-2 mr-3 opacity-50 text-text-primary" />
                            <Command.Input
                                autoFocus
                                placeholder="Type a command or search..."
                                className="w-full h-14 bg-transparent outline-none text-text-primary placeholder:text-text-muted text-lg font-medium"
                            />
                        </div>

                        <Command.List className="max-h-[300px] overflow-y-auto p-2 scrollbar-hide">
                            <Command.Empty className="py-6 text-center text-sm text-text-muted">
                                No results found.
                            </Command.Empty>

                            <Command.Group heading="Navigation" className="px-2 py-3 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                                <Command.Item
                                    onSelect={() => handleSelect('/')}
                                    className="flex items-center px-3 py-2.5 mt-1 text-sm rounded-lg cursor-pointer text-text-primary hover:bg-accent hover:text-white transition-colors aria-selected:bg-accent aria-selected:text-white group"
                                >
                                    <Monitor className="w-4 h-4 mr-3 text-text-muted group-aria-selected:text-white group-hover:text-white" />
                                    Dashboard (Overview)
                                </Command.Item>
                                <Command.Item
                                    onSelect={() => handleSelect('/scenarios')}
                                    className="flex items-center px-3 py-2.5 mt-1 text-sm rounded-lg cursor-pointer text-text-primary hover:bg-accent hover:text-white transition-colors aria-selected:bg-accent aria-selected:text-white group"
                                >
                                    <GitBranch className="w-4 h-4 mr-3 text-text-muted group-aria-selected:text-white group-hover:text-white" />
                                    Scenarios & Trade Proposals
                                </Command.Item>
                                <Command.Item
                                    onSelect={() => handleSelect('/opportunities')}
                                    className="flex items-center px-3 py-2.5 mt-1 text-sm rounded-lg cursor-pointer text-text-primary hover:bg-accent hover:text-white transition-colors aria-selected:bg-accent aria-selected:text-white group"
                                >
                                    <Crosshair className="w-4 h-4 mr-3 text-text-muted group-aria-selected:text-white group-hover:text-white" />
                                    Active Opportunities
                                </Command.Item>
                                <Command.Item
                                    onSelect={() => handleSelect('/war-room')}
                                    className="flex items-center px-3 py-2.5 mt-1 text-sm rounded-lg cursor-pointer text-text-primary hover:bg-accent hover:text-white transition-colors aria-selected:bg-accent aria-selected:text-white group"
                                >
                                    <Users className="w-4 h-4 mr-3 text-text-muted group-aria-selected:text-white group-hover:text-white" />
                                    Agent War Room
                                </Command.Item>
                            </Command.Group>

                            <Command.Separator className="h-px bg-border-subtle my-2 mx-2" />

                            <Command.Group heading="Quick Actions" className="px-2 py-3 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                                <Command.Item
                                    onSelect={() => { setOpen(false); /* Trigger synthesis */ }}
                                    className="flex items-center px-3 py-2.5 mt-1 text-sm rounded-lg cursor-pointer text-text-primary hover:bg-bg-tertiary transition-colors aria-selected:bg-bg-tertiary aria-selected:text-text-primary group"
                                >
                                    <div className="w-4 h-4 mr-3 rounded-full border border-border-default flex items-center justify-center text-[8px] font-mono group-aria-selected:border-text-primary">⌘</div>
                                    Force Portfolio Synthesis
                                </Command.Item>
                                <Command.Item
                                    onSelect={() => { setOpen(false); /* Open settings */ }}
                                    className="flex items-center px-3 py-2.5 mt-1 text-sm rounded-lg cursor-pointer text-text-primary hover:bg-bg-tertiary transition-colors aria-selected:bg-bg-tertiary aria-selected:text-text-primary group"
                                >
                                    <Settings className="w-4 h-4 mr-3 text-text-muted group-aria-selected:text-text-primary hover:text-text-primary" />
                                    Settings & Preferences
                                </Command.Item>
                            </Command.Group>
                        </Command.List>
                    </motion.div>
                </Command.Dialog>
            )}
        </AnimatePresence>
    )
}
