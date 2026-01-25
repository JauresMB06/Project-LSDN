'use client'

import React from "react"

import {
  Activity,
  AlertTriangle,
  Skull,
  TrendingDown,
  TrendingUp,
  Users,
} from 'lucide-react'
import {
  Area,
  AreaChart,
  ResponsiveContainer,
} from 'recharts'

import { Card, CardContent } from '@/components/ui/card'
import type { KPIData } from '@/lib/api'

interface KPICardsProps {
  data: KPIData
}

interface KPICardProps {
  title: string
  value: string | number
  trend: number[]
  trendDirection: 'up' | 'down' | 'neutral'
  trendIsPositive: boolean
  icon: React.ReactNode
  colorClass: string
}

function KPICard({
  title,
  value,
  trend,
  trendDirection,
  trendIsPositive,
  icon,
  colorClass,
}: KPICardProps) {
  const chartData = trend.map((v, i) => ({ value: v, index: i }))
  const firstValue = trend[0]
  const lastValue = trend[trend.length - 1]
  const changePercent = ((lastValue - firstValue) / firstValue * 100).toFixed(1)
  const isPositiveChange = Number(changePercent) >= 0

  return (
    <Card className="relative overflow-hidden border-border/50 bg-card/50 backdrop-blur-sm">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              {title}
            </p>
            <p className="text-2xl font-bold tracking-tight">{value}</p>
            <div className="flex items-center gap-1 text-xs">
              {trendDirection === 'up' ? (
                <TrendingUp className={`size-3 ${trendIsPositive ? 'text-status-controlled' : 'text-status-critical'}`} />
              ) : trendDirection === 'down' ? (
                <TrendingDown className={`size-3 ${trendIsPositive ? 'text-status-controlled' : 'text-status-critical'}`} />
              ) : null}
              <span className={trendIsPositive ? 'text-status-controlled' : 'text-status-critical'}>
                {isPositiveChange ? '+' : ''}{changePercent}%
              </span>
              <span className="text-muted-foreground">vs last week</span>
            </div>
          </div>
          <div className={`flex size-10 items-center justify-center rounded-lg ${colorClass}`}>
            {icon}
          </div>
        </div>
        <div className="mt-3 h-12">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id={`gradient-${title}`} x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="0%"
                    stopColor={trendIsPositive ? 'oklch(0.72 0.19 160)' : 'oklch(0.55 0.22 25)'}
                    stopOpacity={0.3}
                  />
                  <stop
                    offset="100%"
                    stopColor={trendIsPositive ? 'oklch(0.72 0.19 160)' : 'oklch(0.55 0.22 25)'}
                    stopOpacity={0}
                  />
                </linearGradient>
              </defs>
              <Area
                type="monotone"
                dataKey="value"
                stroke={trendIsPositive ? 'oklch(0.72 0.19 160)' : 'oklch(0.55 0.22 25)'}
                strokeWidth={1.5}
                fill={`url(#gradient-${title})`}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

export function KPICards({ data }: KPICardsProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <KPICard
        title="Total Cases"
        value={data.totalCases.toLocaleString()}
        trend={data.totalCasesTrend}
        trendDirection="up"
        trendIsPositive={false}
        icon={<Users className="size-5 text-white" />}
        colorClass="bg-status-escalated"
      />
      <KPICard
        title="Active Clusters"
        value={data.activeClusters}
        trend={data.activeClustersTrend}
        trendDirection="up"
        trendIsPositive={false}
        icon={<AlertTriangle className="size-5 text-white" />}
        colorClass="bg-status-critical"
      />
      <KPICard
        title="Mortality Rate"
        value={`${data.mortalityRate}%`}
        trend={data.mortalityRateTrend}
        trendDirection="down"
        trendIsPositive={true}
        icon={<Skull className="size-5 text-white" />}
        colorClass="bg-chart-4"
      />
      <KPICard
        title="Avg. Priority"
        value={data.avgPriority.toFixed(1)}
        trend={data.avgPriorityTrend}
        trendDirection="down"
        trendIsPositive={true}
        icon={<Activity className="size-5 text-white" />}
        colorClass="bg-status-controlled"
      />
    </div>
  )
}
