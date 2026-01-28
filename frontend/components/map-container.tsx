'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { MapPin, Search, ZoomIn, ZoomOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import type { DiseaseReport } from '@/lib/api'
import type { ClusterMapData } from '@/lib/api'

// Dynamically import Leaflet components to avoid SSR issues
const LeafletMapContainer = dynamic(() => import('react-leaflet').then(mod => mod.MapContainer), {
  ssr: false,
  loading: () => <div className="flex items-center justify-center h-full">Loading map...</div>
})
const TileLayer = dynamic(() => import('react-leaflet').then(mod => mod.TileLayer), {
  ssr: false
})
const Marker = dynamic(() => import('react-leaflet').then(mod => mod.Marker), {
  ssr: false
})
const Popup = dynamic(() => import('react-leaflet').then(mod => mod.Popup), {
  ssr: false
})

interface MapContainerProps {
  reports: DiseaseReport[]
  clusters?: ClusterMapData[]
}

export function MapContainer({ reports, clusters = [] }: MapContainerProps) {
  const [L, setL] = useState<any>(null)

  // Load Leaflet dynamically on client side
  useEffect(() => {
    import('leaflet').then((leaflet) => {
      // Fix for default markers
      delete (leaflet.Icon.Default.prototype as any)._getIconUrl
      leaflet.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
        iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
      })
      setL(leaflet)
    })
  }, [])

  // Count reports by status for the legend
  const criticalCount = reports.filter((r) => r.status === 'critical').length
  const escalatedCount = reports.filter((r) => r.status === 'escalated').length
  const controlledCount = reports.filter((r) => r.status === 'controlled').length

  // Count clusters by risk level
  const highRiskCount = clusters.filter((c) => c.risk === 'HIGH').length
  const mediumRiskCount = clusters.filter((c) => c.risk === 'MEDIUM').length
  const lowRiskCount = clusters.filter((c) => c.risk === 'LOW').length

  // Use clusters if available, otherwise fall back to reports
  const displayClusters = clusters.length > 0 ? clusters : []

  if (!L) {
    return (
      <Card className="relative flex h-[500px] flex-col overflow-hidden border-border/50 bg-card/50 p-0">
        <div className="flex flex-1 items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading interactive map...</p>
          </div>
        </div>
      </Card>
    )
  }

  return (
    <Card className="relative flex h-[500px] flex-col overflow-hidden border-border/50 bg-card/50 p-0">
      {/* Floating Search Bar */}
      <div className="absolute left-4 right-4 top-4 z-10">
        <div className="relative max-w-xs">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search locations..."
            className="h-9 bg-background/90 pl-9 backdrop-blur-sm"
          />
        </div>
      </div>

      {/* Leaflet Map */}
      <div className="flex-1">
        <LeafletMapContainer
          center={[7.3697, 12.3547]} // Center of Cameroon
          zoom={6}
          className="h-full w-full"
          zoomControl={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Render clusters or individual reports as markers */}
          {displayClusters.length > 0 ? (
            displayClusters.slice(0, 20).map((cluster) => {
              // Use cluster center coordinates
              const position: [number, number] = cluster.center || [7.3697, 12.3547]
              const colors = {
                HIGH: '#ef4444', // red-500
                MEDIUM: '#eab308', // yellow-500
                LOW: '#22c55e', // green-500
              }

              return (
                <Marker
                  key={cluster.cluster_id}
                  position={position}
                  icon={new L.Icon({
                    iconUrl: `data:image/svg+xml;base64,${btoa(`
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="10" fill="${colors[cluster.risk as keyof typeof colors]}" stroke="white" stroke-width="2"/>
                        <text x="12" y="16" text-anchor="middle" fill="white" font-size="12" font-weight="bold">${cluster.size}</text>
                      </svg>
                    `)}`,
                    iconSize: [24, 24],
                    iconAnchor: [12, 24],
                    popupAnchor: [0, -24],
                  })}
                >
                  <Popup>
                    <div className="p-2">
                      <h3 className="font-semibold">Cluster {cluster.cluster_id}</h3>
                      <p className="text-sm">Risk Level: {cluster.risk}</p>
                      <p className="text-sm">Locations: {cluster.locations.join(', ')}</p>
                      <p className="text-sm">Total Alerts: {cluster.alert_count}</p>
                      <p className="text-sm">Critical: {cluster.critical_count}</p>
                    </div>
                  </Popup>
                </Marker>
              )
            })
          ) : (
            // Render individual reports
            reports.slice(0, 50).map((report) => {
              // Use coordinates if available, otherwise use default Cameroon center with slight randomization
              const position: [number, number] = report.coordinates?.lat && report.coordinates?.lng
                ? [report.coordinates.lat, report.coordinates.lng]
                : [
                    7.3697 + (Math.random() - 0.5) * 4, // Random lat within Cameroon
                    12.3547 + (Math.random() - 0.5) * 6  // Random lng within Cameroon
                  ]

              const colors = {
                critical: '#dc2626', // red-600
                escalated: '#d97706', // amber-600
                controlled: '#16a34a', // green-600
              }

              return (
                <Marker
                  key={report.id}
                  position={position}
                  icon={new L.Icon({
                    iconUrl: `data:image/svg+xml;base64,${btoa(`
                      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="10" cy="10" r="8" fill="${colors[report.status]}" stroke="white" stroke-width="2"/>
                      </svg>
                    `)}`,
                    iconSize: [20, 20],
                    iconAnchor: [10, 20],
                    popupAnchor: [0, -20],
                  })}
                >
                  <Popup>
                    <div className="p-2">
                      <h3 className="font-semibold">{report.diseaseName}</h3>
                      <p className="text-sm">Location: {report.location}</p>
                      <p className="text-sm">Status: {report.status}</p>
                      <p className="text-sm">Priority: {report.priority}</p>
                      <p className="text-sm">Reported: {new Date(report.reportedAt).toLocaleDateString()}</p>
                    </div>
                  </Popup>
                </Marker>
              )
            })
          )}
        </LeafletMapContainer>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-between border-t border-border bg-background/50 px-4 py-2">
        <div className="flex items-center gap-4 text-xs">
          {displayClusters.length > 0 ? (
            <>
              <div className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-full bg-red-500" />
                <span className="text-muted-foreground">High Risk ({highRiskCount})</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-full bg-yellow-500" />
                <span className="text-muted-foreground">Medium Risk ({mediumRiskCount})</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-full bg-green-500" />
                <span className="text-muted-foreground">Low Risk ({lowRiskCount})</span>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-full bg-status-critical" />
                <span className="text-muted-foreground">Critical ({criticalCount})</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-full bg-status-escalated" />
                <span className="text-muted-foreground">Escalated ({escalatedCount})</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-full bg-status-controlled" />
                <span className="text-muted-foreground">Controlled ({controlledCount})</span>
              </div>
            </>
          )}
        </div>
        <span className="text-xs text-muted-foreground">
          {displayClusters.length > 0 ? `${displayClusters.length} Active Clusters` : `${reports.length} Active Reports`}
        </span>
      </div>
    </Card>
  )
}
