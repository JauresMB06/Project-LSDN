import { useState, useEffect, useCallback } from 'react'
import { api, DashboardStats, Alert, ClusterMapData } from '@/lib/api'

interface RealtimeData {
  stats: DashboardStats | null
  alerts: Alert[]
  clusters: ClusterMapData[]
  loading: boolean
  error: string | null
  lastUpdated: Date | null
}

interface UseRealtimeDataOptions {
  enabled?: boolean
  pollInterval?: number // in milliseconds
  onDataUpdate?: (data: RealtimeData) => void
}

export function useRealtimeData(options: UseRealtimeDataOptions = {}) {
  const {
    enabled = true,
    pollInterval = 30000, // 30 seconds default
    onDataUpdate,
  } = options

  const [data, setData] = useState<RealtimeData>({
    stats: null,
    alerts: [],
    clusters: [],
    loading: true,
    error: null,
    lastUpdated: null,
  })

  const fetchData = useCallback(async () => {
    if (!enabled) return

    try {
      setData(prev => ({ ...prev, loading: true, error: null }))

      // Fetch all data in parallel
      const [stats, alertsResponse, clusters] = await Promise.all([
        api.dashboard.getStats(),
        api.alerts.getAll(50), // Get latest 50 alerts
        api.map.getClusters(),
      ])

      const newData: RealtimeData = {
        stats,
        alerts: alertsResponse.alerts,
        clusters,
        loading: false,
        error: null,
        lastUpdated: new Date(),
      }

      setData(newData)
      onDataUpdate?.(newData)
    } catch (error) {
      console.error('Failed to fetch realtime data:', error)
      setData(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to fetch latest data',
      }))
    }
  }, [enabled, onDataUpdate])

  // Initial fetch
  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Set up polling
  useEffect(() => {
    if (!enabled || pollInterval <= 0) return

    const interval = setInterval(fetchData, pollInterval)

    return () => clearInterval(interval)
  }, [enabled, pollInterval, fetchData])

  // Manual refresh function
  const refresh = useCallback(() => {
    fetchData()
  }, [fetchData])

  return {
    ...data,
    refresh,
  }
}
