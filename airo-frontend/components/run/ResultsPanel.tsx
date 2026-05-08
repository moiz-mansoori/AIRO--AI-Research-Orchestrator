'use client'

import { motion } from 'framer-motion'
import { CheckCircle2, DownloadCloud, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useExperimentStore } from '@/store/experimentStore'
import { MetricCard } from '@/components/dashboard/MetricCard'
import { airoApi } from '@/lib/api'

export function ResultsPanel() {
  const { result, errors, resetExperiment } = useExperimentStore()

  if (errors && errors.length > 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-red-50 border border-red-200 rounded-2xl p-6 shadow-sm flex flex-col items-start gap-4"
      >
        <div>
          <h2 className="font-sans font-bold text-xl text-red-900 mb-1">Experiment Failed</h2>
          <p className="font-sans text-sm text-red-700">The pipeline encountered an error and could not complete.</p>
        </div>
        
        <div className="bg-white rounded-lg border border-red-100 p-4 w-full">
          <ul className="list-disc pl-5 text-red-600 text-xs font-mono space-y-1">
            {errors.map((err, i) => <li key={i}>{err}</li>)}
          </ul>
        </div>

        <Button 
          onClick={resetExperiment}
          className="bg-red-600 hover:bg-red-700 text-white shadow-md gap-2"
        >
          <RefreshCw size={16} />
          Try Again
        </Button>
      </motion.div>
    )
  }

  if (!result) return null

  const handleDownloadPdf = () => {
    window.open(airoApi.getReportPdfUrl(result.experiment_id), '_blank')
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-4">
          <CheckCircle2 className="text-emerald-500" size={32} />
          <div>
            <h2 className="font-sans font-bold text-xl text-emerald-900">Experiment Complete</h2>
            <p className="font-mono text-xs text-emerald-700">ID: {result.experiment_id}</p>
          </div>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <Button 
            onClick={resetExperiment}
            variant="outline" 
            className="flex-1 md:flex-none border-emerald-300 text-emerald-700 hover:bg-emerald-100 gap-2"
          >
            <RefreshCw size={16} />
            Run Another
          </Button>
          <Button 
            onClick={handleDownloadPdf}
            className="flex-1 md:flex-none bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-md hover:brightness-110 gap-2"
          >
            <DownloadCloud size={16} />
            Download PDF
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard 
          label="Best Model" 
          value={result.best_model_type} 
          subValue={result.best_run_id} 
          gradientClass="from-cyan-500 to-indigo-500"
        />
        <MetricCard 
          label={`Top ${result.primary_metric_name}`} 
          value={result.leaderboard[0]?.primary_metric.toFixed(4) || '0.0000'} 
          subValue={`+${result.improvement_over_baseline_pct.toFixed(1)}% vs baseline`} 
          gradientClass="from-emerald-400 to-cyan-400"
          delay={0.1}
        />
        <MetricCard 
          label="Critic Audit" 
          value={result.leaderboard[0]?.verdict || 'N/A'} 
          subValue={`${result.critic_results.filter(c => c.verdict === 'PASS').length} passing models`} 
          gradientClass={result.leaderboard[0]?.verdict === 'PASS' ? 'from-emerald-400 to-teal-400' : 'from-amber-400 to-orange-400'}
          delay={0.2}
        />
      </div>

      {/* Re-use Leaderboard logic here if needed, or simply direct to leaderboard page */}
    </motion.div>
  )
}
