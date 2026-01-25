'use client'

import React, { useState, useEffect } from 'react'
import { KPICards } from '@/components/kpi-cards'
import { MapContainer } from '@/components/map-container'
import { LiveFeed } from '@/components/live-feed'
import { MortalityChart } from '@/components/mortality-chart'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { RefreshCw, Wifi, WifiOff, AlertTriangle } from 'lucide-react'
import { api, KPIData, DiseaseReport, MortalityTrend } from '@/lib/api'
import { useRealtimeData } from '@/hooks/use-realtime-data'

export function DashboardContent() {
  const [isOnline, setIsOnline] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [kpiData, setKpiData] = useState<KPIData | null>(null)
  const [reports, setReports] = useState<DiseaseReport[]>([])
  const [mortalityData, setMortalityData] = useState<MortalityTrend[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch data from backend
  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch KPI data
      const stats = await api.dashboard.getStats()
      const kpi: KPIData = {
        totalCases: stats.total_alerts,
        totalCasesTrend: [], // TODO: implement trend data
        activeClusters: stats.active_clusters,
        activeClustersTrend: [],
        mortalityRate: 0, // TODO: calculate from mortality data
        mortalityRateTrend: [],
        avgPriority: 0, // TODO: calculate from alerts
        avgPriorityTrend: [],
      }
      setKpiData(kpi)

      // Fetch alerts (reports)
      const alertsResponse = await api.alerts.getAll(50)
      const transformedReports: DiseaseReport[] = alertsResponse.alerts.map(alert => ({
        id: alert.id.toString(),
        disease_name: alert.disease_name,
        location: alert.location,
        region: 'Unknown', // TODO: map location to region
        coordinates: { lat: 0, lng: 0 }, // TODO: get coordinates from location
        reportedAt: new Date(alert.timestamp * 1000).toISOString(),
        priority: alert.priority_level as 1 | 2 | 3,
        priority_level: alert.priority_level,
        priority_name: alert.priority_name,
        status: alert.priority_level === 1 ? 'critical' : alert.priority_level === 2 ? 'escalated' : 'controlled',
        affectedCount: 0, // TODO: get from alert details
        mortalityCount: 0, // TODO: get from alert details
        reporter: alert.reporter_id,
        reporter_id: alert.reporter_id,
        species: 'Unknown', // TODO: get from alert details
        notes: JSON.stringify(alert.details),
        diseaseName: alert.disease_name,
        timestamp: alert.timestamp,
        cluster_boost: alert.cluster_boost,
        details: alert.details,
      }))
      setReports(transformedReports)

      // Fetch mortality data
      const mortalityStats = await api.mortality.getStats()
      // Transform mortality stats to trend data
      const trends: MortalityTrend[] = [
        {
          month: 'Current',
          cattle: Math.floor(mortalityStats.total * 0.6),
          poultry: Math.floor(mortalityStats.total * 0.25),
          swine: Math.floor(mortalityStats.total * 0.1),
          sheep: Math.floor(mortalityStats.total * 0.05),
        }
      ]
      setMortalityData(trends)

    } catch (err) {
      console.error('Failed to fetch dashboard data:', err)
      setError('Failed to load dashboard data. Please check your connection.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // Initial data fetch
    fetchData()

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await fetchData()
    setIsRefreshing(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading dashboard data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6 p-6">
        <Alert className="border-status-critical/50 bg-status-critical/10">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <div className="flex justify-center">
          <Button onClick={handleRefresh} variant="outline" className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      {/* Connection Status */}
      {!isOnline && (
        <Alert className="border-status-critical/50 bg-status-critical/10">
          <WifiOff className="h-4 w-4" />
          <AlertDescription>
            You are currently offline. Some features may not be available.
          </AlertDescription>
        </Alert>
      )}

      {/* KPI Cards */}
      {kpiData && <KPICards data={kpiData} />}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Map Container - Takes 2 columns on large screens */}
        <div className="lg:col-span-2">
          <MapContainer reports={reports} />
        </div>

        {/* Live Feed - Takes 1 column */}
        <div className="space-y-6">
          <LiveFeed reports={reports.slice(0, 10)} />
        </div>
      </div>

      {/* Mortality Chart */}
      {mortalityData.length > 0 && <MortalityChart data={mortalityData} />}

      {/* Refresh Button */}
      <div className="flex justify-center">
        <Button
          onClick={handleRefresh}
          disabled={isRefreshing || !isOnline}
          variant="outline"
          className="gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          {isRefreshing ? 'Refreshing...' : 'Refresh Data'}
        </Button>
      </div>
    </div>
  )
}
