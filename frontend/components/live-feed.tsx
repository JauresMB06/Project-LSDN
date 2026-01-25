'use client'

import { Clock, MapPin, User } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { DiseaseReport } from '@/lib/mock-data'

interface LiveFeedProps {
  reports: DiseaseReport[]
}

function StatusBadge({ status }: { status: DiseaseReport['status'] }) {
  const variants = {
    critical: 'bg-status-critical/20 text-status-critical border-status-critical/30',
    escalated: 'bg-status-escalated/20 text-status-escalated border-status-escalated/30',
    controlled: 'bg-status-controlled/20 text-status-controlled border-status-controlled/30',
  }

  const labels = {
    critical: 'Critical',
    escalated: 'Escalated',
    controlled: 'Controlled',
  }

  return (
    <Badge variant="outline" className={variants[status]}>
      {labels[status]}
    </Badge>
  )
}

function PriorityIndicator({ priority }: { priority: 1 | 2 | 3 }) {
  const colors = {
    1: 'bg-status-critical',
    2: 'bg-status-escalated',
    3: 'bg-status-controlled',
  }

  return (
    <div className="flex items-center gap-1">
      <span className={`size-2 rounded-full ${colors[priority]}`} />
      <span className="text-xs text-muted-foreground">P{priority}</span>
    </div>
  )
}

export function LiveFeed({ reports }: LiveFeedProps) {
  return (
    <Card className="flex h-full flex-col border-border/50 bg-card/50">
      <CardHeader className="flex-row items-center justify-between space-y-0 border-b border-border pb-3">
        <CardTitle className="text-base font-semibold">Live Intelligence Feed</CardTitle>
        <div className="flex items-center gap-1.5 text-xs text-status-controlled">
          <span className="relative flex size-2">
            <span className="absolute inline-flex size-full animate-ping rounded-full bg-status-controlled opacity-75" />
            <span className="relative inline-flex size-2 rounded-full bg-status-controlled" />
          </span>
          Live
        </div>
      </CardHeader>
      <CardContent className="flex-1 p-0">
        <ScrollArea className="h-[400px] lg:h-[calc(100%-1px)]">
          <div className="space-y-2 p-3">
            {reports.map((report) => (
              <div
                key={report.id}
                className={`group relative rounded-lg border bg-background/50 p-3 transition-colors hover:bg-muted/50 ${
                  report.priority === 1 ? 'animate-pulse-critical border-status-critical/50' : 'border-border/50'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-medium leading-none">{report.diseaseName}</h4>
                      <PriorityIndicator priority={report.priority} />
                    </div>
                    <p className="text-xs text-muted-foreground">{report.species}</p>
                  </div>
                  <StatusBadge status={report.status} />
                </div>

                <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <MapPin className="size-3" />
                    <span>{report.location}, {report.region}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="size-3" />
                    <span>{formatDistanceToNow(new Date(report.reportedAt), { addSuffix: true })}</span>
                  </div>
                </div>

                <div className="mt-2 flex items-center justify-between">
                  <div className="flex items-center gap-3 text-xs">
                    <span className="text-muted-foreground">
                      <span className="font-medium text-foreground">{report.affectedCount}</span> affected
                    </span>
                    <span className="text-muted-foreground">
                      <span className="font-medium text-status-critical">{report.mortalityCount}</span> mortality
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <User className="size-3" />
                    <span className="truncate max-w-[100px]">{report.reporter}</span>
                  </div>
                </div>

                <div className="mt-2 text-[10px] uppercase tracking-wider text-muted-foreground/70">
                  {report.id}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
