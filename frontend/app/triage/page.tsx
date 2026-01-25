'use client'

import * as React from 'react'
import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { AlertTriangle, Clock, Users, Activity, RefreshCw } from 'lucide-react'
import { TriageTable } from '@/components/triage-table'
import type { DiseaseReport } from '@/lib/api'

export default function TriagePage() {
  const [reports, setReports] = useState<DiseaseReport[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch triage data from the new API endpoint
  useEffect(() => {
    const fetchTriageData = async () => {
      try {
        setLoading(true)
        // Use the new triage endpoint
        const response = await fetch('http://localhost:8000/api/triage?limit=50')
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        const data = await response.json()

        // Convert API response to DiseaseReport format
        const formattedReports: DiseaseReport[] = data.map((alert: any) => ({
          id: alert.id.toString(),
          diseaseName: alert.disease_name,
          location: alert.location,
          region: alert.location,
          coordinates: { lat: 0, lng: 0 },
          reportedAt: new Date(alert.timestamp * 1000).toISOString(),
          priority: alert.priority_level as 1 | 2 | 3,
          status: alert.priority_level === 1 ? 'critical' :
                  alert.priority_level === 2 ? 'escalated' : 'controlled',
          affectedCount: 1,
          mortalityCount: 0,
          reporter: alert.reporter_id,
          species: 'Unknown'
        }))

        setReports(formattedReports)
      } catch (err) {
        console.error('Failed to fetch triage data:', err)
        setError('Failed to load triage data. Please check if the backend is running.')
        setReports([])
      } finally {
        setLoading(false)
      }
    }

    fetchTriageData()
  }, [])

  const handleStatusChange = (id: string, newStatus: DiseaseReport['status']) => {
    setReports(prev => prev.map(report =>
      report.id === id ? { ...report, status: newStatus } : report
    ))
  }

  const handleViewReport = (report: DiseaseReport) => {
    console.log('View report:', report)
  }

  // Calculate statistics
  const criticalCount = reports.filter(r => r.status === 'critical').length
  const escalatedCount = reports.filter(r => r.status === 'escalated').length
  const controlledCount = reports.filter(r => r.status === 'controlled').length

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading triage data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6 p-6">
        <div className="border border-red-200 bg-red-50 p-4 rounded-lg">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
            <h3 className="text-red-800 font-medium">Error Loading Data</h3>
          </div>
          <p className="text-red-700 mt-2">{error}</p>
          <Button
            onClick={() => window.location.reload()}
            variant="outline"
            className="mt-4"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Triage Center</h1>
          <p className="text-muted-foreground">
            Monitor and prioritize disease outbreak alerts
          </p>
        </div>
        <Button onClick={() => window.location.reload()} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Statistics Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Alerts</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{reports.length}</div>
            <p className="text-xs text-muted-foreground">
              Active disease reports
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical</CardTitle>
            <AlertTriangle className="h-4 w-4 text-status-critical" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-status-critical">{criticalCount}</div>
            <p className="text-xs text-muted-foreground">
              Require immediate action
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Escalated</CardTitle>
            <Clock className="h-4 w-4 text-status-escalated" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-status-escalated">{escalatedCount}</div>
            <p className="text-xs text-muted-foreground">
              Need attention soon
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Controlled</CardTitle>
            <Users className="h-4 w-4 text-status-controlled" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-status-controlled">{controlledCount}</div>
            <p className="text-xs text-muted-foreground">
              Under monitoring
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Triage Table */}
      <Card>
        <CardHeader>
          <CardTitle>Alert Triage Queue</CardTitle>
          <CardDescription>
            Review and prioritize disease outbreak alerts. Critical alerts require immediate response.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <TriageTable
            reports={reports}
            onStatusChange={handleStatusChange}
            onViewReport={handleViewReport}
          />
        </CardContent>
      </Card>
    </div>
  )
}
