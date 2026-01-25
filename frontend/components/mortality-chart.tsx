'use client'

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { MortalityTrend } from '@/lib/api'

interface MortalityChartProps {
  data: MortalityTrend[]
}

export function MortalityChart({ data }: MortalityChartProps) {
  return (
    <Card className="border-border/50 bg-card/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">Mortality Trends by Species</CardTitle>
        <CardDescription>
          Monthly mortality data across livestock categories (Segment Tree aggregation)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.25 0.01 260)" vertical={false} />
              <XAxis
                dataKey="month"
                axisLine={false}
                tickLine={false}
                tick={{ fill: 'oklch(0.65 0 0)', fontSize: 12 }}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: 'oklch(0.65 0 0)', fontSize: 12 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'oklch(0.17 0.01 260)',
                  border: '1px solid oklch(0.25 0.01 260)',
                  borderRadius: '8px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                }}
                labelStyle={{ color: 'oklch(0.95 0 0)', fontWeight: 600 }}
                itemStyle={{ color: 'oklch(0.75 0 0)' }}
              />
              <Legend
                verticalAlign="top"
                height={36}
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ paddingBottom: '8px' }}
              />
              <Bar
                dataKey="cattle"
                name="Cattle"
                fill="oklch(0.72 0.19 160)"
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="poultry"
                name="Poultry"
                fill="oklch(0.75 0.18 85)"
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="swine"
                name="Swine"
                fill="oklch(0.55 0.22 25)"
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="sheep"
                name="Sheep"
                fill="oklch(0.65 0.15 250)"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
