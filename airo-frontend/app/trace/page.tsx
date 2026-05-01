'use client'

import { useEffect, useState } from 'react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { LogTerminal } from '@/components/trace/LogTerminal'
import { useExperimentStore } from '@/store/experimentStore'
import { airoApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Activity } from 'lucide-react'
import Link from 'next/link'

export default function TracePage() {
  const store = useExperimentStore()
  const [logs, setLogs] = useState<string[]>([])
  const [isListening, setIsListening] = useState(false)

  // Listen to SSE if experiment is running
  useEffect(() => {
    if (!store.experimentId) return

    // eslint-disable-next-line react-hooks/exhaustive-deps
    setIsListening(true)
    const eventSource = new EventSource(airoApi.getLogStreamUrl(store.experimentId))
    
    eventSource.onmessage = (e) => {
      setLogs(prev => [...prev, e.data])
      store.appendLog(e.data)
    }

    eventSource.onerror = () => {
      // Stream ended or connection lost
      eventSource.close()
      setIsListening(false)
    }

    return () => {
      eventSource.close()
      setIsListening(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [store.experimentId]) // Intentionally not including store.appendLog in deps

  // If no experiment is active or completed recently in this session, show empty state
  if (!store.experimentId && logs.length === 0) {
    return (
      <PageWrapper>
        <div className="w-full max-w-4xl mx-auto mt-20 text-center">
          <div className="w-16 h-16 rounded-full bg-cyan-50 text-cyan-500 flex items-center justify-center mx-auto mb-4">
            <Activity size={32} />
          </div>
          <h2 className="font-sans font-bold text-2xl text-slate-800 mb-2">No Active Trace</h2>
          <p className="font-sans text-slate-500 mb-8 max-w-md mx-auto">
            You are not currently running an experiment in this session. Start one to see live SSE log streaming.
          </p>
          <Link href="/run">
            <Button className="bg-cyan-600 hover:bg-cyan-700 text-white">
              Go to Run Experiment
            </Button>
          </Link>
        </div>
      </PageWrapper>
    )
  }

  return (
    <PageWrapper>
      <div className="max-w-6xl mx-auto w-full">
        <div className="flex items-end justify-between mb-6">
          <div>
            <h1 className="font-sans font-bold text-3xl text-slate-800 mb-2">Live Trace</h1>
            <p className="font-sans text-sm text-slate-500">
              Real-time stdout logs from the backend Agents.
            </p>
          </div>
          <div className="font-mono text-xs px-3 py-1 bg-white border border-slate-200 rounded-md text-slate-500">
            Experiment ID: <span className="font-bold text-cyan-600">{store.experimentId}</span>
          </div>
        </div>

        <LogTerminal logs={logs.length > 0 ? logs : store.logs} isRunning={isListening} />
      </div>
    </PageWrapper>
  )
}
