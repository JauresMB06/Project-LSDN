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

  // Fetch mortality data from API using Segment Tree range queries for July-November
  React.useEffect(() => {
    const fetchMortalityData = async () => {
      try {
        setMortalityLoading(true)
        // Fetch species data which includes mortality trends from Segment Tree
        const response = await api.analytics.getSpecies()
        // Convert to monthly format for July-November (months 6-10, 0-indexed as 181-334 days approximately)
        // For now, we'll use the species totals and distribute across months
        // In a full implementation, this would query specific date ranges from the Segment Tree
        const monthlyData = [
          { month: 'Jul', cattle: Math.floor(response.species_data[0]?.total_mortality * 0.2) || 0, poultry: Math.floor(response.species_data[1]?.total_mortality * 0.2) || 0, swine: Math.floor(response.species_data[2]?.total_mortality * 0.2) || 0, sheep: Math.floor(response.species_data[3]?.total_mortality * 0.2) || 0 },
          { month: 'Aug', cattle: Math.floor(response.species_data[0]?.total_mortality * 0.22) || 0, poultry: Math.floor(response.species_data[1]?.total_mortality * 0.22) || 0, swine: Math.floor(response.species_data[2]?.total_mortality * 0.22) || 0, sheep: Math.floor(response.species_data[3]?.total_mortality * 0.22) || 0 },
          { month: 'Sep', cattle: Math.floor(response.species_data[0]?.total_mortality * 0.18) || 0, poultry: Math.floor(response.species_data[1]?.total_mortality * 0.18) || 0, swine: Math.floor(response.species_data[2]?.total_mortality * 0.18) || 0, sheep: Math.floor(response.species_data[3]?.total_mortality * 0.18) || 0 },
          { month: 'Oct', cattle: Math.floor(response.species_data[0]?.total_mortality * 0.25) || 0, poultry: Math.floor(response.species_data[1]?.total_mortality * 0.25) || 0, swine: Math.floor(response.species_data[2]?.total_mortality * 0.25) || 0, sheep: Math.floor(response.species_data[3]?.total_mortality * 0.25) || 0 },
          { month: 'Nov', cattle: Math.floor(response.species_data[0]?.total_mortality * 0.15) || 0, poultry: Math.floor(response.species_data[1]?.total_mortality * 0.15) || 0, swine: Math.floor(response.species_data[2]?.total_mortality * 0.15) || 0, sheep: Math.floor(response.species_data[3]?.total_mortality * 0.15) || 0 },
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
