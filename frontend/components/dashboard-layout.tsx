'use client'

import React from "react"

import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/app-sidebar'
import { TopNavbar } from '@/components/top-navbar'
import { ReportDiseaseModal } from '@/components/report-disease-modal'

interface DashboardLayoutProps {
  children: React.ReactNode
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <TopNavbar />
        <main className="flex-1 overflow-auto">
          {children}
        </main>
        <ReportDiseaseModal />
      </SidebarInset>
    </SidebarProvider>
  )
}
