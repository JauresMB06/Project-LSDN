'use client'

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from 'recharts'
import { useEffect, useState } from 'react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import { api } from '@/lib/api'

// Mock data for components that don't have API yet
const diseaseDistribution = [
  { name: 'African Swine Fever', value: 320, fill: 'hsl(var(--chart-1))' },
  { name: 'Avian Influenza', value: 280, fill: 'hsl(var(--chart-2))' },
  { name: 'Foot-and-Mouth Disease', value: 245, fill: 'hsl(var(--chart-3))' },
  { name: 'Newcastle Disease', value: 189, fill: 'hsl(var(--chart-4))' },
  { name: 'Other', value: 213, fill: 'hsl(var(--chart-5))' },
]

const regionalData = [
  { region: 'Far North', outbreaks: 45, controlled: 38 },
  { region: 'North', outbreaks: 38, controlled: 32 },
  { region: 'Adamawa', outbreaks: 32, controlled: 28 },
  { region: 'Centre', outbreaks: 28, controlled: 25 },
  { region: 'Littoral', outbreaks: 22, controlled: 20 },
  { region: 'West', outbreaks: 18, controlled: 15 },
  { region: 'North-West', outbreaks: 15, controlled: 12 },
  { region: 'South-West', outbreaks: 12, controlled: 10 },
  { region: 'South', outbreaks: 10, controlled: 9 },
  { region: 'East', outbreaks: 8, controlled: 7 },
]

const timeSeriesData = [
  { date: 'Jan', cases: 145, mortality: 12 },
  { date: 'Feb', cases: 168, mortality: 15 },
  { date: 'Mar', cases: 195, mortality: 18 },
  { date: 'Apr', cases: 178, mortality: 14 },
  { date: 'May', cases: 210, mortality: 22 },
  { date: 'Jun', cases: 185, mortality: 16 },
  { date: 'Jul', cases: 225, mortality: 25 },
  { date: 'Aug', cases: 198, mortality: 19 },
  { date: 'Sep', cases: 245, mortality: 28 },
  { date: 'Oct', cases: 212, mortality: 21 },
  { date: 'Nov', cases: 278, mortality: 32 },
  { date: 'Dec', cases: 256, mortality: 29 },
]

const chartConfig = {
  cases: {
    label: 'Cases',
    color: 'hsl(var(--chart-1))',
  },
  mortality: {
    label: 'Mortality',
    color: 'hsl(var(--chart-3))',
  },
  outbreaks: {
    label: 'Outbreaks',
    color: 'hsl(var(--chart-2))',
  },
  controlled: {
    label: 'Controlled',
    color: 'hsl(var(--chart-1))',
  },
  affected: {
    label: 'Affected',
    color: 'hsl(var(--chart-4))',
  },
}

