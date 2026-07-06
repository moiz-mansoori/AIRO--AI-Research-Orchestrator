import axios from 'axios'
import { ExperimentResult } from '@/types/airo'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
})

export const airoApi = {
  runExperiment: async (formData: FormData) => {
    const res = await api.post<{ experiment_id: string }>('/api/run', formData)
    return res.data
  },

  getStatus: async (experimentId: string) => {
    const res = await api.get<{ status: 'running' | 'complete' | 'failed' | 'not_found', result?: ExperimentResult, errors?: string[] }>(`/api/status/${experimentId}`)
    return res.data
  },

  getExperiments: async () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const res = await api.get<any[]>('/api/experiments')
    return res.data
  },

  getReportMarkdown: async (experimentId: string) => {
    const res = await api.get<string>(`/api/report/${experimentId}/markdown`)
    return res.data
  },

  getReportCharts: async (experimentId: string) => {
    const res = await api.get<{
      best_model_type: string
      best_run_id: string
      shap: { feature: string; importance: number }[]
      learning_curve: {
        train_sizes: number[]
        train_scores: number[]
        val_scores: number[]
      } | null
    }>(`/api/report/${experimentId}/charts`)
    return res.data
  },

  getLogStreamUrl: (experimentId: string) => {
    return `${API_BASE_URL}/api/logs/${experimentId}`
  },

  getReportPdfUrl: (experimentId: string) => {
    return `${API_BASE_URL}/api/report/${experimentId}/pdf`
  }
}
