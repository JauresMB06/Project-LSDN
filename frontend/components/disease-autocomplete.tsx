'use client'

import * as React from 'react'
import { Check, Search } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Input } from '@/components/ui/input'
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
} from '@/components/ui/popover'

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
  const [inputValue, setInputValue] = React.useState(value || '')
  const [diseases, setDiseases] = React.useState<Array<{id: string, name: string, category: string}>>([])
  const [loading, setLoading] = React.useState(false)

  // Sync input value with external value changes
  React.useEffect(() => {
    if (value !== inputValue) {
      setInputValue(value)
    }
  }, [value])

  // Fetch autocomplete suggestions based on input value
  React.useEffect(() => {
    const fetchSuggestions = async () => {
      if (inputValue.length < 2) {
        setDiseases([])
        setOpen(false)
        return
      }

      try {
        setLoading(true)
        const response = await fetch(`http://localhost:8000/api/trie/autocomplete?prefix=${encodeURIComponent(inputValue)}&limit=10`)
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
        setOpen(diseaseList.length > 0)
      } catch (error) {
        console.error('Failed to fetch autocomplete suggestions:', error)
        setDiseases([])
        setOpen(false)
      } finally {
        setLoading(false)
      }
    }

    const debounceTimer = setTimeout(fetchSuggestions, 300) // Debounce API calls
    return () => clearTimeout(debounceTimer)
  }, [inputValue])

  const handleInputChange = (newValue: string) => {
    setInputValue(newValue)
    onChange(newValue) // Update parent component immediately
  }

  const handleSelect = (diseaseName: string) => {
    setInputValue(diseaseName)
    onChange(diseaseName)
    setOpen(false)
  }

  return (
    <div className="relative">
      <div className="relative">
        <Input
          type="text"
          placeholder={placeholder}
          value={inputValue}
          onChange={(e) => handleInputChange(e.target.value)}
          className={cn("pr-10", className)}
        />
        <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      </div>

      {open && diseases.length > 0 && (
        <div className="absolute top-full z-50 w-full mt-1 bg-popover border border-border rounded-md shadow-md">
          <div className="p-1">
            <div className="px-2 py-1.5 text-sm font-medium text-muted-foreground">
              Disease/Symptom
            </div>
            {diseases.map((disease) => (
              <div
                key={disease.id}
                className="flex items-center px-2 py-1.5 text-sm cursor-pointer hover:bg-accent hover:text-accent-foreground rounded-sm"
                onClick={() => handleSelect(disease.name)}
              >
                <Check
                  className={cn(
                    "mr-2 h-4 w-4",
                    inputValue === disease.name ? "opacity-100" : "opacity-0"
                  )}
                />
                <span>{disease.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
