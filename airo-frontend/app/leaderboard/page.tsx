'use client'

import { PageWrapper } from '@/components/layout/PageWrapper'
import { LeaderboardTable } from '@/components/leaderboard/LeaderboardTable'
import { useExperimentStore } from '@/store/experimentStore'
import { Trophy } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function LeaderboardPage() {
  const { result } = useExperimentStore()

  if (!result) {
    return (
      <PageWrapper>
        <div className="w-full max-w-4xl mx-auto mt-20 text-center">
          <div className="w-16 h-16 rounded-full bg-cyan-50 text-amber-500 flex items-center justify-center mx-auto mb-4">
            <Trophy size={32} />
          </div>
          <h2 className="font-sans font-bold text-2xl text-slate-800 mb-2">No Leaderboard Available</h2>
          <p className="font-sans text-slate-500 mb-8 max-w-md mx-auto">
            You need to complete an experiment first to view the generated leaderboard and critic audit results.
          </p>
          <Link href="/run">
            <Button className="bg-cyan-600 hover:bg-cyan-700 text-white">
              Run Experiment
            </Button>
          </Link>
        </div>
      </PageWrapper>
    )
  }

  return (
    <PageWrapper>
      <div className="max-w-5xl mx-auto w-full">
        
        {/* Header Block */}
        <div className="bg-white border border-cyan-100 rounded-2xl p-6 md:p-8 mb-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-sm relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-amber-200 to-orange-100 opacity-20 blur-3xl rounded-full" />
          
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 mb-3 rounded-full bg-amber-50 border border-amber-200 text-amber-600 text-[10px] font-bold tracking-widest uppercase">
              <Trophy size={12} />
              Final Results
            </div>
            <h1 className="font-sans font-bold text-3xl text-slate-800 mb-2">
              Model Leaderboard
            </h1>
            <p className="font-mono text-sm text-slate-500">
              Experiment ID: {result.experiment_id}
            </p>
          </div>

          <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 min-w-[200px]">
            <p className="font-sans text-[11px] font-semibold uppercase tracking-wide text-slate-400 mb-1">
              Top Performance
            </p>
            <p className="font-mono text-2xl font-bold text-emerald-600">
              +{result.improvement_over_baseline_pct.toFixed(2)}%
            </p>
            <p className="font-sans text-xs text-slate-500">improvement over baseline</p>
          </div>
        </div>

        <LeaderboardTable 
          entries={result.leaderboard} 
          metricName={result.primary_metric_name.toUpperCase()} 
        />
        
      </div>
    </PageWrapper>
  )
}
