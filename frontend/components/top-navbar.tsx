'use client'

import * as React from 'react'
import { Search, Bell, User } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
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
        {/* Disease Search */}
        <div className="relative">
          <Command className="w-80">
            <CommandInput
              placeholder="Search diseases..."
              className="h-9"
              onFocus={() => setOpen(true)}
              onBlur={() => setTimeout(() => setOpen(false), 200)}
            />
            {open && (
              <div className="absolute top-full z-50 w-full rounded-md border bg-popover p-0 shadow-md">
                <CommandList>
                  <CommandEmpty>No diseases found.</CommandEmpty>
                  <CommandGroup heading="Diseases">
                    {diseases.map((d) => (
                      <CommandItem
                        key={d.id}
                        value={d.name}
                        onSelect={() => handleDiseaseSelect(d.name)}
                      >
                        <Search className="mr-2 h-4 w-4" />
                        <span>{d.name}</span>
                        <Badge variant="secondary" className="ml-auto text-xs">
                          {d.category}
                        </Badge>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </CommandList>
              </div>
            )}
          </Command>
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
