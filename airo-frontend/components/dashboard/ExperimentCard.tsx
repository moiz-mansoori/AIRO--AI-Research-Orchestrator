'use client'

import { motion } from 'framer-motion'
import { FileText, Inbox } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

interface ExperimentCardProps {
  experimentId: string
  bestModelType: string
  bestMetric: number
  verdict: 'PASS' | 'WARN' | 'FAIL'
  hasReport: boolean
  delay?: number
}

export function ExperimentCard({ experimentId, bestModelType, bestMetric, verdict, hasReport, delay = 0 }: ExperimentCardProps) {
  
  const getVerdictStyle = () => {
    switch (verdict) {
      case 'PASS': return 'bg-emerald-50 text-emerald-600 border-emerald-200'
      case 'WARN': return 'bg-amber-50 text-amber-600 border-amber-200'
      case 'FAIL': return 'bg-red-50 text-red-500 border-red-200'
      default: return 'bg-slate-50 text-slate-500 border-slate-200'
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay, ease: 'easeOut' }}
      className="flex items-center justify-between p-4 bg-white border border-slate-100 rounded-xl hover:shadow-cyan-sm transition-all"
    >
      <div className="flex flex-col gap-1">
        <span className="font-mono text-xs text-cyan-600 font-medium">
          {experimentId}
        </span>
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <span className="font-medium text-slate-700">{bestModelType}</span>
          <span>•</span>
          <span className="font-mono text-[11px]">Metric: {bestMetric.toFixed(4)}</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <Badge variant="outline" className={`font-mono text-[10px] tracking-widest ${getVerdictStyle()}`}>
          {verdict}
        </Badge>
        
        {hasReport ? (
          <Link href={`/report?id=${experimentId}`}>
            <Button variant="outline" size="sm" className="border-cyan-300 text-cyan-600 hover:bg-cyan-50 gap-2">
              <FileText size={14} />
              View Report
            </Button>
          </Link>
        ) : (
          <Button variant="outline" size="sm" disabled className="gap-2">
            No Report
          </Button>
        )}
      </div>
    </motion.div>
  )
}

export function EmptyExperimentCard() {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
      <Inbox className="text-slate-300 mb-3" size={32} />
      <p className="font-sans text-sm text-slate-500 mb-4">No experiments found.</p>
      <Link href="/run">
        <Button className="bg-gradient-to-r from-cyan-500 to-cyan-600 text-white hover:brightness-110 shadow-sm">
          Run your first experiment
        </Button>
      </Link>
    </div>
  )
}
