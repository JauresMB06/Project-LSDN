'use client'

import * as React from 'react'
import {
  Bell,
  Database,
  Globe,
  Key,
  MapPin,
  Moon,
  Palette,
  Save,
  Shield,
  Sun,
  User,
  Volume2,
} from 'lucide-react'

import { DashboardLayout } from '@/components/dashboard-layout'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export default function SettingsPage() {
  const [isSaving, setIsSaving] = React.useState(false)

  const handleSave = () => {
    setIsSaving(true)
    setTimeout(() => setIsSaving(false), 1000)
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto space-y-6 p-4 pb-24 md:p-6">
        {/* Header */}
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-bold tracking-tight text-balance md:text-3xl">
            Settings
          </h1>
          <p className="text-sm text-muted-foreground">
            Configure your LDSN Command Center preferences
          </p>
        </div>

        <Tabs defaultValue="general" className="space-y-6">
          <TabsList className="bg-muted/50">
            <TabsTrigger value="general">General</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="api">API Configuration</TabsTrigger>
            <TabsTrigger value="account">Account</TabsTrigger>
          </TabsList>

          {/* General Settings */}
          <TabsContent value="general" className="space-y-6">
            <Card className="border-border/50 bg-card/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base font-semibold">
                  <Palette className="size-5" />
                  Appearance
                </CardTitle>
                <CardDescription>
                  Customize the look and feel of the dashboard
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Theme</Label>
                    <p className="text-sm text-muted-foreground">
                      Select your preferred color scheme
                    </p>
                  </div>
                  <Select defaultValue="dark">
                    <SelectTrigger className="w-[140px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="light">
                        <div className="flex items-center gap-2">
                          <Sun className="size-4" />
                          Light
                        </div>
                      </SelectItem>
                      <SelectItem value="dark">
                        <div className="flex items-center gap-2">
                          <Moon className="size-4" />
                          Dark
                        </div>
                      </SelectItem>
                      <SelectItem value="system">System</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Compact Mode</Label>
                    <p className="text-sm text-muted-foreground">
                      Reduce spacing for more data density
                    </p>
                  </div>
                  <Switch />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Animations</Label>
                    <p className="text-sm text-muted-foreground">
                      Enable smooth transitions and animations
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
              </CardContent>
            </Card>

            <Card className="border-border/50 bg-card/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base font-semibold">
                  <MapPin className="size-5" />
                  Regional Settings
                </CardTitle>
                <CardDescription>
                  Configure location and language preferences
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Default Region</Label>
                    <Select defaultValue="all">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Regions</SelectItem>
                        <SelectItem value="far-north">Far North</SelectItem>
                        <SelectItem value="north">North</SelectItem>
                        <SelectItem value="adamawa">Adamawa</SelectItem>
                        <SelectItem value="centre">Centre</SelectItem>
                        <SelectItem value="littoral">Littoral</SelectItem>
                        <SelectItem value="west">West</SelectItem>
                        <SelectItem value="north-west">North-West</SelectItem>
                        <SelectItem value="south-west">South-West</SelectItem>
                        <SelectItem value="south">South</SelectItem>
                        <SelectItem value="east">East</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Language</Label>
                    <Select defaultValue="en">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="en">English</SelectItem>
                        <SelectItem value="fr">French</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Timezone</Label>
                  <Select defaultValue="wat">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="wat">West Africa Time (WAT)</SelectItem>
                      <SelectItem value="utc">UTC</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Notifications Settings */}
          <TabsContent value="notifications" className="space-y-6">
            <Card className="border-border/50 bg-card/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base font-semibold">
                  <Bell className="size-5" />
                  Alert Preferences
                </CardTitle>
                <CardDescription>
                  Configure how you receive disease outbreak alerts
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label className="flex items-center gap-2">
                      P1 Critical Alerts
                      <Badge className="bg-status-critical/20 text-status-critical border-status-critical/30">
                        High Priority
                      </Badge>
                    </Label>
                    <p className="text-sm text-muted-foreground">
                      Immediate notification for critical outbreaks
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label className="flex items-center gap-2">
                      P2 Escalated Alerts
                      <Badge className="bg-status-escalated/20 text-status-escalated border-status-escalated/30">
                        Medium Priority
                      </Badge>
                    </Label>
                    <p className="text-sm text-muted-foreground">
                      Notifications for escalated situations
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label className="flex items-center gap-2">
                      P3 Controlled Alerts
                      <Badge className="bg-status-controlled/20 text-status-controlled border-status-controlled/30">
                        Low Priority
                      </Badge>
                    </Label>
                    <p className="text-sm text-muted-foreground">
                      Updates on controlled situations
                    </p>
                  </div>
                  <Switch />
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Sound Alerts</Label>
                    <p className="text-sm text-muted-foreground">
                      Play audio for critical notifications
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Volume2 className="size-4 text-muted-foreground" />
                    <Switch defaultChecked />
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Browser Notifications</Label>
                    <p className="text-sm text-muted-foreground">
                      Show desktop notifications
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* API Configuration */}
          <TabsContent value="api" className="space-y-6">
            <Card className="border-border/50 bg-card/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base font-semibold">
                  <Database className="size-5" />
                  Backend Configuration
                </CardTitle>
                <CardDescription>
                  Configure connection to your FastAPI backend
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label>API Base URL</Label>
                  <Input
                    type="url"
                    placeholder="http://localhost:8000"
                    defaultValue="http://localhost:8000"
                    className="font-mono text-sm"
                  />
                  <p className="text-xs text-muted-foreground">
                    The base URL for your FastAPI backend server
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>WebSocket URL</Label>
                  <Input
                    type="url"
                    placeholder="ws://localhost:8000/ws"
                    defaultValue="ws://localhost:8000/ws"
                    className="font-mono text-sm"
                  />
                  <p className="text-xs text-muted-foreground">
                    WebSocket endpoint for real-time updates
                  </p>
                </div>

                <Separator />

                <div className="space-y-2">
                  <Label>API Key</Label>
                  <div className="flex gap-2">
                    <Input
                      type="password"
                      placeholder="Enter your API key"
                      className="font-mono text-sm"
                    />
                    <Button variant="outline" size="icon">
                      <Key className="size-4" />
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Optional API key for authenticated requests
                  </p>
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Auto-retry on failure</Label>
                    <p className="text-sm text-muted-foreground">
                      Automatically retry failed API requests
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>

                <div className="rounded-lg border border-border/50 bg-muted/30 p-4">
                  <h4 className="mb-2 font-medium">API Endpoints Reference</h4>
                  <div className="space-y-1 font-mono text-xs text-muted-foreground">
                    <p>GET  /api/reports - List all reports</p>
                    <p>POST /api/reports - Create new report</p>
                    <p>GET  /api/kpis - Get dashboard KPIs</p>
                    <p>GET  /api/analytics - Get analytics data</p>
                    <p>GET  /api/health - System health check</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Account Settings */}
          <TabsContent value="account" className="space-y-6">
            <Card className="border-border/50 bg-card/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base font-semibold">
                  <User className="size-5" />
                  User Profile
                </CardTitle>
                <CardDescription>
                  Manage your account information
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center gap-4">
                  <div className="flex size-16 items-center justify-center rounded-full bg-primary/10">
                    <User className="size-8 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">Admin User</p>
                    <p className="text-sm text-muted-foreground">admin@ldsn.cm</p>
                    <Badge variant="outline" className="mt-1">System Administrator</Badge>
                  </div>
                </div>

                <Separator />

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Full Name</Label>
                    <Input defaultValue="Admin User" />
                  </div>
                  <div className="space-y-2">
                    <Label>Email</Label>
                    <Input type="email" defaultValue="admin@ldsn.cm" />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Organization</Label>
                  <Input defaultValue="Ministry of Livestock, Fisheries and Animal Industries" />
                </div>
              </CardContent>
            </Card>

            <Card className="border-border/50 bg-card/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base font-semibold">
                  <Shield className="size-5" />
                  Security
                </CardTitle>
                <CardDescription>
                  Manage your security settings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Two-Factor Authentication</Label>
                    <p className="text-sm text-muted-foreground">
                      Add an extra layer of security
                    </p>
                  </div>
                  <Switch />
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Session Timeout</Label>
                    <p className="text-sm text-muted-foreground">
                      Auto-logout after inactivity
                    </p>
                  </div>
                  <Select defaultValue="30">
                    <SelectTrigger className="w-[140px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="15">15 minutes</SelectItem>
                      <SelectItem value="30">30 minutes</SelectItem>
                      <SelectItem value="60">1 hour</SelectItem>
                      <SelectItem value="never">Never</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button variant="outline" className="w-full bg-transparent">
                  Change Password
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Save Button */}
        <div className="flex justify-end">
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <span className="mr-2 size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 size-4" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>
    </DashboardLayout>
  )
}
