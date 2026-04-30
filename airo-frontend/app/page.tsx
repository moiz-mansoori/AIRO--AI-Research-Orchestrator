'use client'

import { useEffect, useState } from 'react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { MetricCard } from '@/components/dashboard/MetricCard'
import { AgentPipeline } from '@/components/dashboard/AgentPipeline'
import { ExperimentCard, EmptyExperimentCard } from '@/components/dashboard/ExperimentCard'
import { StatusBar } from '@/components/dashboard/StatusBar'
import { airoApi } from '@/lib/api'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

export interface ExperimentSummary {
  experiment_id: string;
  best_model_type: string;
  best_metric: number;
  verdict: 'PASS' | 'WARN' | 'FAIL';
  has_report: boolean;
}

export default function Home() {
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    airoApi.getExperiments().then(data => {
      setExperiments(data)
      setLoading(false)
    }).catch(() => {
      setLoading(false)
    })
  }, [])

  // Calculate simple stats
  const totalRuns = experiments.length
  const passedRuns = experiments.filter(e => e.verdict === 'PASS').length
  const avgMetric = totalRuns > 0 
    ? (experiments.reduce((sum, e) => sum + e.best_metric, 0) / totalRuns).toFixed(4)
    : '0.0000'

  return (
    <PageWrapper>
      
      {/* Hero Section */}
      <section className="relative w-full rounded-3xl p-8 md:p-12 mb-8 bg-gradient-to-br from-[#F0FDFC] via-[#ECFDF5] to-[#F8FFFE] border border-cyan-100 overflow-hidden shadow-sm">
        {/* Decorative blur */}
        <div className="absolute -top-24 -right-24 w-64 h-64 bg-cyan-400 opacity-15 blur-3xl rounded-full pointer-events-none" />
        
        <div className="relative z-10 max-w-2xl">
          <div className="inline-block px-3 py-1 mb-4 rounded-full bg-cyan-50 border border-cyan-200 text-cyan-600 text-[10px] font-bold tracking-widest uppercase">
            MULTI-AGENT
          </div>
          
          <h1 className="font-sans font-bold text-3xl md:text-4xl text-slate-800 mb-4 tracking-tight">
            AIRO — AI Research Orchestrator
          </h1>
          
          <p className="font-sans text-sm text-slate-500 mb-8 max-w-xl leading-relaxed">
            Automate your end-to-end Machine Learning experiments. 
            Upload a dataset, set a compute budget, and watch the multi-agent pipeline ingest, train, audit, and generate comprehensive research reports.
          </p>
          
          <Link href="/run">
            <Button className="bg-gradient-to-r from-cyan-500 to-cyan-600 text-white rounded-xl px-6 py-6 shadow-cyan-md hover:scale-105 hover:brightness-110 transition-all text-base font-medium">
              Run Experiment →
            </Button>
          </Link>
        </div>
      </section>

      {/* Metric Cards Grid */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <MetricCard 
          label="Total Experiments" 
          value={totalRuns} 
          subValue="Across all tasks" 
          gradientClass="from-cyan-500 to-indigo-500"
          delay={0.1}
        />
        <MetricCard 
          label="Critic Pass Rate" 
          value={`${totalRuns > 0 ? Math.round((passedRuns / totalRuns) * 100) : 0}%`} 
          subValue={`${passedRuns} of ${totalRuns} runs`} 
          gradientClass="from-emerald-400 to-cyan-400"
          delay={0.2}
        />
        <MetricCard 
          label="Avg Top Metric" 
          value={avgMetric} 
          subValue="Across all leaderboards" 
          gradientClass="from-amber-400 to-orange-400"
          delay={0.3}
        />
      </section>

      {/* Agent Pipeline Strip */}
      <section className="mb-10">
        <h2 className="font-sans font-semibold text-lg text-slate-800 mb-4">Pipeline Architecture</h2>
        <AgentPipeline />
      </section>

      {/* Recent Experiments */}
      <section className="mb-16">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-cyan-50 flex items-center justify-center text-cyan-600">
            <span className="font-mono text-sm">📅</span>
          </div>
          <h2 className="font-sans font-semibold text-lg text-slate-800">Recent Experiments</h2>
          <div className="flex-1 h-px bg-slate-200 ml-4" />
        </div>

        <div className="flex flex-col gap-3">
          {loading ? (
            <div className="p-8 text-center font-mono text-sm text-slate-400 animate-pulse">Loading experiments...</div>
          ) : experiments.length === 0 ? (
            <EmptyExperimentCard />
          ) : (
            experiments.map((exp, idx) => (
              <ExperimentCard 
                key={exp.experiment_id}
                experimentId={exp.experiment_id}
                bestModelType={exp.best_model_type}
                bestMetric={exp.best_metric}
                verdict={exp.verdict}
                hasReport={exp.has_report}
                delay={0.4 + (idx * 0.08)}
              />
            ))
          )}
        </div>
      </section>

      <StatusBar />
    </PageWrapper>
  )
}
