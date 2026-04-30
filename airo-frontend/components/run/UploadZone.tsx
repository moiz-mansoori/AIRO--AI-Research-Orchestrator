'use client'

import { useState, useCallback } from 'react'
import { UploadCloud, X } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface UploadZoneProps {
  onFileSelect: (file: File | null) => void
  selectedFile: File | null
}

export function UploadZone({ onFileSelect, selectedFile }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true)
    } else if (e.type === 'dragleave') {
      setIsDragging(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0])
    }
  }, [onFileSelect])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0])
    }
  }

  if (selectedFile) {
    return (
      <div className="flex items-center justify-between p-4 border border-cyan-200 bg-cyan-50/50 rounded-2xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-cyan-100 flex items-center justify-center text-cyan-600">
            <UploadCloud size={20} />
          </div>
          <div>
            <p className="font-mono text-sm font-medium text-cyan-800">{selectedFile.name}</p>
            <p className="font-sans text-[11px] text-cyan-600">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
          </div>
        </div>
        <Button variant="ghost" size="icon" onClick={() => onFileSelect(null)} className="text-cyan-600 hover:text-cyan-800 hover:bg-cyan-100">
          <X size={18} />
        </Button>
      </div>
    )
  }

  return (
    <div
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      className={`
        relative flex flex-col items-center justify-center w-full p-10 border-2 border-dashed rounded-2xl transition-all duration-200 ease-in-out
        ${isDragging 
          ? 'border-cyan-400 bg-cyan-50 scale-[1.01]' 
          : 'border-slate-200 bg-cyan-50/30 hover:bg-cyan-50/50 hover:border-cyan-200'
        }
      `}
    >
      <input
        type="file"
        accept=".csv,.parquet,.json"
        onChange={handleChange}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
      />
      <UploadCloud className={`mb-4 transition-colors ${isDragging ? 'text-cyan-500' : 'text-cyan-400'}`} size={40} />
      <h3 className="font-sans text-lg font-semibold text-slate-700 mb-1">Drop your dataset here</h3>
      <p className="font-sans text-xs text-slate-500 mb-6">CSV, Parquet, or JSON · Max 50MB</p>
      <Button variant="outline" className="border-cyan-300 text-cyan-600 bg-white hover:bg-cyan-50 pointer-events-none">
        Browse files
      </Button>
    </div>
  )
}
