'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Zap } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { useExperimentStore } from '@/store/experimentStore'

const AGENT_STEPS = [
  { id: 'data', name: 'Data' },
  { id: 'config', name: 'Config' },
  { id: 'train', name: 'Training' },
  { id: 'critic', name: 'Critic' },
  { id: 'eval', name: 'Evaluator' },
  { id: 'report', name: 'Reporter' }
]

export function RunningBanner() {
  const { experimentId, startTime, logs } = useExperimentStore()
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    if (!startTime) return
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)
    return () => clearInterval(interval)
  }, [startTime])

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60).toString().padStart(2, '0')
    const s = (secs % 60).toString().padStart(2, '0')
    return `${m}:${s}`
  }

  // Derive current agent from logs simply by looking for the last tag
  const lastLog = logs.length > 0 ? logs[logs.length - 1] : ''
  let activeAgent = 'data'
  if (lastLog.includes('[config]')) activeAgent = 'config'
  else if (lastLog.includes('[train]')) activeAgent = 'train'
  else if (lastLog.includes('[critic]')) activeAgent = 'critic'
  else if (lastLog.includes('[evaluator]')) activeAgent = 'eval'
  else if (lastLog.includes('[report]')) activeAgent = 'report'

  const activeIndex = AGENT_STEPS.findIndex(a => a.id === activeAgent)

  return (
    <motion.div 
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full bg-gradient-to-r from-cyan-50 to-emerald-50 border-l-4 border-cyan-500 rounded-xl p-5 mb-8 shadow-cyan-sm animate-[pulse_2s_cubic-bezier(0.4,0,0.6,1)_infinite]"
      style={{ animationDuration: '3s' }}
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div className="flex items-center gap-3">
          <Zap className="text-cyan-500 animate-pulse" size={24} />
          <div>
            <h3 className="font-sans font-bold text-slate-800">Pipeline running...</h3>
            <p className="font-mono text-xs text-slate-500">ID: {experimentId}</p>
          </div>
        </div>

        <div className="font-mono text-xl font-bold text-cyan-700 bg-white px-4 py-2 rounded-lg border border-cyan-100 shadow-sm">
          {formatTime(elapsed)}
        </div>

        <Link href="/trace">
          <Button variant="outline" className="border-cyan-300 text-cyan-600 bg-white hover:bg-cyan-50 w-full md:w-auto">
            View Live Trace →
          </Button>
        </Link>
      </div>

      {/* Progress Dots */}
      <div className="flex items-center justify-between mt-6 px-2">
        {AGENT_STEPS.map((step, idx) => {
          const isDone = idx < activeIndex
          const isCurrent = idx === activeIndex
          
          return (
            <div key={step.id} className="flex flex-col items-center gap-2 relative z-10">
              <div className={`
                w-4 h-4 rounded-full transition-all duration-300
                ${isDone ? 'bg-emerald-400' : isCurrent ? 'bg-cyan-500 ring-4 ring-cyan-200 animate-pulse' : 'bg-slate-200'}
              `} />
              <span className={`hidden sm:block text-[10px] uppercase tracking-wider font-semibold ${isDone ? 'text-emerald-600' : isCurrent ? 'text-cyan-600' : 'text-slate-400'}`}>
                {step.name}
              </span>
            </div>
          )
        })}
        {/* Connector Line */}
        <div className="absolute left-[5%] right-[5%] h-0.5 bg-slate-200 -z-0 mt-[-24px] sm:mt-[-20px]">
          <div 
            className="h-full bg-emerald-400 transition-all duration-500"
            style={{ width: `${(activeIndex / (AGENT_STEPS.length - 1)) * 100}%` }}
          />
        </div>
      </div>
    </motion.div>
  )
}
