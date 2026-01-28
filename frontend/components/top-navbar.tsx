'use client'

import * as React from 'react'
import { Search, Bell, User } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Badge } from '@/components/ui/badge'
import { Kbd } from '@/components/ui/kbd'
import { api } from '@/lib/api'

interface TopNavbarProps {
  onDiseaseSelect?: (disease: string) => void
}

export function TopNavbar({ onDiseaseSelect }: TopNavbarProps) {
  const [open, setOpen] = React.useState(false)
  const [diseases, setDiseases] = React.useState<Array<{id: string, name: string, category: string}>>([])

  // Load diseases on component mount using Trie API
  React.useEffect(() => {
    const loadDiseases = async () => {
      try {
        // Use Trie autocomplete with empty prefix to get initial suggestions
        const response = await fetch('http://localhost:8000/api/trie/autocomplete?prefix=&limit=20')
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        const data = await response.json()

        // Transform Trie suggestions to disease format
        const diseaseList = data.suggestions.map((name: string, index: number) => ({
          id: (index + 1).toString(),
          name,
          category: 'Disease/Symptom'
        }))
        setDiseases(diseaseList)
      } catch (error) {
        console.error('Failed to load diseases:', error)
        // Fallback to empty array if API fails
        setDiseases([])
      }
    }

    loadDiseases()
  }, [])

  const handleDiseaseSelect = (disease: string) => {
    onDiseaseSelect?.(disease)
    setOpen(false)
  }

  return (
    <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
      <SidebarTrigger className="-ml-1" />
      <div className="flex flex-1 items-center gap-2">
        {/* Disease Search - Simplified to avoid hydration mismatch */}
        <div className="relative">
          <div className="relative w-80">
            <input
              type="text"
              placeholder="Search diseases..."
              className="flex h-9 w-full rounded-md bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              onFocus={() => setOpen(true)}
              onBlur={() => setTimeout(() => setOpen(false), 200)}
            />
            <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          </div>

          {open && diseases.length > 0 && (
            <div className="absolute top-full z-50 w-full mt-1 rounded-md border bg-popover p-1 shadow-md">
              <div className="px-2 py-1.5 text-sm font-medium text-muted-foreground">
                Diseases
              </div>
              {diseases.slice(0, 5).map((d) => (
                <div
                  key={d.id}
                  className="flex items-center px-2 py-1.5 text-sm cursor-pointer hover:bg-accent hover:text-accent-foreground rounded-sm"
                  onClick={() => handleDiseaseSelect(d.name)}
                >
                  <Search className="mr-2 h-4 w-4" />
                  <span>{d.name}</span>
                  <Badge variant="secondary" className="ml-auto text-xs">
                    {d.category}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Keyboard Shortcut */}
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Kbd>⌘</Kbd>
          <Kbd>K</Kbd>
        </div>
      </div>

      {/* Right side actions */}
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" className="h-8 w-8">
          <Bell className="h-4 w-4" />
          <span className="sr-only">Notifications</span>
        </Button>
        <Button variant="ghost" size="icon" className="h-8 w-8">
          <User className="h-4 w-4" />
          <span className="sr-only">Account</span>
        </Button>
      </div>
    </header>
  )
}
