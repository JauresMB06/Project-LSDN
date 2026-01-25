'use client'

import * as React from 'react'
import {
  Activity,
  CheckCircle2,
  Clock,
  Database,
  Globe,
  RefreshCw,
  Server,
  Shield,
  Wifi,
  XCircle,
  AlertTriangle,
  Zap,
} from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'

import { DashboardLayout } from '@/components/dashboard-layout'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'

// Mock system health data
const mockHealthData = {
  status: 'operational' as const,
  uptime: 99.97,
  lastSync: new Date().toISOString(),
  services: [
    { name: 'API Gateway', status: 'healthy' as const, latency: 45, lastCheck: new Date().toISOString(), icon: Globe },
    { name: 'Database', status: 'healthy' as const, latency: 12, lastCheck: new Date().toISOString(), icon: Database },
    { name: 'Auth Service', status: 'healthy' as const, latency: 28, lastCheck: new Date().toISOString(), icon: Shield },
    { name: 'Notification Service', status: 'warning' as const, latency: 180, lastCheck: new Date().toISOString(), icon: Wifi },
    { name: 'Map Service', status: 'healthy' as const, latency: 65, lastCheck: new Date().toISOString(), icon: Activity },
    { name: 'Analytics Engine', status: 'healthy' as const, latency: 92, lastCheck: new Date().toISOString(), icon: Zap },
  ],
  metrics: {
    apiRequests24h: 45892,
    averageLatency: 67,
    errorRate: 0.12,
    activeConnections: 234,
  },
}

function StatusIcon({ status }: { status: 'healthy' | 'warning' | 'error' }) {
  if (status === 'healthy') {
    return <CheckCircle2 className="size-5 text-status-controlled" />
  }
  if (status === 'warning') {
    return <AlertTriangle className="size-5 text-status-escalated" />
  }
  return <XCircle className="size-5 text-status-critical" />
}

function OverallStatusBadge({ status }: { status: 'operational' | 'degraded' | 'outage' }) {
  const variants = {
    operational: 'bg-status-controlled/20 text-status-controlled border-status-controlled/30',
    degraded: 'bg-status-escalated/20 text-status-escalated border-status-escalated/30',
    outage: 'bg-status-critical/20 text-status-critical border-status-critical/30',
  }

  const labels = {
    operational: 'All Systems Operational',
    degraded: 'Partial System Degradation',
    outage: 'Major System Outage',
  }

  return (
    <Badge variant="outline" className={`text-sm ${variants[status]}`}>
      {status === 'operational' && <CheckCircle2 className="mr-1 size-3" />}
      {status === 'degraded' && <AlertTriangle className="mr-1 size-3" />}
      {status === 'outage' && <XCircle className="mr-1 size-3" />}
      {labels[status]}
    </Badge>
  )
}

export default function HealthPage() {
  const [isRefreshing, setIsRefreshing] = React.useState(false)
  const [lastRefresh, setLastRefresh] = React.useState(new Date())

  const handleRefresh = () => {
    setIsRefreshing(true)
    setTimeout(() => {
      setIsRefreshing(false)
      setLastRefresh(new Date())
    }, 1500)
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto space-y-6 p-4 pb-24 md:p-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-col gap-1">
            <h1 className="text-2xl font-bold tracking-tight text-balance md:text-3xl">
              System Health
            </h1>
            <p className="text-sm text-muted-foreground">
              Monitor the status and performance of all LDSN services
            </p>
          </div>
          <div className="flex items-center gap-4">
            <OverallStatusBadge status={mockHealthData.status} />
            <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isRefreshing}>
              <RefreshCw className={`mr-2 size-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Key Metrics */}
        <section aria-labelledby="metrics-heading">
          <h2 id="metrics-heading" className="sr-only">System Metrics</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="border-border/50 bg-card/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Uptime</p>
                    <p className="text-2xl font-bold">{mockHealthData.uptime}%</p>
                  </div>
                  <div className="flex size-12 items-center justify-center rounded-full bg-status-controlled/10">
                    <Server className="size-6 text-status-controlled" />
                  </div>
                </div>
                <Progress value={mockHealthData.uptime} className="mt-3 h-1" />
              </CardContent>
            </Card>

            <Card className="border-border/50 bg-card/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">API Requests (24h)</p>
                    <p className="text-2xl font-bold">{mockHealthData.metrics.apiRequests24h.toLocaleString()}</p>
                  </div>
                  <div className="flex size-12 items-center justify-center rounded-full bg-primary/10">
                    <Globe className="size-6 text-primary" />
                  </div>
                </div>
                <p className="mt-3 text-xs text-muted-foreground">+12% from yesterday</p>
              </CardContent>
            </Card>

            <Card className="border-border/50 bg-card/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Avg Latency</p>
                    <p className="text-2xl font-bold">{mockHealthData.metrics.averageLatency}ms</p>
                  </div>
                  <div className="flex size-12 items-center justify-center rounded-full bg-status-escalated/10">
                    <Zap className="size-6 text-status-escalated" />
                  </div>
                </div>
                <p className="mt-3 text-xs text-muted-foreground">Target: &lt;100ms</p>
              </CardContent>
            </Card>

            <Card className="border-border/50 bg-card/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Error Rate</p>
                    <p className="text-2xl font-bold">{mockHealthData.metrics.errorRate}%</p>
                  </div>
                  <div className="flex size-12 items-center justify-center rounded-full bg-status-controlled/10">
                    <CheckCircle2 className="size-6 text-status-controlled" />
                  </div>
                </div>
                <p className="mt-3 text-xs text-muted-foreground">Below threshold (1%)</p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Service Status */}
        <section aria-labelledby="services-heading">
          <Card className="border-border/50 bg-card/50">
            <CardHeader>
              <CardTitle className="text-base font-semibold">Service Status</CardTitle>
              <CardDescription>
                Real-time health status of all system components
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockHealthData.services.map((service) => (
                  <div
                    key={service.name}
                    className={`flex items-center justify-between rounded-lg border p-4 ${
                      service.status === 'warning'
                        ? 'border-status-escalated/30 bg-status-escalated/5'
                        : 'border-border/50 bg-background/50'
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`flex size-10 items-center justify-center rounded-lg ${
                        service.status === 'warning'
                          ? 'bg-status-escalated/10'
                          : 'bg-muted'
                      }`}>
                        <service.icon className={`size-5 ${
                          service.status === 'warning'
                            ? 'text-status-escalated'
                            : 'text-muted-foreground'
                        }`} />
                      </div>
                      <div>
                        <p className="font-medium">{service.name}</p>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <Clock className="size-3" />
                          <span>Last checked {formatDistanceToNow(new Date(service.lastCheck), { addSuffix: true })}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className={`text-sm font-medium ${
                          service.latency > 150
                            ? 'text-status-escalated'
                            : service.latency > 200
                            ? 'text-status-critical'
                            : 'text-foreground'
                        }`}>
                          {service.latency}ms
                        </p>
                        <p className="text-xs text-muted-foreground">latency</p>
                      </div>
                      <StatusIcon status={service.status} />
                    </div>
                  </div>
                ))}
              </div>
          </CardContent>
        </Card>
      </section>

      {/* Last Updated */}
        <div className="text-center text-sm text-muted-foreground">
          Last refreshed: {format(lastRefresh, 'MMM d, yyyy HH:mm:ss')}
        </div>
      </div>
    </DashboardLayout>
  )
}
