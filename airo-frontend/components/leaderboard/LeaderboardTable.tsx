'use client'

import { motion } from 'framer-motion'
import { Badge } from '@/components/ui/badge'

interface LeaderboardEntry {
  rank: number
  model_type: string
  primary_metric: number
  verdict: 'PASS' | 'WARN' | 'FAIL'
}

interface LeaderboardTableProps {
  entries: LeaderboardEntry[]
  metricName: string
}

export function LeaderboardTable({ entries, metricName }: LeaderboardTableProps) {
  
  if (entries.length === 0) {
    return (
      <div className="w-full p-8 bg-white border border-slate-200 rounded-xl text-center">
        <p className="font-sans text-slate-500 text-sm">No models evaluated yet.</p>
      </div>
    )
  }

  const getVerdictStyle = (verdict: string) => {
    switch (verdict) {
      case 'PASS': return 'bg-emerald-50 text-emerald-600 border-emerald-200'
      case 'WARN': return 'bg-amber-50 text-amber-600 border-amber-200'
      case 'FAIL': return 'bg-red-50 text-red-500 border-red-200'
      default: return 'bg-slate-50 text-slate-500 border-slate-200'
    }
  }

  return (
    <div className="w-full bg-white border border-cyan-100 rounded-xl overflow-hidden shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left font-sans text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-cyan-100 text-slate-500 uppercase text-[10px] tracking-wider">
              <th className="px-6 py-4 font-semibold">Rank</th>
              <th className="px-6 py-4 font-semibold">Model Architecture</th>
              <th className="px-6 py-4 font-semibold">{metricName}</th>
              <th className="px-6 py-4 font-semibold">Critic Verdict</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry, idx) => (
              <motion.tr 
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2, delay: idx * 0.05 }}
                key={idx} 
                className={`
                  border-b border-slate-100 hover:bg-cyan-50/30 transition-colors
                  ${idx === 0 ? 'bg-cyan-50/50' : ''}
                `}
              >
                <td className="px-6 py-4">
                  <div className={`
                    w-6 h-6 rounded flex items-center justify-center font-mono text-xs font-bold
                    ${idx === 0 ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-500'}
                  `}>
                    #{entry.rank}
                  </div>
                </td>
                <td className="px-6 py-4 font-medium text-slate-700">
                  {entry.model_type}
                  {idx === 0 && <span className="ml-2 text-[10px] bg-cyan-100 text-cyan-700 px-2 py-0.5 rounded-full font-bold">BEST</span>}
                </td>
                <td className="px-6 py-4 font-mono font-medium text-slate-800">
                  {entry.primary_metric.toFixed(4)}
                </td>
                <td className="px-6 py-4">
                  <Badge variant="outline" className={`font-mono text-[10px] tracking-widest ${getVerdictStyle(entry.verdict)}`}>
                    {entry.verdict}
                  </Badge>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
