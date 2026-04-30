'use client'

import { motion } from 'framer-motion'

interface MetricCardProps {
  label: string
  value: string | number
  subValue: string
  gradientClass: string
  delay?: number
}

export function MetricCard({ label, value, subValue, gradientClass, delay = 0 }: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay, ease: 'easeOut' }}
      className="relative bg-white border border-cyan-100 rounded-2xl p-5 hover:-translate-y-0.5 hover:shadow-cyan-md hover:border-cyan-200 transition-all duration-200 overflow-hidden"
    >
      <div className={`absolute top-0 left-0 w-full h-[3px] bg-gradient-to-r ${gradientClass}`} />
      
      <p className="font-sans text-[11px] font-semibold uppercase tracking-wide text-slate-400 mb-2">
        {label}
      </p>
      
      <p className="font-sans text-[32px] font-bold text-slate-800 leading-none mb-1">
        {value}
      </p>
      
      <p className="font-mono text-xs text-slate-400">
        {subValue}
      </p>
    </motion.div>
  )
}
