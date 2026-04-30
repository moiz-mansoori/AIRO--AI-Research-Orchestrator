'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { DownloadCloud } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { airoApi } from '@/lib/api'

interface MarkdownViewerProps {
  content: string
  experimentId: string
}

export function MarkdownViewer({ content, experimentId }: MarkdownViewerProps) {
  
  const handleDownloadPdf = () => {
    window.open(airoApi.getReportPdfUrl(experimentId), '_blank')
  }

  return (
    <div className="w-full bg-white border border-cyan-100 rounded-2xl shadow-sm overflow-hidden">
      
      {/* Viewer Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-slate-50 border-b border-cyan-100">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-cyan-400" />
          <span className="font-mono text-sm font-semibold text-slate-700">airo_report.md</span>
        </div>
        <Button 
          onClick={handleDownloadPdf}
          variant="outline" 
          size="sm" 
          className="border-cyan-300 text-cyan-700 hover:bg-cyan-50 gap-2 h-8"
        >
          <DownloadCloud size={14} />
          <span className="text-xs">Download PDF</span>
        </Button>
      </div>

      {/* Markdown Content */}
      <div className="p-8 md:p-12 max-w-4xl mx-auto">
        <article className="prose prose-slate prose-cyan max-w-none 
          prose-headings:font-sans prose-headings:font-bold prose-headings:text-slate-800
          prose-h1:text-3xl prose-h1:mb-8 prose-h1:border-b prose-h1:pb-4 prose-h1:border-slate-200
          prose-h2:text-2xl prose-h2:mt-12 prose-h2:mb-6
          prose-h3:text-xl prose-h3:mt-8
          prose-p:font-sans prose-p:text-slate-600 prose-p:leading-relaxed
          prose-a:text-cyan-600 prose-a:no-underline hover:prose-a:underline
          prose-code:font-mono prose-code:text-cyan-700 prose-code:bg-cyan-50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md
          prose-pre:bg-slate-900 prose-pre:text-slate-200 prose-pre:shadow-lg
          prose-strong:text-slate-800
          prose-ul:text-slate-600 prose-li:marker:text-cyan-400
          prose-table:border-collapse prose-th:bg-slate-50 prose-th:p-3 prose-th:text-slate-700 prose-td:p-3 prose-td:border-t prose-td:border-slate-100
        ">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {content}
          </ReactMarkdown>
        </article>
      </div>
    </div>
  )
}
