'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  LayoutDashboard, 
  PlayCircle, 
  Activity, 
  BarChart2, 
  FileText, 
  GitBranch,
  Microscope
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { airoApi } from '@/lib/api'

const navItems = [
  { href: '/', label: 'Home', icon: LayoutDashboard },
  { href: '/run', label: 'Run Experiment', icon: PlayCircle },
  { href: '/trace', label: 'Live Trace', icon: Activity },
  { href: '/leaderboard', label: 'Leaderboard', icon: BarChart2 },
  { href: '/report', label: 'Report Viewer', icon: FileText },
]

export function Sidebar() {
  const pathname = usePathname()
  const [expCount, setExpCount] = useState(0)

  useEffect(() => {
    // Fetch experiment count for stats block
    airoApi.getExperiments().then((exps) => {
      setExpCount(exps.length)
    }).catch(() => {})
  }, [pathname]) // Refresh count on navigation

  return (
    <aside className="hidden md:flex w-64 flex-col bg-white border-r border-slate-200/60 shadow-sm h-screen sticky top-0">
      
      {/* Brand Block */}
      <div className="p-6 pb-8 border-b border-slate-100">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-400 to-cyan-600 flex items-center justify-center text-white shadow-sm">
            <Microscope size={18} />
          </div>
          <div>
            <h1 className="font-sans font-bold text-lg text-slate-800 leading-tight">AIRO</h1>
            <p className="font-mono text-[10px] text-cyan-600 leading-tight tracking-tight">AI Research Orchestrator</p>
          </div>
        </div>
        <p className="font-sans text-[10px] text-slate-400 mt-2 ml-[44px]">v0.1.0</p>
      </div>

      {/* Nav Links */}
      <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link 
              key={item.href} 
              href={item.href}
              className={`
                flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-150
                ${isActive 
                  ? 'bg-cyan-50 border-l-2 border-cyan-500 text-slate-800' 
                  : 'text-slate-600 hover:bg-slate-50 border-l-2 border-transparent'
                }
              `}
            >
              <item.icon 
                size={18} 
                className={isActive ? 'text-cyan-500' : 'text-slate-400'} 
              />
              <span className="font-sans text-sm font-medium">{item.label}</span>
            </Link>
          )
        })}
      </nav>

      {/* Footer Stats Block */}
      <div className="p-4 bg-slate-50 border-t border-slate-200 mt-auto">
        <div className="space-y-2 mb-4">
          <div className="flex justify-between items-center">
            <span className="font-sans text-xs text-slate-500">Experiments run</span>
            <span className="font-mono text-[11px] text-cyan-600 font-medium">{expCount}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="font-sans text-xs text-slate-500">Agents</span>
            <span className="font-mono text-[11px] text-emerald-600 font-medium">6</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="font-sans text-xs text-slate-500">LLM Provider</span>
            <span className="font-mono text-[11px] text-amber-600 font-medium">Groq</span>
          </div>
        </div>
        
        <div className="w-full h-px bg-slate-200 mb-4" />
        
        <Link 
          href="https://github.com" 
          target="_blank"
          className="flex items-center justify-center gap-2 w-full py-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
        >
          <GitBranch size={16} />
          <span className="font-sans text-xs">View Source</span>
        </Link>
      </div>

    </aside>
  )
}
