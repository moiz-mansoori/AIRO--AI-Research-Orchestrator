'use client'

import { useEffect, useState } from 'react'
import { airoApi } from '@/lib/api'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  LineChart,
  Line,
  CartesianGrid,
  Legend,
} from 'recharts'
import { BarChart3, LineChart as LucideLineChart, Loader2, AlertCircle } from 'lucide-react'

interface InteractiveChartsProps {
  experimentId: string
}

interface ShapItem {
  feature: string
  importance: number
}

interface ChartMetrics {
  best_model_type: string
  best_run_id: string
  shap: ShapItem[]
  learning_curve: {
    train_sizes: number[]
    train_scores: number[]
    val_scores: number[]
  } | null
}

export function InteractiveCharts({ experimentId }: InteractiveChartsProps) {
  const [data, setData] = useState<ChartMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!experimentId) return

    setLoading(true)
    setError(false)

    airoApi.getReportCharts(experimentId)
      .then((res) => {
        setData(res)
        setLoading(false)
      })
      .catch(() => {
        setError(true)
        setLoading(false)
      })
  }, [experimentId])

  if (!mounted) return null

  if (loading) {
    return (
      <div className="w-full mt-6 p-12 bg-white border border-cyan-100 rounded-2xl flex flex-col items-center justify-center text-slate-400">
        <Loader2 className="animate-spin mb-3 text-cyan-600" size={24} />
        <span className="font-mono text-xs">Loading visualization metrics...</span>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="w-full mt-6 p-6 bg-amber-50/50 border border-amber-100 rounded-2xl flex items-start gap-3">
        <AlertCircle className="text-amber-600 mt-0.5 flex-shrink-0" size={18} />
        <div>
          <h4 className="font-sans font-bold text-sm text-slate-800">Legacy Experiment / Limited Data</h4>
          <p className="font-sans text-xs text-slate-600 mt-0.5">
            Chart data not available for this experiment — run a new experiment to generate interactive visual graphs.
          </p>
        </div>
      </div>
    )
  }

  // Format Learning Curve data for Recharts
  const learningCurveData = data.learning_curve
    ? data.learning_curve.train_sizes.map((size, idx) => ({
        size,
        train: data.learning_curve!.train_scores[idx],
        val: data.learning_curve!.val_scores[idx],
      }))
    : []

  // Reverse SHAP values so highest importance is at the top of the horizontal layout
  const shapData = [...data.shap].reverse()

  return (
    <div className="w-full mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      {/* SHAP Feature Importance Card */}
      <div className="bg-white border border-cyan-100 rounded-2xl shadow-sm overflow-hidden p-6 flex flex-col">
        <div className="flex items-center gap-2.5 mb-6 border-b border-cyan-50/50 pb-4">
          <div className="w-8 h-8 rounded-lg bg-cyan-50 flex items-center justify-center text-cyan-600">
            <BarChart3 size={16} />
          </div>
          <div>
            <h3 className="font-sans font-bold text-slate-800 text-sm">SHAP Feature Importances</h3>
            <p className="font-sans text-xs text-slate-400">Average impact on model outputs (magnitude)</p>
          </div>
        </div>

        <div className="h-[280px] w-full relative">
          {shapData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={shapData}
                layout="vertical"
                margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
              >
                <XAxis type="number" stroke="#94a3b8" fontSize={10} />
                <YAxis
                  dataKey="feature"
                  type="category"
                  stroke="#475569"
                  fontSize={10}
                  tickLine={false}
                  width={90}
                />
                <Tooltip
                  contentStyle={{
                    background: '#0f172a',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '11px',
                    color: '#fff',
                  }}
                  itemStyle={{ color: '#22d3ee' }}
                />
                <Bar dataKey="importance" fill="#0891b2" radius={[0, 4, 4, 0]} barSize={16} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="w-full h-full flex items-center justify-center text-slate-400 font-sans text-xs">
              SHAP analysis skipped/failed for this experiment run.
            </div>
          )}
        </div>
      </div>

      {/* Learning Curve Card */}
      <div className="bg-white border border-cyan-100 rounded-2xl shadow-sm overflow-hidden p-6 flex flex-col">
        <div className="flex items-center gap-2.5 mb-6 border-b border-cyan-50/50 pb-4">
          <div className="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600">
            <LucideLineChart size={16} />
          </div>
          <div>
            <h3 className="font-sans font-bold text-slate-800 text-sm">Learning Curves</h3>
            <p className="font-sans text-xs text-slate-400">Training vs. Validation performance progression</p>
          </div>
        </div>

        <div className="h-[280px] w-full relative">
          {learningCurveData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={learningCurveData}
                margin={{ top: 5, right: 10, left: -10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="size" stroke="#94a3b8" fontSize={10} />
                <YAxis stroke="#94a3b8" fontSize={10} domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{
                    background: '#0f172a',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '11px',
                    color: '#fff',
                  }}
                />
                <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: '11px' }} />
                <Line
                  type="monotone"
                  dataKey="train"
                  name="Training Score"
                  stroke="#4f46e5"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                />
                <Line
                  type="monotone"
                  dataKey="val"
                  name="Validation Score"
                  stroke="#059669"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="w-full h-full flex items-center justify-center text-slate-400 font-sans text-xs">
              Learning curve analysis skipped/failed for this experiment run.
            </div>
          )}
        </div>
      </div>

    </div>
  )
}
