'use client'

import { useState, useEffect } from 'react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { UploadZone } from '@/components/run/UploadZone'
import { ConfigForm } from '@/components/run/ConfigForm'
import { RunningBanner } from '@/components/run/RunningBanner'
import { ResultsPanel } from '@/components/run/ResultsPanel'
import { Button } from '@/components/ui/button'
import { useExperimentStore } from '@/store/experimentStore'
import { airoApi } from '@/lib/api'
import { Loader2 } from 'lucide-react'

export default function RunExperimentPage() {
  const [file, setFile] = useState<File | null>(null)
  const [taskType, setTaskType] = useState<'classification'|'regression'>('classification')
  const [targetColumn, setTargetColumn] = useState('')
  const [budget, setBudget] = useState<'fast'|'standard'|'exhaustive'>('standard')
  const [skipCurves, setSkipCurves] = useState(false)
  const [skipShap, setSkipShap] = useState(false)
  
  const [isLaunching, setIsLaunching] = useState(false)

  const store = useExperimentStore()

  // Polling logic when running
  useEffect(() => {
    let interval: NodeJS.Timeout
    if (store.running && store.experimentId) {
      interval = setInterval(async () => {
        try {
          const res = await airoApi.getStatus(store.experimentId!)
          if (res.status === 'complete' && res.result) {
            store.finishExperiment(res.result)
          } else if (res.status === 'failed') {
            store.failExperiment(res.errors || ['Unknown error occurred'])
          }
        } catch (e) {
          console.error("Failed to poll status", e)
        }
      }, 3000) // Poll every 3 seconds
    }
    return () => clearInterval(interval)
  }, [store.running, store.experimentId, store])

  const handleLaunch = async () => {
    if (!file || !targetColumn) return
    setIsLaunching(true)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('task_type', taskType)
    formData.append('target_column', targetColumn)
    formData.append('compute_budget', budget)
    formData.append('skip_curves', skipCurves.toString())
    formData.append('skip_shap', skipShap.toString())

    try {
      const res = await airoApi.runExperiment(formData)
      store.startExperiment(res.experiment_id)
    } catch (e) {
      alert("Failed to launch experiment. Ensure backend is running.")
    } finally {
      setIsLaunching(false)
    }
  }

  const canLaunch = !!file && !!targetColumn

  return (
    <PageWrapper>
      <div className="max-w-4xl mx-auto w-full">
        <h1 className="font-sans font-bold text-3xl text-slate-800 mb-2">Run Experiment</h1>
        <p className="font-sans text-sm text-slate-500 mb-8">
          Upload a structured dataset and configure the AIRO multi-agent pipeline.
        </p>

        {store.running && <RunningBanner />}
        {store.done && <ResultsPanel />}

        {!store.running && !store.done && (
          <div className="bg-white rounded-2xl border border-cyan-100 p-6 md:p-8 shadow-sm">
            <div className="mb-8">
              <UploadZone onFileSelect={setFile} selectedFile={file} />
            </div>

            <div className="mb-8">
              <ConfigForm 
                taskType={taskType} setTaskType={setTaskType}
                targetColumn={targetColumn} setTargetColumn={setTargetColumn}
                budget={budget} setBudget={setBudget}
                skipCurves={skipCurves} setSkipCurves={setSkipCurves}
                skipShap={skipShap} setSkipShap={setSkipShap}
              />
            </div>

            <div className="pt-6 border-t border-slate-100">
              <Button 
                className="w-full py-6 text-lg font-medium rounded-xl transition-all shadow-cyan-md hover:scale-[1.01]"
                style={{
                  background: canLaunch ? 'linear-gradient(135deg, #06B6D4, #0891B2)' : '#F1F5F9',
                  color: canLaunch ? 'white' : '#94A3B8'
                }}
                disabled={!canLaunch || isLaunching}
                onClick={handleLaunch}
              >
                {isLaunching ? (
                  <><Loader2 className="mr-2 animate-spin" /> Launching Pipeline...</>
                ) : (
                  '▶ Launch AIRO Pipeline'
                )}
              </Button>
            </div>
          </div>
        )}
      </div>
    </PageWrapper>
  )
}
