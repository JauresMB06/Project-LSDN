'use client'

import {
  AlertTriangle,
  Calendar,
  Clock,
  ExternalLink,
  MapPin,
  Skull,
  User,
  Users,
} from 'lucide-react'
import { formatDistanceToNow, format } from 'date-fns'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Separator } from '@/components/ui/separator'
import type { DiseaseReport } from '@/lib/api'

interface ReportDetailModalProps {
  report: DiseaseReport | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onStatusChange?: (id: string, status: DiseaseReport['status']) => void
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
    <Badge variant="outline" className={`text-sm ${variants[status]}`}>
      {labels[status]}
    </Badge>
  )
}

export function ReportDetailModal({
  report,
  open,
  onOpenChange,
  onStatusChange,
}: ReportDetailModalProps) {
  if (!report) return null

  const mortalityRate = ((report.mortalityCount / report.affectedCount) * 100).toFixed(1)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl bg-card border-border/50">
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div>
              <DialogTitle className="text-xl">{report.diseaseName}</DialogTitle>
              <DialogDescription className="flex items-center gap-2 mt-1">
                <span className="font-mono text-xs">{report.id}</span>
                <span className="text-muted-foreground">|</span>
                <span>{report.species}</span>
              </DialogDescription>
            </div>
            <div className="flex items-center gap-2">
              <span className={`inline-flex items-center justify-center size-8 rounded-full text-sm font-bold ${
                report.priority === 1 ? 'bg-status-critical text-white' :
                report.priority === 2 ? 'bg-status-escalated text-background' :
                'bg-status-controlled text-background'
              }`}>
                P{report.priority}
              </span>
              <StatusBadge status={report.status} />
            </div>
          </div>
        </DialogHeader>

        <div className="grid gap-6 py-4">
          {/* Key Metrics */}
          <div className="grid grid-cols-3 gap-4">
            <div className="rounded-lg border border-border/50 bg-background/50 p-4 text-center">
              <Users className="mx-auto size-5 text-muted-foreground mb-2" />
              <p className="text-2xl font-bold">{report.affectedCount}</p>
              <p className="text-xs text-muted-foreground">Affected Animals</p>
            </div>
            <div className="rounded-lg border border-status-critical/30 bg-status-critical/10 p-4 text-center">
              <Skull className="mx-auto size-5 text-status-critical mb-2" />
              <p className="text-2xl font-bold text-status-critical">{report.mortalityCount}</p>
              <p className="text-xs text-muted-foreground">Mortalities</p>
            </div>
            <div className="rounded-lg border border-border/50 bg-background/50 p-4 text-center">
              <AlertTriangle className="mx-auto size-5 text-status-escalated mb-2" />
              <p className="text-2xl font-bold">{mortalityRate}%</p>
              <p className="text-xs text-muted-foreground">Mortality Rate</p>
            </div>
          </div>

          <Separator />

          {/* Location & Time */}
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-3">
              <h4 className="text-sm font-semibold">Location Details</h4>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <MapPin className="size-4 text-muted-foreground" />
                  <span>{report.location}, {report.region}</span>
                </div>
                <div className="text-xs text-muted-foreground pl-6">
                  Coordinates: {report.coordinates.lat.toFixed(4)}, {report.coordinates.lng.toFixed(4)}
                </div>
                <Button variant="outline" size="sm" className="mt-2 bg-transparent">
                  <ExternalLink className="mr-2 size-3" />
                  View on Map
                </Button>
              </div>
            </div>
            <div className="space-y-3">
              <h4 className="text-sm font-semibold">Timeline</h4>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <Calendar className="size-4 text-muted-foreground" />
                  <span>{format(new Date(report.reportedAt), 'MMMM d, yyyy')}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="size-4 text-muted-foreground" />
                  <span>{format(new Date(report.reportedAt), 'HH:mm:ss')}</span>
                </div>
                <div className="text-xs text-muted-foreground pl-6">
                  {formatDistanceToNow(new Date(report.reportedAt), { addSuffix: true })}
                </div>
              </div>
            </div>
          </div>

          <Separator />

          {/* Reporter Info */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold">Reported By</h4>
            <div className="flex items-center gap-3">
              <div className="size-10 rounded-full bg-muted flex items-center justify-center">
                <User className="size-5 text-muted-foreground" />
              </div>
              <div>
                <p className="font-medium">{report.reporter}</p>
                <p className="text-xs text-muted-foreground">Veterinary Officer</p>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter className="flex-col gap-2 sm:flex-row">
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="border-status-critical/30 text-status-critical hover:bg-status-critical/10 bg-transparent"
              onClick={() => onStatusChange?.(report.id, 'critical')}
            >
              Mark Critical
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="border-status-escalated/30 text-status-escalated hover:bg-status-escalated/10 bg-transparent"
              onClick={() => onStatusChange?.(report.id, 'escalated')}
            >
              Mark Escalated
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="border-status-controlled/30 text-status-controlled hover:bg-status-controlled/10 bg-transparent"
              onClick={() => onStatusChange?.(report.id, 'controlled')}
            >
              Mark Controlled
            </Button>
          </div>
          <Button variant="default" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
