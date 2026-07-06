'use client'

import { Menu, Microscope } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from '@/components/ui/sheet'
import { Sidebar } from './Sidebar'

export function TopBar() {
  return (
    <header className="md:hidden flex items-center justify-between h-14 px-4 bg-white border-b border-slate-200/60 shadow-sm sticky top-0 z-50">
      
      <div className="flex items-center gap-2">
        <div className="w-6 h-6 rounded-full bg-gradient-to-br from-cyan-400 to-cyan-600 flex items-center justify-center text-white shadow-sm">
          <Microscope size={14} />
        </div>
        <span className="font-sans font-bold text-slate-800">AIRO</span>
      </div>

      <Sheet>
        <SheetTrigger 
          render={
            <Button variant="ghost" size="icon" className="text-slate-600" />
          }
        >
          <Menu size={20} />
          <span className="sr-only">Toggle Menu</span>
        </SheetTrigger>
        <SheetContent side="left" className="p-0 w-64 border-r-slate-200">
          <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
          {/* Reuse the sidebar layout but forced block so it renders inside the sheet correctly */}
          <div className="h-full flex flex-col [&>aside]:flex [&>aside]:w-full [&>aside]:border-none [&>aside]:h-full">
            <Sidebar />
          </div>
        </SheetContent>
      </Sheet>

    </header>
  )
}
