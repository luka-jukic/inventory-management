import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

const getBacklog = vi.hoisted(() => vi.fn())

vi.mock('../src/api', () => ({
  api: { getBacklog },
  isCanceled: (err) => err?.name === 'CanceledError'
}))

import Backlog from '../src/views/Backlog.vue'
import { useFilters } from '../src/composables/useFilters.js'

const item = (id, priority) => ({
  id,
  order_id: `ORD-2025-000${id}`,
  item_sku: `SKU-${id}`,
  item_name: `Item ${id}`,
  quantity_needed: 10,
  quantity_available: 2,
  days_delayed: 1,
  priority,
  has_purchase_order: false
})

const filters = useFilters()
let wrapper

beforeEach(() => {
  getBacklog.mockReset()
  getBacklog.mockResolvedValue([item('1', 'high'), item('2', 'low')])
})

afterEach(() => {
  wrapper?.unmount()
  filters.resetFilters()
})

describe('Backlog view', () => {
  it('loads backlog with the current filters and renders the rows', async () => {
    filters.selectedLocation.value = 'Tokyo'
    wrapper = mount(Backlog)
    await flushPromises()

    const [sentFilters, options] = getBacklog.mock.calls[0]
    expect(sentFilters).toMatchObject({ warehouse: 'Tokyo' })
    expect(options.signal).toBeInstanceOf(AbortSignal)
    expect(wrapper.findAll('tbody tr')).toHaveLength(2)
  })

  // Regression: the view used to reload only on warehouse/category changes
  it.each([
    ['selectedPeriod', 'Q1-2025', { month: 'Q1-2025' }],
    ['selectedStatus', 'Backordered', { status: 'Backordered' }],
    ['selectedCategory', 'Sensors', { category: 'Sensors' }]
  ])('reloads when %s changes', async (name, value, expected) => {
    wrapper = mount(Backlog)
    await flushPromises()
    filters[name].value = value
    await nextTick()
    await flushPromises()
    expect(getBacklog).toHaveBeenCalledTimes(2)
    expect(getBacklog.mock.calls[1][0]).toMatchObject(expected)
  })

  it('aborts the previous request when filters change', async () => {
    wrapper = mount(Backlog)
    const firstSignal = getBacklog.mock.calls[0][1].signal
    filters.selectedLocation.value = 'London'
    await nextTick()
    expect(firstSignal.aborted).toBe(true)
  })

  it('aborts the pending request on unmount', async () => {
    wrapper = mount(Backlog)
    const signal = getBacklog.mock.calls[0][1].signal
    wrapper.unmount()
    wrapper = null
    expect(signal.aborted).toBe(true)
  })

  it('shows an error when loading fails, but not for canceled requests', async () => {
    getBacklog.mockRejectedValueOnce(Object.assign(new Error('canceled'), { name: 'CanceledError' }))
    wrapper = mount(Backlog)
    await flushPromises()
    expect(wrapper.text()).not.toContain('canceled')

    getBacklog.mockRejectedValueOnce(new Error('Network Error'))
    filters.selectedLocation.value = 'Tokyo'
    await nextTick()
    await flushPromises()
    expect(wrapper.text()).toContain('Network Error')
  })
})
