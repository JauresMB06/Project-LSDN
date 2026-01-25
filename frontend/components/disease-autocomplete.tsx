'use client'

import * as React from 'react'
import { Check, ChevronsUpDown, Search } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Badge } from '@/components/ui/badge'
import { api } from '@/lib/api'

interface DiseaseAutocompleteProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}

export function DiseaseAutocomplete({
  value,
  onChange,
  placeholder = "Search diseases...",
  className,
}: DiseaseAutocompleteProps) {
  const [open, setOpen] = React.useState(false)
  const [searchValue, setSearchValue] = React.useState('')
  const [diseases, setDiseases] = React.useState<Array<{id: string, name: string, category: string}>>([])
  const [loading, setLoading] = React.useState(false)

  // Fetch autocomplete suggestions based on search value
  React.useEffect(() => {
    const fetchSuggestions = async () => {
      if (searchValue.length < 2) {
        setDiseases([])
        return
      }

      try {
        setLoading(true)
        const response = await fetch(`http://localhost:8000/api/trie/autocomplete?prefix=${encodeURIComponent(searchValue)}&limit=10`)
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        const data = await response.json()

        // Map Trie suggestions to disease format
        const diseaseList = data.suggestions.map((suggestion: string, index: number) => ({
          id: (index + 1).toString(),
          name: suggestion,
          category: 'Disease/Symptom'
        }))
        setDiseases(diseaseList)
      } catch (error) {
        console.error('Failed to fetch autocomplete suggestions:', error)
        setDiseases([])
      } finally {
        setLoading(false)
      }
    }

    const debounceTimer = setTimeout(fetchSuggestions, 300) // Debounce API calls
    return () => clearTimeout(debounceTimer)
  }, [searchValue])

  // Filter diseases based on search
  const filteredDiseases = React.useMemo(() => {
    if (!searchValue) return diseases
    return diseases.filter(disease =>
      disease.name.toLowerCase().includes(searchValue.toLowerCase()) ||
      disease.category.toLowerCase().includes(searchValue.toLowerCase())
    )
  }, [searchValue, diseases])

  // Group diseases by category
  const groupedDiseases = React.useMemo(() => {
    const groups: Record<string, typeof diseases> = {}
    filteredDiseases.forEach(disease => {
      if (!groups[disease.category]) {
        groups[disease.category] = []
      }
      groups[disease.category].push(disease)
    })
    return groups
  }, [filteredDiseases])

  const selectedDisease = diseases.find(d => d.name === value)

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn("w-full justify-between", className)}
        >
          {selectedDisease ? (
            <div className="flex items-center gap-2">
              <span>{selectedDisease.name}</span>
              <Badge variant="secondary" className="text-xs">
                {selectedDisease.category}
              </Badge>
            </div>
          ) : (
            <span className="text-muted-foreground">{placeholder}</span>
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-full p-0" align="start">
        <Command>
          <CommandInput
            placeholder="Search diseases..."
            value={searchValue}
            onValueChange={setSearchValue}
          />
          <CommandList>
            <CommandEmpty>No diseases found.</CommandEmpty>
            {Object.entries(groupedDiseases).map(([category, diseases]) => (
              <CommandGroup key={category} heading={category}>
                {diseases.map((disease) => (
                  <CommandItem
                    key={disease.id}
                    value={disease.name}
                    onSelect={() => {
                      onChange(disease.name === value ? '' : disease.name)
                      setOpen(false)
                      setSearchValue('')
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        value === disease.name ? "opacity-100" : "opacity-0"
                      )}
                    />
                    <div className="flex flex-col">
                      <span>{disease.name}</span>
                      <span className="text-xs text-muted-foreground">
                        {disease.category}
                      </span>
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            ))}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
