'use client'

import { useEffect, useRef } from 'react'
import { Terminal, ScrollText } from 'lucide-react'

interface LogTerminalProps {
  logs: string[]
  isRunning: boolean
}

export function LogTerminal({ logs, isRunning }: LogTerminalProps) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Auto-scroll to bottom
    if (endRef.current) {
      endRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  // Helper to colorize log levels
  const formatLogLine = (line: string, idx: number) => {
    let colorClass = 'text-slate-300'
    if (line.includes('INFO')) colorClass = 'text-cyan-400'
    if (line.includes('ERROR') || line.includes('FAIL')) colorClass = 'text-red-400'
    if (line.includes('WARNING') || line.includes('WARN')) colorClass = 'text-amber-400'
    if (line.includes('SUCCESS') || line.includes('PASS')) colorClass = 'text-emerald-400'

    // Highlight agent tags like [data] or [train]
    const agentMatch = line.match(/\[(.*?)\]/)
    const agentTag = agentMatch ? agentMatch[0] : null
    const textAfterTag = agentTag ? line.split(agentTag)[1] : line

    return (
      <div key={idx} className="font-mono text-[13px] leading-relaxed break-words hover:bg-slate-800/50 px-2 rounded">
        {agentTag && <span className="text-fuchsia-400 mr-2">{agentTag}</span>}
        <span className={colorClass}>{textAfterTag}</span>
      </div>
    )
  }

  return (
    <div className="flex flex-col w-full h-[600px] bg-[#0F172A] rounded-xl border border-slate-700 shadow-2xl overflow-hidden">
      
      {/* Terminal Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-[#1E293B] border-b border-slate-700">
        <div className="flex items-center gap-2">
          <Terminal size={16} className="text-slate-400" />
          <span className="font-sans text-xs font-medium text-slate-300">airo.log</span>
        </div>
        <div className="flex items-center gap-2">
          {isRunning && (
            <span className="flex items-center gap-2 text-[10px] text-emerald-400 uppercase tracking-widest font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Streaming
            </span>
          )}
        </div>
      </div>

      {/* Terminal Body */}
      <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
        {logs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 gap-3">
            <ScrollText size={32} className="opacity-50" />
            <p className="font-mono text-sm">No logs recorded yet.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-1 pb-4">
            {logs.map((line, i) => formatLogLine(line, i))}
            <div ref={endRef} />
          </div>
        )}
      </div>
    </div>
  )
}