export function DiseaseDistributionChart() {
  return (
    <Card className="border-border/50 bg-card/50">
      <CardHeader>
        <CardTitle className="text-base font-semibold">Disease Distribution</CardTitle>
        <CardDescription>Breakdown of reported diseases by type</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[300px] w-full">
          <PieChart>
            <Pie
              data={diseaseDistribution}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
              label={({ name, percent }) => `${name.split(' ')[0]} ${(percent * 100).toFixed(0)}%`}
              labelLine={false}
            >
              {diseaseDistribution.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
            <ChartTooltip content={<ChartTooltipContent />} />
          </PieChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}

export function RegionalOutbreaksChart() {
  return (
    <Card className="border-border/50 bg-card/50">
      <CardHeader>
        <CardTitle className="text-base font-semibold">Regional Analysis</CardTitle>
        <CardDescription>Outbreaks vs controlled cases by region</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[300px] w-full">
          <BarChart data={regionalData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" horizontal={false} />
            <XAxis type="number" stroke="hsl(var(--muted-foreground))" fontSize={12} />
            <YAxis 
              dataKey="region" 
              type="category" 
              width={80} 
              stroke="hsl(var(--muted-foreground))" 
              fontSize={11}
            />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Bar dataKey="outbreaks" fill="hsl(var(--chart-2))" radius={[0, 4, 4, 0]} />
            <Bar dataKey="controlled" fill="hsl(var(--chart-1))" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}

export function TimeSeriesChart() {
  return (
    <Card className="border-border/50 bg-card/50">
      <CardHeader>
        <CardTitle className="text-base font-semibold">Yearly Trend</CardTitle>
        <CardDescription>Monthly cases and mortality over the past year</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[300px] w-full">
          <AreaChart data={timeSeriesData}>
            <defs>
              <linearGradient id="colorCases" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--chart-1))" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(var(--chart-1))" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorMortality" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--chart-3))" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(var(--chart-3))" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={12} />
            <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Area
              type="monotone"
              dataKey="cases"
              stroke="hsl(var(--chart-1))"
              fillOpacity={1}
              fill="url(#colorCases)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="mortality"
              stroke="hsl(var(--chart-3))"
              fillOpacity={1}
              fill="url(#colorMortality)"
              strokeWidth={2}
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}

export function SpeciesImpactChart() {
  const [speciesData, setSpeciesData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  // Fetch species analytics data
  useEffect(() => {
    const fetchSpeciesData = async () => {
      try {
        setLoading(true)
        const response = await fetch('http://localhost:8000/api/analytics/species')
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        const data = await response.json()

        // Transform API data to chart format
        const transformedData = data.species_data.map((species: any) => ({
          species: species.species,
          affected: species.affected_animals,
          mortality: species.total_mortality,
        }))
        setSpeciesData(transformedData)
      } catch (err) {
        console.error('Failed to fetch species analytics:', err)
        // Fallback to mock data if API fails
        setSpeciesData([
          { species: 'Cattle', affected: 4250, mortality: 185 },
          { species: 'Poultry', affected: 12500, mortality: 890 },
          { species: 'Swine', affected: 2100, mortality: 145 },
          { species: 'Sheep', affected: 1850, mortality: 78 },
          { species: 'Goats', affected: 1420, mortality: 52 },
        ])
      } finally {
        setLoading(false)
      }
    }

    fetchSpeciesData()
  }, [])

  if (loading) {
    return (
      <Card className="border-border/50 bg-card/50">
        <CardHeader>
          <CardTitle className="text-base font-semibold">Species Impact</CardTitle>
          <CardDescription>Loading species analytics...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[300px]">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-border/50 bg-card/50">
      <CardHeader>
        <CardTitle className="text-base font-semibold">Species Impact</CardTitle>
        <CardDescription>Affected animals and mortality by species</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[300px] w-full">
          <BarChart data={speciesData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="species" stroke="hsl(var(--muted-foreground))" fontSize={12} />
            <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Bar dataKey="affected" fill="hsl(var(--chart-4))" radius={[4, 4, 0, 0]} />
            <Bar dataKey="mortality" fill="hsl(var(--chart-3))" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}

// Response Metrics Component
export function ResponseMetrics() {
  const metrics = [
    {
      label: 'Avg Response Time',
      value: '4.2 hrs',
      change: '-12%',
      trend: 'positive',
      description: 'Time from report to first action',
    },
    {
      label: 'Containment Rate',
      value: '87.3%',
      change: '+5.2%',
      trend: 'positive',
      description: 'Successfully contained outbreaks',
    },
    {
      label: 'Vaccination Coverage',
      value: '68.5%',
      change: '+8.1%',
      trend: 'positive',
      description: 'Livestock vaccination rate',
    },
    {
      label: 'Lab Tests Processed',
      value: '1,247',
      change: '+18%',
      trend: 'positive',
      description: 'Diagnostic tests this month',
    },
  ]

  return (
    <Card className="border-border/50 bg-card/50">
      <CardHeader>
        <CardTitle className="text-base font-semibold">Response Metrics</CardTitle>
        <CardDescription>Key performance indicators for disease response</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {metrics.map((metric) => (
            <div key={metric.label} className="space-y-1 rounded-lg border border-border/50 bg-background/50 p-4">
              <p className="text-xs text-muted-foreground">{metric.label}</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold">{metric.value}</span>
                <span className={`text-xs font-medium ${
                  metric.trend === 'positive' ? 'text-status-controlled' : 'text-status-critical'
                }`}>
                  {metric.change}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">{metric.description}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
