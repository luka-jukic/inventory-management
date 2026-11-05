import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api'

const client = axios.create({ baseURL: API_BASE_URL })
if (import.meta.env.VITE_API_TOKEN) {
  client.defaults.headers.common['X-API-Token'] = import.meta.env.VITE_API_TOKEN
}

const FILTER_KEYS = ['warehouse', 'category', 'status', 'month']

// Build params from filters, skipping empty/'all' values
const buildParams = (filters, keys = FILTER_KEYS) => {
  const params = {}
  for (const k of keys) {
    if (filters[k] && filters[k] !== 'all') params[k] = filters[k]
  }
  return params
}

const get = async (url, params, options = {}) =>
  (await client.get(url, { params, signal: options.signal })).data

export const api = {
  getInventory: (filters = {}, options = {}) =>
    get('/inventory', buildParams(filters, ['warehouse', 'category']), options),

  getInventoryItem: (id, options = {}) => get(`/inventory/${id}`, undefined, options),

  getOrders: (filters = {}, options = {}) => get('/orders', buildParams(filters), options),

  getOrder: (id, options = {}) => get(`/orders/${id}`, undefined, options),

  getDemandForecasts: (options = {}) => get('/demand', undefined, options),

  getBacklog: (filters = {}, options = {}) => get('/backlog', buildParams(filters), options),

  getDashboardSummary: (filters = {}, options = {}) =>
    get('/dashboard/summary', buildParams(filters), options),

  getTopProducts: (filters = {}, options = {}) =>
    get('/dashboard/top-products', buildParams(filters), options),

  getSpendingSummary: (filters = {}, options = {}) =>
    get('/spending/summary', buildParams(filters, ['month']), options),

  getMonthlySpending: (options = {}) => get('/spending/monthly', undefined, options),

  getCategorySpending: (options = {}) => get('/spending/categories', undefined, options),

  getTransactions: (filters = {}, options = {}) =>
    get('/spending/transactions', buildParams(filters, ['month']), options),

  getTasks: (options = {}) => get('/tasks', undefined, options),

  async createTask(taskData, options = {}) {
    return (await client.post('/tasks', taskData, { signal: options.signal })).data
  },

  async deleteTask(taskId, options = {}) {
    return (await client.delete(`/tasks/${taskId}`, { signal: options.signal })).data
  },

  async toggleTask(taskId, options = {}) {
    return (await client.patch(`/tasks/${taskId}`, undefined, { signal: options.signal })).data
  },

  async createPurchaseOrder(purchaseOrderData, options = {}) {
    return (await client.post('/purchase-orders', purchaseOrderData, { signal: options.signal })).data
  },

  getQuarterlyReports: (filters = {}, options = {}) =>
    get('/reports/quarterly', buildParams(filters), options),

  getMonthlyTrends: (filters = {}, options = {}) =>
    get('/reports/monthly-trends', buildParams(filters), options),

  getPurchaseOrderByBacklogItem: (backlogItemId, options = {}) =>
    get(`/purchase-orders/${backlogItemId}`, undefined, options)
}

export const isCanceled = (err) => axios.isCancel(err) || err?.name === 'CanceledError'
