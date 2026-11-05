import { describe, it, expect, afterEach } from 'vitest'
import { useFilters } from '../src/composables/useFilters.js'

const filters = useFilters()

afterEach(() => filters.resetFilters())

describe('useFilters', () => {
  it('starts with no active filters', () => {
    expect(filters.hasActiveFilters.value).toBe(false)
    expect(filters.getCurrentFilters()).toEqual({ warehouse: 'all', category: 'all', status: 'all' })
  })

  it('maps the period to the month param', () => {
    filters.selectedPeriod.value = 'Q2-2025'
    filters.selectedLocation.value = 'Tokyo'
    expect(filters.getCurrentFilters()).toEqual({
      warehouse: 'Tokyo',
      category: 'all',
      status: 'all',
      month: 'Q2-2025'
    })
    expect(filters.hasActiveFilters.value).toBe(true)
  })

  it('shares state between callers', () => {
    filters.selectedStatus.value = 'Delivered'
    expect(useFilters().getCurrentFilters().status).toBe('Delivered')
  })

  it('resets all filters', () => {
    filters.selectedCategory.value = 'Sensors'
    filters.selectedPeriod.value = '2025-01'
    filters.resetFilters()
    expect(filters.hasActiveFilters.value).toBe(false)
  })
})
