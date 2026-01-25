'use client'

import * as React from 'react'
import { CalendarDays, Download, RefreshCw, AlertTriangle } from 'lucide-react'

import { DashboardLayout } from '@/components/dashboard-layout'
import {
  DiseaseDistributionChart,
  RegionalOutbreaksChart,
  TimeSeriesChart,
  SpeciesImpactChart,
  ResponseMetrics,
} from '@/components/analytics-charts'
import { MortalityChart } from '@/components/mortality-chart'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useRealtimeData } from '@/hooks/use-realtime-data'
import { api } from '@/lib/api'

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = React.useState('30d')
  const { stats, alerts, clusters, loading, error, refresh } = useRealtimeData({
    pollInterval: 30000, // Refresh every 30 seconds
  })

  const [mortalityData, setMortalityData] = React.useState<any[]>([])
  const [mortalityLoading, setMortalityLoading] = React.useState(true)
  const [isRefreshing, setIsRefreshing] = React.useState(false)

  // Fetch mortality data from API
  React.useEffect(() => {
    const fetchMortalityData = async () => {
      try {
        setMortalityLoading(true)
        const response = await api.mortality.getStats()
        // Convert API response to chart format
        // For now, create sample monthly data based on totals
        const monthlyData = [
          { month: 'Jan', cattle: Math.floor(response.total * 0.4), poultry: Math.floor(response.total * 0.35), swine: Math.floor(response.total * 0.15), sheep: Math.floor(response.total * 0.1) },
          { month: 'Feb', cattle: Math.floor(response.total * 0.42), poultry: Math.floor(response.total * 0.33), swine: Math.floor(response.total * 0.17), sheep: Math.floor(response.total * 0.08) },
          { month: 'Mar', cattle: Math.floor(response.total * 0.38), poultry: Math.floor(response.total * 0.37), swine: Math.floor(response.total * 0.13), sheep: Math.floor(response.total * 0.12) },
          { month: 'Apr', cattle: Math.floor(response.total * 0.45), poultry: Math.floor(response.total * 0.32), swine: Math.floor(response.total * 0.16), sheep: Math.floor(response.total * 0.07) },
          { month: 'May', cattle: Math.floor(response.total * 0.41), poultry: Math.floor(response.total * 0.36), swine: Math.floor(response.total * 0.14), sheep: Math.floor(response.total * 0.09) },
          { month: 'Jun', cattle: Math.floor(response.total * 0.43), poultry: Math.floor(response.total * 0.34), swine: Math.floor(response.total * 0.18), sheep: Math.floor(response.total * 0.05) },
        ]
        setMortalityData(monthlyData)
      } catch (err) {
        console.error('Failed to fetch mortality data:', err)
        // Set empty data if API fails
        setMortalityData([])
      } finally {
        setMortalityLoading(false)
      }
    }

    fetchMortalityData()
  }, [])

  const handleRefresh = () => {
    setIsRefreshing(true)
    refresh()
    // Re-fetch mortality data
    window.location.reload()
  }

  if (loading && !stats) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Loading analytics data...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="container mx-auto space-y-6 p-4 pb-24 md:p-6">
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
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto space-y-6 p-4 pb-24 md:p-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-col gap-1">
            <h1 className="text-2xl font-bold tracking-tight text-balance md:text-3xl">
              Analytics
            </h1>
            <p className="text-sm text-muted-foreground">
              Comprehensive insights into disease surveillance data
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Select value={dateRange} onValueChange={setDateRange}>
              <SelectTrigger className="w-[140px] bg-background/50">
                <CalendarDays className="mr-2 size-4" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7d">Last 7 days</SelectItem>
                <SelectItem value="30d">Last 30 days</SelectItem>
                <SelectItem value="90d">Last 90 days</SelectItem>
                <SelectItem value="1y">Last year</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="icon" onClick={handleRefresh} disabled={isRefreshing}>
              <RefreshCw className={`size-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span className="sr-only">Refresh data</span>
            </Button>
            <Button variant="outline" size="sm">
              <Download className="mr-2 size-4" />
              Export
            </Button>
          </div>
        </div>

        {/* Response Metrics */}
        <section aria-labelledby="metrics-heading">
          <h2 id="metrics-heading" className="sr-only">Response Metrics</h2>
          <ResponseMetrics />
        </section>

        {/* Charts Row 1 */}
        <section aria-labelledby="trends-heading" className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <h2 id="trends-heading" className="sr-only">Trend Analysis</h2>
          <TimeSeriesChart />
          <DiseaseDistributionChart />
        </section>

        {/* Charts Row 2 */}
        <section aria-labelledby="regional-heading" className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <h2 id="regional-heading" className="sr-only">Regional and Species Analysis</h2>
          <RegionalOutbreaksChart />
          <SpeciesImpactChart />
        </section>

        {/* Mortality Trends */}
        <section aria-labelledby="mortality-heading">
          <h2 id="mortality-heading" className="sr-only">Mortality Trends</h2>
          <MortalityChart data={mortalityData} />
        </section>
      </div>
    </DashboardLayout>
  )
}
