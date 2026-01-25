'use client'

import * as React from 'react'
import { DashboardLayout } from '@/components/dashboard-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, MapPin, User, FileText, CheckCircle } from 'lucide-react'
import { DiseaseAutocomplete } from '@/components/disease-autocomplete'
import { api, ReportRequest, ReportResponse } from '@/lib/api'

export default function ReportPage() {
  const [formData, setFormData] = React.useState<ReportRequest>({
    disease_name: '',
    location: '',
    reporter_id: '',
    mortality_count: undefined,
    latitude: undefined,
    longitude: undefined,
  })
  const [loading, setLoading] = React.useState(false)
  const [success, setSuccess] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [locations, setLocations] = React.useState<string[]>([])

  // Fetch available locations on mount
  React.useEffect(() => {
    const fetchLocations = async () => {
      try {
        const locationData = await api.locations.getAll()
        setLocations(locationData.locations)
      } catch (err) {
        console.error('Failed to fetch locations:', err)
      }
    }
    fetchLocations()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await api.reports.create(formData)
      setSuccess(true)
      // Reset form
      setFormData({
        disease_name: '',
        location: '',
        reporter_id: '',
        mortality_count: undefined,
        latitude: undefined,
        longitude: undefined,
      })
    } catch (err) {
      console.error('Failed to submit report:', err)
      setError('Failed to submit report. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: keyof ReportRequest, value: string | number | undefined) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  if (success) {
    return (
      <DashboardLayout>
        <div className="container mx-auto space-y-6 p-4 pb-24 md:p-6">
          <Card className="max-w-md mx-auto">
            <CardContent className="pt-6">
              <div className="text-center space-y-4">
                <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
                <div>
                  <h3 className="text-lg font-semibold text-green-900">Report Submitted Successfully!</h3>
                  <p className="text-sm text-muted-foreground mt-2">
                    Your disease report has been submitted and will be reviewed by our team.
                  </p>
                </div>
                <Button onClick={() => setSuccess(false)} className="w-full">
                  Submit Another Report
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto space-y-6 p-4 pb-24 md:p-6">
        {/* Header */}
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-bold tracking-tight text-balance md:text-3xl">
            Submit Disease Report
          </h1>
          <p className="text-sm text-muted-foreground">
            Report livestock disease observations with our intelligent disease recognition system
          </p>
        </div>

        <div className="max-w-2xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="size-5" />
                Disease Report Form
              </CardTitle>
              <CardDescription>
                Please provide accurate information to help us respond effectively to disease outbreaks
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Disease Name with Autocomplete */}
                <div className="space-y-2">
                  <Label htmlFor="disease">Disease or Symptom *</Label>
                  <DiseaseAutocomplete
                    value={formData.disease_name}
                    onChange={(value) => handleInputChange('disease_name', value)}
                    placeholder="Start typing to search diseases..."
                  />
                  <p className="text-xs text-muted-foreground">
                    Our system uses Trie-based autocomplete for accurate disease identification
                  </p>
                </div>

                {/* Location */}
                <div className="space-y-2">
                  <Label htmlFor="location">Location *</Label>
                  <div className="flex items-center gap-2">
                    <MapPin className="size-4 text-muted-foreground" />
                    <Select
                      value={formData.location}
                      onValueChange={(value) => handleInputChange('location', value)}
                    >
                      <SelectTrigger className="flex-1">
                        <SelectValue placeholder="Select location" />
                      </SelectTrigger>
                      <SelectContent>
                        {locations.map((location) => (
                          <SelectItem key={location} value={location}>
                            {location}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Reporter ID */}
                <div className="space-y-2">
                  <Label htmlFor="reporter">Reporter ID *</Label>
                  <div className="flex items-center gap-2">
                    <User className="size-4 text-muted-foreground" />
                    <Input
                      id="reporter"
                      value={formData.reporter_id}
                      onChange={(e) => handleInputChange('reporter_id', e.target.value)}
                      placeholder="Enter your reporter ID"
                      required
                    />
                  </div>
                </div>

                {/* Mortality Count */}
                <div className="space-y-2">
                  <Label htmlFor="mortality">Mortality Count</Label>
                  <Input
                    id="mortality"
                    type="number"
                    min="0"
                    value={formData.mortality_count || ''}
                    onChange={(e) => handleInputChange('mortality_count', e.target.value ? parseInt(e.target.value) : undefined)}
                    placeholder="Number of deaths (optional)"
                  />
                  <p className="text-xs text-muted-foreground">
                    Used for Segment Tree mortality tracking and trend analysis
                  </p>
                </div>

                {/* GPS Coordinates */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="latitude">Latitude</Label>
                    <Input
                      id="latitude"
                      type="number"
                      step="0.000001"
                      value={formData.latitude || ''}
                      onChange={(e) => handleInputChange('latitude', e.target.value ? parseFloat(e.target.value) : undefined)}
                      placeholder="Optional GPS latitude"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="longitude">Longitude</Label>
                    <Input
                      id="longitude"
                      type="number"
                      step="0.000001"
                      value={formData.longitude || ''}
                      onChange={(e) => handleInputChange('longitude', e.target.value ? parseFloat(e.target.value) : undefined)}
                      placeholder="Optional GPS longitude"
                    />
                  </div>
                </div>

                {error && (
                  <div className="flex items-center gap-2 p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
                    <AlertCircle className="size-4" />
                    {error}
                  </div>
                )}

                <Button type="submit" disabled={loading} className="w-full">
                  {loading ? 'Submitting Report...' : 'Submit Report'}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card className="mt-6">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="size-5 text-blue-500 mt-0.5" />
                <div className="space-y-2">
                  <h4 className="font-medium text-blue-900">Intelligent Processing</h4>
                  <p className="text-sm text-muted-foreground">
                    Your report will be automatically prioritized using our Priority Queue system and
                    checked for cluster membership using Union-Find algorithms. Critical reports trigger
                    immediate response protocols.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}
