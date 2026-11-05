import { describe, it, expect } from 'vitest'
import { parseLocalDate } from '../src/utils/dates'

describe('parseLocalDate', () => {
  it('keeps the local calendar day of a date-only string', () => {
    const d = parseLocalDate('2025-11-10')
    expect([d.getFullYear(), d.getMonth(), d.getDate()]).toEqual([2025, 10, 10])
    expect(d.getHours()).toBe(0)
  })

  it('keeps the local day west of UTC too', () => {
    const d = parseLocalDate('2025-01-01')
    expect(d.getDate()).toBe(1)
    expect(d.getMonth()).toBe(0)
  })
})
