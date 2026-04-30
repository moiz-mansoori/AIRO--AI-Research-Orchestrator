'use client'

import { motion } from 'framer-motion'

export function PageWrapper({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="flex-1 w-full max-w-7xl mx-auto p-4 md:p-8"
    >
      {children}
    </motion.div>
  )
}
