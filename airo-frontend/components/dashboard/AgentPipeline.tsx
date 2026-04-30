'use client'

import { ChevronRight } from 'lucide-react'

const AGENTS = [
  { id: 1, name: 'Data Agent', role: 'Ingest & QA' },
  { id: 2, name: 'Config Agent', role: 'Hyperparameters' },
  { id: 3, name: 'Training Agent', role: 'AutoML execution' },
  { id: 4, name: 'Critic Agent', role: 'Audit & Critique' },
  { id: 5, name: 'Evaluator Agent', role: 'Select Best Model' },
  { id: 6, name: 'Reporter Agent', role: 'Generate Insights' },
]

export function AgentPipeline({ activeAgent = '' }: { activeAgent?: string }) {
  return (
    <div className="w-full overflow-x-auto pb-4 hide-scrollbar">
      <div className="flex items-center gap-2 min-w-max">
        {AGENTS.map((agent, idx) => {
          const isActive = activeAgent.toLowerCase().includes(agent.name.split(' ')[0].toLowerCase())
          
          return (
            <div key={agent.id} className="flex items-center gap-2">
              <div 
                className={`
                  flex flex-col px-4 py-3 rounded-xl border transition-all duration-300
                  ${isActive 
                    ? 'border-cyan-400 bg-cyan-50 shadow-cyan-glow' 
                    : 'border-cyan-100 bg-white'
                  }
                `}
              >
                <span className={`font-mono text-[10px] ${isActive ? 'text-cyan-500' : 'text-cyan-400'}`}>
                  0{agent.id}
                </span>
                <span className="font-sans text-[13px] font-semibold text-slate-700 leading-tight">
                  {agent.name}
                </span>
                <span className="font-sans text-[11px] text-slate-400">
                  {agent.role}
                </span>
              </div>
              
              {idx < AGENTS.length - 1 && (
                <ChevronRight className="text-cyan-300" size={16} />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
