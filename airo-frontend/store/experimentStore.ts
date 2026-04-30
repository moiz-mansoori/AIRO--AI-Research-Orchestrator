import { create } from 'zustand'
import { ExperimentResult } from '@/types/airo'

interface ExperimentState {
  running: boolean
  done: boolean
  experimentId: string | null
  startTime: number | null
  result: ExperimentResult | null
  errors: string[]
  logs: string[]
  
  startExperiment: (id: string) => void
  appendLog: (line: string) => void
  finishExperiment: (result: ExperimentResult) => void
  failExperiment: (errors: string[]) => void
  resetExperiment: () => void
}

export const useExperimentStore = create<ExperimentState>((set) => ({
  running: false,
  done: false,
  experimentId: null,
  startTime: null,
  result: null,
  errors: [],
  logs: [],

  startExperiment: (id) => set({
    running: true,
    done: false,
    experimentId: id,
    startTime: Date.now(),
    result: null,
    errors: [],
    logs: []
  }),

  appendLog: (line) => set((state) => ({
    logs: [...state.logs, line]
  })),

  finishExperiment: (result) => set({
    running: false,
    done: true,
    result
  }),

  failExperiment: (errors) => set({
    running: false,
    done: true,
    errors
  }),

  resetExperiment: () => set({
    running: false,
    done: false,
    experimentId: null,
    startTime: null,
    result: null,
    errors: [],
    logs: []
  })
}))
