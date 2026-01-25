'use client'

import * as React from 'react'
import {
  ArrowUpDown,
  ChevronDown,
  Clock,
  Filter,
  MapPin,
  MoreHorizontal,
  Search,
  User,
} from 'lucide-react'
import { formatDistanceToNow, format } from 'date-fns'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { DiseaseReport } from '@/lib/api'
import { api } from '@/lib/api'

interface TriageTableProps {
  reports: DiseaseReport[]
  onStatusChange?: (id: string, status: DiseaseReport['status']) => void
  onViewReport?: (report: DiseaseReport) => void
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

function PriorityBadge({ priority }: { priority: 1 | 2 | 3 }) {
  const colors = {
    1: 'bg-status-critical text-white',
    2: 'bg-status-escalated text-background',
    3: 'bg-status-controlled text-background',
  }

  return (
    <span className={`inline-flex items-center justify-center size-6 rounded-full text-xs font-bold ${colors[priority]}`}>
      P{priority}
    </span>
  )
}

export function TriageTable({ reports: initialReports, onStatusChange, onViewReport }: TriageTableProps) {
  const [reports, setReports] = React.useState<DiseaseReport[]>(initialReports || [])
  const [loading, setLoading] = React.useState(false)
  const [search, setSearch] = React.useState('')
  const [statusFilter, setStatusFilter] = React.useState<string>('all')
  const [priorityFilter, setPriorityFilter] = React.useState<string>('all')
  const [selectedRows, setSelectedRows] = React.useState<Set<string>>(new Set())
  const [sortBy, setSortBy] = React.useState<'priority' | 'date' | 'affected'>('priority')
  const [sortOrder, setSortOrder] = React.useState<'asc' | 'desc'>('asc')

  // Fetch triage alerts on component mount
  React.useEffect(() => {
    const fetchTriageAlerts = async () => {
      setLoading(true)
      try {
        const alerts = await api.triage.getAlerts(100) // Get up to 100 alerts
        // Convert API alerts to DiseaseReport format
        const convertedReports: DiseaseReport[] = alerts.map(alert => ({
          id: alert.id.toString(),
          diseaseName: alert.disease_name,
          location: alert.location,
          region: 'Unknown', // TODO: get from location data
          coordinates: { lat: 0, lng: 0 }, // TODO: get from location data
          reportedAt: new Date(alert.timestamp * 1000).toISOString(),
          priority: alert.priority_level as 1 | 2 | 3,
          status: alert.priority_level === 1 ? 'critical' : alert.priority_level === 2 ? 'escalated' : 'controlled',
          affectedCount: alert.details?.affected_count || 0,
          mortalityCount: alert.details?.mortality_count || 0,
          reporter: alert.reporter_id,
          species: alert.details?.species || 'Unknown',
          notes: alert.details?.notes
        }))
        setReports(convertedReports)
      } catch (error) {
        console.error('Failed to fetch triage alerts:', error)
        // Fallback to initial reports if API fails
        setReports(initialReports || [])
      } finally {
        setLoading(false)
      }
    }

    fetchTriageAlerts()
  }, [initialReports])

  const filteredReports = React.useMemo(() => {
    let filtered = [...reports]

    // Search filter
    if (search) {
      const searchLower = search.toLowerCase()
      filtered = filtered.filter(
        (r) =>
          r.diseaseName.toLowerCase().includes(searchLower) ||
          r.location.toLowerCase().includes(searchLower) ||
          r.region.toLowerCase().includes(searchLower) ||
          r.id.toLowerCase().includes(searchLower)
      )
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((r) => r.status === statusFilter)
    }

    // Priority filter
    if (priorityFilter !== 'all') {
      filtered = filtered.filter((r) => r.priority === Number(priorityFilter))
    }

    // Sorting
    filtered.sort((a, b) => {
      let comparison = 0
      if (sortBy === 'priority') {
        comparison = a.priority - b.priority
      } else if (sortBy === 'date') {
        comparison = new Date(b.reportedAt).getTime() - new Date(a.reportedAt).getTime()
      } else if (sortBy === 'affected') {
        comparison = b.affectedCount - a.affectedCount
      }
      return sortOrder === 'asc' ? comparison : -comparison
    })

    return filtered
  }, [reports, search, statusFilter, priorityFilter, sortBy, sortOrder])

  const toggleSort = (column: 'priority' | 'date' | 'affected') => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortOrder('asc')
    }
  }

  const toggleRowSelection = (id: string) => {
    const newSelected = new Set(selectedRows)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedRows(newSelected)
  }

  const toggleAllRows = () => {
    if (selectedRows.size === filteredReports.length) {
      setSelectedRows(new Set())
    } else {
      setSelectedRows(new Set(filteredReports.map((r) => r.id)))
    }
  }

  const criticalCount = reports.filter((r) => r.status === 'critical').length
  const escalatedCount = reports.filter((r) => r.status === 'escalated').length
  const controlledCount = reports.filter((r) => r.status === 'controlled').length

  return (
    <div className="space-y-4">
      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-4">
        <div className="flex items-center gap-3 rounded-lg border border-status-critical/30 bg-status-critical/10 p-3">
          <div className="size-10 rounded-full bg-status-critical/20 flex items-center justify-center">
            <span className="text-lg font-bold text-status-critical">{criticalCount}</span>
          </div>
          <div>
            <p className="text-sm font-medium text-status-critical">Critical</p>
            <p className="text-xs text-muted-foreground">Requires immediate action</p>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-lg border border-status-escalated/30 bg-status-escalated/10 p-3">
          <div className="size-10 rounded-full bg-status-escalated/20 flex items-center justify-center">
            <span className="text-lg font-bold text-status-escalated">{escalatedCount}</span>
          </div>
          <div>
            <p className="text-sm font-medium text-status-escalated">Escalated</p>
            <p className="text-xs text-muted-foreground">Under active monitoring</p>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-lg border border-status-controlled/30 bg-status-controlled/10 p-3">
          <div className="size-10 rounded-full bg-status-controlled/20 flex items-center justify-center">
            <span className="text-lg font-bold text-status-controlled">{controlledCount}</span>
          </div>
          <div>
            <p className="text-sm font-medium text-status-controlled">Controlled</p>
            <p className="text-xs text-muted-foreground">Situation contained</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 items-center gap-2">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search reports..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 bg-background/50"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[140px] bg-background/50">
              <Filter className="mr-2 size-4" />
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
              <SelectItem value="escalated">Escalated</SelectItem>
              <SelectItem value="controlled">Controlled</SelectItem>
            </SelectContent>
          </Select>
          <Select value={priorityFilter} onValueChange={setPriorityFilter}>
            <SelectTrigger className="w-[140px] bg-background/50">
              <SelectValue placeholder="Priority" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Priorities</SelectItem>
              <SelectItem value="1">P1 - Critical</SelectItem>
              <SelectItem value="2">P2 - High</SelectItem>
              <SelectItem value="3">P3 - Normal</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {selectedRows.size > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {selectedRows.size} selected
            </span>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  Bulk Actions <ChevronDown className="ml-2 size-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => onStatusChange && selectedRows.forEach((id) => onStatusChange(id, 'escalated'))}>
                  Mark as Escalated
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onStatusChange && selectedRows.forEach((id) => onStatusChange(id, 'controlled'))}>
                  Mark as Controlled
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-destructive">
                  Archive Selected
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="rounded-lg border border-border/50 bg-card/50">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="w-[40px]">
                <Checkbox
                  checked={selectedRows.size === filteredReports.length && filteredReports.length > 0}
                  onCheckedChange={toggleAllRows}
                  aria-label="Select all"
                />
              </TableHead>
              <TableHead className="w-[100px]">
                <Button
                  variant="ghost"
                  size="sm"
                  className="-ml-3 h-8 data-[state=open]:bg-accent"
                  onClick={() => toggleSort('priority')}
                >
                  Priority
                  <ArrowUpDown className="ml-2 size-4" />
                </Button>
              </TableHead>
              <TableHead>Report ID</TableHead>
              <TableHead>Disease</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  size="sm"
                  className="-ml-3 h-8 data-[state=open]:bg-accent"
                  onClick={() => toggleSort('affected')}
                >
                  Affected
                  <ArrowUpDown className="ml-2 size-4" />
                </Button>
              </TableHead>
              <TableHead>Status</TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  size="sm"
                  className="-ml-3 h-8 data-[state=open]:bg-accent"
                  onClick={() => toggleSort('date')}
                >
                  Reported
                  <ArrowUpDown className="ml-2 size-4" />
                </Button>
              </TableHead>
              <TableHead>Reporter</TableHead>
              <TableHead className="w-[50px]" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredReports.length === 0 ? (
              <TableRow>
                <TableCell colSpan={10} className="h-24 text-center text-muted-foreground">
                  No reports found.
                </TableCell>
              </TableRow>
            ) : (
              filteredReports.map((report) => (
                <TableRow
                  key={report.id}
                  className={`${report.priority === 1 ? 'bg-status-critical/5' : ''}`}
                >
                  <TableCell>
                    <Checkbox
                      checked={selectedRows.has(report.id)}
                      onCheckedChange={() => toggleRowSelection(report.id)}
                      aria-label={`Select ${report.id}`}
                    />
                  </TableCell>
                  <TableCell>
                    <PriorityBadge priority={report.priority} />
                  </TableCell>
                  <TableCell className="font-mono text-xs">{report.id}</TableCell>
                  <TableCell>
                    <div>
                      <p className="font-medium">{report.diseaseName}</p>
                      <p className="text-xs text-muted-foreground">{report.species}</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <MapPin className="size-3 text-muted-foreground" />
                      <span>{report.location}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">{report.region}</p>
                  </TableCell>
                  <TableCell>
                    <div>
                      <span className="font-medium">{report.affectedCount}</span>
                      <span className="text-xs text-muted-foreground"> / </span>
                      <span className="text-status-critical">{report.mortalityCount}</span>
                      <span className="text-xs text-muted-foreground"> mort.</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={report.status} />
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Clock className="size-3 text-muted-foreground" />
                      <span className="text-xs">{formatDistanceToNow(new Date(report.reportedAt), { addSuffix: true })}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">{format(new Date(report.reportedAt), 'MMM d, HH:mm')}</p>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <User className="size-3 text-muted-foreground" />
                      <span className="text-xs truncate max-w-[100px]">{report.reporter}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="size-8">
                          <MoreHorizontal className="size-4" />
                          <span className="sr-only">Actions</span>
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuItem onClick={() => onViewReport?.(report)}>
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem>Edit Report</DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuLabel>Change Status</DropdownMenuLabel>
                        <DropdownMenuItem onClick={() => onStatusChange?.(report.id, 'critical')}>
                          Mark Critical
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => onStatusChange?.(report.id, 'escalated')}>
                          Mark Escalated
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => onStatusChange?.(report.id, 'controlled')}>
                          Mark Controlled
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="text-destructive">
                          Archive
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination Info */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <p>
          Showing {filteredReports.length} of {reports.length} reports
        </p>
        <p className="text-xs">
          Last updated: {format(new Date(), 'MMM d, yyyy HH:mm:ss')}
        </p>
      </div>
    </div>
  )
}
