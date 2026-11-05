import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// One fake axios instance shared by every api.js call
const http = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
  defaults: { headers: { common: {} } }
}))

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => http),
    isCancel: (err) => err?.__CANCEL__ === true
  }
}))

const loadApi = async () => {
  vi.resetModules()
  return import('../src/api.js')
}

beforeEach(() => {
  vi.clearAllMocks()
  http.defaults.headers.common = {}
  http.get.mockResolvedValue({ data: [] })
})

afterEach(() => vi.unstubAllEnvs())

describe('api filter params', () => {
  it('skips "all" and empty filters', async () => {
    const { api } = await loadApi()
    await api.getOrders({ warehouse: 'all', category: '', status: 'Delivered', month: 'Q1-2025' })
    expect(http.get).toHaveBeenCalledWith('/orders', {
      params: { status: 'Delivered', month: 'Q1-2025' },
      signal: undefined
    })
  })

  it('sends only warehouse and category for inventory', async () => {
    const { api } = await loadApi()
    await api.getInventory({ warehouse: 'Tokyo', category: 'Sensors', status: 'Delivered', month: '2025-01' })
    expect(http.get.mock.calls[0][1].params).toEqual({ warehouse: 'Tokyo', category: 'Sensors' })
  })

  it('passes the abort signal through', async () => {
    const { api } = await loadApi()
    const ctrl = new AbortController()
    await api.getBacklog({ warehouse: 'Tokyo' }, { signal: ctrl.signal })
    expect(http.get).toHaveBeenCalledWith('/backlog', { params: { warehouse: 'Tokyo' }, signal: ctrl.signal })
  })

  it('returns the response data', async () => {
    http.get.mockResolvedValue({ data: [{ id: '1' }] })
    const { api } = await loadApi()
    expect(await api.getBacklog()).toEqual([{ id: '1' }])
  })
})

describe('api token', () => {
  it('sends X-API-Token when VITE_API_TOKEN is set', async () => {
    vi.stubEnv('VITE_API_TOKEN', 'secret')
    await loadApi()
    expect(http.defaults.headers.common['X-API-Token']).toBe('secret')
  })

  it('sends no token header by default', async () => {
    vi.stubEnv('VITE_API_TOKEN', '')
    await loadApi()
    expect(http.defaults.headers.common).not.toHaveProperty('X-API-Token')
  })
})

describe('isCanceled', () => {
  it('detects canceled requests', async () => {
    const { isCanceled } = await loadApi()
    expect(isCanceled({ name: 'CanceledError' })).toBe(true)
    expect(isCanceled({ __CANCEL__: true })).toBe(true)
    expect(isCanceled(new Error('Network Error'))).toBe(false)
    expect(isCanceled(undefined)).toBe(false)
  })
})
