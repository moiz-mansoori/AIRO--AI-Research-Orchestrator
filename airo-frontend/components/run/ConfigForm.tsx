'use client'

import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'

interface ConfigFormProps {
  taskType: 'classification' | 'regression'
  setTaskType: (val: 'classification' | 'regression') => void
  targetColumn: string
  setTargetColumn: (val: string) => void
  budget: 'fast' | 'standard' | 'exhaustive'
  setBudget: (val: 'fast' | 'standard' | 'exhaustive') => void
  skipCurves: boolean
  setSkipCurves: (val: boolean) => void
  skipShap: boolean
  setSkipShap: (val: boolean) => void
}

export function ConfigForm({
  taskType, setTaskType,
  targetColumn, setTargetColumn,
  budget, setBudget,
  skipCurves, setSkipCurves,
  skipShap, setSkipShap
}: ConfigFormProps) {
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      
      {/* Left Column */}
      <div className="space-y-6">
        
        <div className="space-y-3">
          <Label className="font-sans font-semibold text-slate-700">Target Column</Label>
          <Input 
            placeholder="e.g. Outcome" 
            value={targetColumn}
            onChange={(e) => setTargetColumn(e.target.value)}
            className="border-slate-200 focus-visible:ring-cyan-400"
          />
          <p className="text-[11px] text-slate-500">Exact name of the column to predict.</p>
        </div>

        <div className="space-y-3">
          <Label className="font-sans font-semibold text-slate-700">Task Type</Label>
          <div className="flex items-center p-1 bg-slate-100 rounded-lg">
            <button
              type="button"
              onClick={() => setTaskType('classification')}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${taskType === 'classification' ? 'bg-cyan-500 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-200'}`}
            >
              Classification
            </button>
            <button
              type="button"
              onClick={() => setTaskType('regression')}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${taskType === 'regression' ? 'bg-cyan-500 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-200'}`}
            >
              Regression
            </button>
          </div>
        </div>
      </div>

      {/* Right Column */}
      <div className="space-y-6">
        
        <div className="space-y-3">
          <Label className="font-sans font-semibold text-slate-700">Compute Budget</Label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { id: 'fast', label: 'Fast', sub: '3 configs' },
              { id: 'standard', label: 'Standard', sub: '6 configs' },
              { id: 'exhaustive', label: 'Exhaustive', sub: '10 configs' },
            ].map((opt) => (
              <button
                key={opt.id}
                type="button"
                onClick={() => setBudget(opt.id as 'fast' | 'standard' | 'exhaustive')}
                className={`
                  flex flex-col items-center justify-center py-3 border rounded-xl transition-all
                  ${budget === opt.id 
                    ? 'border-cyan-400 bg-cyan-50 shadow-cyan-sm ring-1 ring-cyan-400' 
                    : 'border-slate-200 bg-white hover:border-cyan-200'
                  }
                `}
              >
                <span className={`text-sm font-medium ${budget === opt.id ? 'text-cyan-700' : 'text-slate-600'}`}>{opt.label}</span>
                <span className="text-[10px] text-slate-400">{opt.sub}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-4 pt-2">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-sm font-medium text-slate-700">Skip Learning Curves</Label>
              <p className="text-[11px] text-slate-500">Speeds up evaluator agent</p>
            </div>
            <Switch checked={skipCurves} onCheckedChange={setSkipCurves} className="data-[state=checked]:bg-cyan-500" />
          </div>
          
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-sm font-medium text-slate-700">Skip SHAP Analysis</Label>
              <p className="text-[11px] text-slate-500">Skips feature importance plotting</p>
            </div>
            <Switch checked={skipShap} onCheckedChange={setSkipShap} className="data-[state=checked]:bg-cyan-500" />
          </div>
        </div>

      </div>
    </div>
  )
}
