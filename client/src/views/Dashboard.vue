<template>
  <div class="dashboard">
    <div class="page-header">
      <h2>{{ t('dashboard.title') }}</h2>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Key Performance Indicators -->
      <div class="kpi-section">
        <h3 class="section-title">{{ t('dashboard.kpi.title') }}</h3>
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-header">
              <span class="kpi-label">{{ t('dashboard.kpi.inventoryTurnover') }}</span>
            </div>
            <div class="kpi-value">{{ kpis.turnover.display }}</div>
            <div class="kpi-goal">{{ t('dashboard.kpi.goal') }}: 4.5 ({{ kpis.turnover.delta }})</div>
            <div class="kpi-progress-bar">
              <div class="kpi-progress" :class="{ success: kpis.turnover.good }" :style="{ width: kpis.turnover.width + '%' }"></div>
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-header">
              <span class="kpi-label">{{ t('dashboard.kpi.ordersFulfilled') }}</span>
            </div>
            <div class="kpi-value">{{ kpis.fulfilled.display }}</div>
            <div class="kpi-goal">{{ t('dashboard.kpi.goal') }}: 200 ({{ kpis.fulfilled.delta }})</div>
            <div class="kpi-progress-bar">
              <div class="kpi-progress" :class="{ success: kpis.fulfilled.good }" :style="{ width: kpis.fulfilled.width + '%' }"></div>
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-header">
              <span class="kpi-label">{{ t('dashboard.kpi.orderFillRate') }}</span>
            </div>
            <div class="kpi-value">{{ kpis.fillRate.display }}%</div>
            <div class="kpi-goal">{{ t('dashboard.kpi.goal') }}: 95% ({{ kpis.fillRate.delta }})</div>
            <div class="kpi-progress-bar">
              <div class="kpi-progress" :class="{ success: kpis.fillRate.good }" :style="{ width: kpis.fillRate.width + '%' }"></div>
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-header">
              <span class="kpi-label">{{ t(selectedPeriod === 'all' ? 'dashboard.kpi.revenueYTD' : 'dashboard.kpi.revenueMTD') }}</span>
            </div>
            <div class="kpi-value">{{ formatCurrency(Math.round(summary.total_orders_value), selectedCurrency) }}</div>
            <div class="kpi-goal">{{ t('dashboard.kpi.goal') }}: {{ formatCurrency(summary.revenue_goal, selectedCurrency) }} ({{ summary.total_orders_value > summary.revenue_goal ? '+' : '' }}{{ ((summary.total_orders_value / summary.revenue_goal - 1) * 100).toFixed(1) }}%)</div>
            <div class="kpi-progress-bar">
              <div class="kpi-progress" :style="{ width: Math.min((summary.total_orders_value / summary.revenue_goal * 100), 100) + '%' }"></div>
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-header">
              <span class="kpi-label">{{ t('dashboard.kpi.avgProcessingTime') }}</span>
            </div>
            <div class="kpi-value">{{ kpis.processing.display }}</div>
            <div class="kpi-goal">{{ t('dashboard.kpi.goal') }}: 3.0 ({{ kpis.processing.delta }})</div>
            <div class="kpi-progress-bar">
              <div class="kpi-progress" :class="{ success: kpis.processing.good }" :style="{ width: kpis.processing.width + '%' }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Summary Section -->
      <div class="summary-section">
        <h3 class="section-title">{{ t('dashboard.summary.title') }}</h3>
      </div>

      <!-- Charts Grid -->
      <div class="charts-grid">
        <!-- Order Health Dashboard -->
        <div class="card chart-card">
          <div class="card-header">
            <h3 class="card-title">{{ t('dashboard.orderHealth.title') }}</h3>
          </div>
          <div class="chart-content">
            <div class="order-health-container">
              <!-- Left: Donut Chart -->
              <div class="order-health-chart">
                <svg viewBox="0 0 200 200" class="donut-svg-compact">
                  <circle cx="100" cy="100" r="65" fill="none" stroke="var(--border)" stroke-width="25"/>
                  <circle cx="100" cy="100" r="65" fill="none" stroke="#10b981" stroke-width="25"
                    :stroke-dasharray="`${getCircleSegment(statusData.delivered)} 408`"
                    stroke-dashoffset="0" transform="rotate(-90 100 100)"/>
                  <circle cx="100" cy="100" r="65" fill="none" stroke="#3b82f6" stroke-width="25"
                    :stroke-dasharray="`${getCircleSegment(statusData.shipped)} 408`"
                    :stroke-dashoffset="`-${getCircleSegment(statusData.delivered)}`"
                    transform="rotate(-90 100 100)"/>
                  <circle cx="100" cy="100" r="65" fill="none" stroke="#f59e0b" stroke-width="25"
                    :stroke-dasharray="`${getCircleSegment(statusData.processing)} 408`"
                    :stroke-dashoffset="`-${getCircleSegment(statusData.delivered) + getCircleSegment(statusData.shipped)}`"
                    transform="rotate(-90 100 100)"/>
                  <circle cx="100" cy="100" r="65" fill="none" stroke="#ef4444" stroke-width="25"
                    :stroke-dasharray="`${getCircleSegment(statusData.backordered)} 408`"
                    :stroke-dashoffset="`-${getCircleSegment(statusData.delivered) + getCircleSegment(statusData.shipped) + getCircleSegment(statusData.processing)}`"
                    transform="rotate(-90 100 100)"/>
                  <text x="100" y="90" text-anchor="middle" class="donut-center-label">{{ t('dashboard.orderHealth.total') }}</text>
                  <text x="100" y="120" text-anchor="middle" class="donut-center-value">{{ summary.total_orders }}</text>
                </svg>
                <div class="donut-legend-compact">
                  <div class="legend-item-compact"><span class="legend-dot" style="background: #10b981"></span>{{ t('status.delivered') }}</div>
                  <div class="legend-item-compact"><span class="legend-dot" style="background: #3b82f6"></span>{{ t('status.shipped') }}</div>
                  <div class="legend-item-compact"><span class="legend-dot" style="background: #f59e0b"></span>{{ t('status.processing') }}</div>
                  <div class="legend-item-compact"><span class="legend-dot" style="background: #ef4444"></span>{{ t('status.backordered') }}</div>
                </div>
              </div>

              <!-- Right: Health Metrics -->
              <div class="order-health-metrics">
                <div class="health-metric">
                  <div class="health-metric-label">{{ t('dashboard.orderHealth.revenue') }}</div>
                  <div class="health-metric-value">{{ formatCurrency(summary.total_orders_value, selectedCurrency) }}</div>
                </div>
                <div class="health-metric">
                  <div class="health-metric-label">{{ t('dashboard.orderHealth.avgOrderValue') }}</div>
                  <div class="health-metric-value">{{ formatCurrency(summary.avg_order_value, selectedCurrency) }}</div>
                </div>
                <div class="health-metric">
                  <div class="health-metric-label">{{ t('dashboard.orderHealth.onTimeRate') }}</div>
                  <div class="health-metric-value" :class="{ 'metric-good': summary.on_time_rate >= 90, 'metric-warning': summary.on_time_rate < 90 && summary.on_time_rate >= 75, 'metric-bad': summary.on_time_rate < 75 }">
                    {{ summary.on_time_rate == null ? '\u2014' : summary.on_time_rate.toFixed(1) + '%' }}
                  </div>
                </div>
                <div class="health-metric">
                  <div class="health-metric-label">{{ t('dashboard.orderHealth.avgFulfillmentDays') }}</div>
                  <div class="health-metric-value">{{ summary.avg_processing_days == null ? '\u2014' : summary.avg_processing_days.toFixed(1) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Inventory by Category -->
        <div class="card chart-card">
          <div class="card-header">
            <h3 class="card-title">{{ t('dashboard.inventoryValue.title') }}</h3>
          </div>
          <div class="chart-content">
            <div class="horizontal-bar-chart" v-if="categoryData.length > 0">
              <div v-for="cat in categoryData" :key="cat.name" class="h-bar-item">
                <div class="h-bar-label">{{ translateCategory(cat.name) }}</div>
                <div class="h-bar-container">
                  <div class="h-bar" :style="{ width: (cat.value / maxCategoryValue * 100) + '%', background: cat.color }">
                    <span class="h-bar-value">{{ formatCategoryValue(cat.value) }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="no-data">{{ t('dashboard.inventoryShortages.noData') }}</div>
          </div>
        </div>

        <!-- Inventory Shortages -->
        <div class="card chart-card full-width">
          <div class="card-header">
            <h3 class="card-title">{{ t('dashboard.inventoryShortages.title') }} ({{ backlogItems.length }})</h3>
          </div>
          <div v-if="backlogItems.length === 0" class="no-backlog">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="success-icon">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            <p class="no-backlog-text">{{ t('dashboard.inventoryShortages.noShortages') }}</p>
          </div>
          <div v-else class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('dashboard.inventoryShortages.orderId') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.sku') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.itemName') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.quantityNeeded') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.quantityAvailable') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.shortage') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.daysDelayed') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.priority') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.actions') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in backlogItems"
                  :key="item.id"
                  class="clickable-row"
                  tabindex="0"
                  @click="showBacklogDetail(item)"
                  @keydown.enter.self="showBacklogDetail(item)"
                  @keydown.space.self.prevent="showBacklogDetail(item)"
                >
                  <td><strong>{{ item.order_id }}</strong></td>
                  <td><strong>{{ item.item_sku }}</strong></td>
                  <td>{{ translateProductName(item.item_name) }}</td>
                  <td>{{ item.quantity_needed }}</td>
                  <td>{{ item.quantity_available }}</td>
                  <td>
                    <span class="badge danger">
                      {{ Math.abs(item.quantity_needed - item.quantity_available) }} {{ t('dashboard.inventoryShortages.unitsShort') }}
                    </span>
                  </td>
                  <td>
                    <span :style="{ color: item.days_delayed > 7 ? '#ef4444' : '#f59e0b', fontWeight: 600 }">
                      {{ item.days_delayed }} {{ t('dashboard.inventoryShortages.days') }}
                    </span>
                  </td>
                  <td>
                    <span :class="['badge', item.priority]">
                      {{ translatePriority(item.priority) }}
                    </span>
                  </td>
                  <td>
                    <button
                      v-if="!item.has_purchase_order"
                      @click.stop="openPOModal(item)"
                      class="po-button create"
                    >
                      {{ t('dashboard.inventoryShortages.createPO') }}
                    </button>
                    <button
                      v-else
                      @click.stop="viewPO(item)"
                      class="po-button view"
                    >
                      {{ t('dashboard.inventoryShortages.viewPO') }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Top Products Table -->
        <div class="card chart-card full-width">
          <div class="card-header">
            <h3 class="card-title">{{ t('dashboard.topProducts.title') }}</h3>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('dashboard.topProducts.product') }}</th>
                  <th>{{ t('dashboard.topProducts.sku') }}</th>
                  <th>{{ t('dashboard.topProducts.category') }}</th>
                  <th>{{ t('dashboard.topProducts.unitsOrdered') }}</th>
                  <th>{{ t('dashboard.topProducts.revenue') }}</th>
                  <th>{{ t('dashboard.topProducts.firstOrder') }}</th>
                  <th>{{ t('dashboard.topProducts.stockStatus') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in topProducts"
                  :key="item.sku"
                  class="clickable-row"
                  tabindex="0"
                  @click="showProductDetail(item)"
                  @keydown.enter.self="showProductDetail(item)"
                  @keydown.space.self.prevent="showProductDetail(item)"
                >
                  <td><strong>{{ translateProductName(item.name) }}</strong></td>
                  <td>{{ item.sku }}</td>
                  <td>{{ translateCategory(item.category) }}</td>
                  <td>{{ item.unitsOrdered }}</td>
                  <td><strong>{{ formatCurrency(item.revenue, selectedCurrency) }}</strong></td>
                  <td>{{ formatDate(item.firstOrderDate) }}</td>
                  <td>
                    <span :class="['badge', getStockBadge(item.stockLevel)]">
                      {{ translateStockLevel(item.stockLevel) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <ProductDetailModal
      :is-open="showProductModal"
      :product="selectedProduct"
      @close="showProductModal = false"
    />

    <BacklogDetailModal
      :is-open="showBacklogModal"
      :backlog-item="selectedBacklogItem"
      @close="showBacklogModal = false"
    />

    <PurchaseOrderModal
      :is-open="showPOModal"
      :backlog-item="selectedBacklogForPO"
      :mode="poModalMode"
      :unit-cost="selectedPOUnitCost"
      @close="showPOModal = false"
      @po-created="handlePOCreated"
    />
  </div>
</template>

<script>
import { ref, shallowRef, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { api, isCanceled } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'
import ProductDetailModal from '../components/ProductDetailModal.vue'
import BacklogDetailModal from '../components/BacklogDetailModal.vue'
import PurchaseOrderModal from '../components/PurchaseOrderModal.vue'

export default {
  name: 'Dashboard',
  components: {
    ProductDetailModal,
    BacklogDetailModal,
    PurchaseOrderModal,
  },
  setup() {
    const { t, currentLocale, currentCurrency, translateProductName, translateWarehouse } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const summary = ref({})
    const allOrders = shallowRef([]) // replaced, never mutated
    const inventoryItems = ref([])

    // Modal state
    const showProductModal = ref(false)
    const selectedProduct = ref(null)
    const showBacklogModal = ref(false)
    const selectedBacklogItem = ref(null)
    const showPOModal = ref(false)
    const selectedBacklogForPO = ref(null)
    const poModalMode = ref('create')

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()


    const statusData = computed(() => ({
      delivered: 0, shipped: 0, processing: 0, backordered: 0,
      ...summary.value.status_counts
    }))

    // Single neutral slate color for all categories
    const categoryData = computed(() =>
      (summary.value.inventory_value_by_category || []).map(c => ({
        name: c.category,
        value: c.value,
        color: '#64748b',
        count: c.count
      }))
    )

    const formatCategoryValue = (value) =>
      currentCurrency.value === 'JPY'
        ? formatCurrency(value, 'JPY')
        : formatCurrencyWithDecimals(value / 1000, 'USD', 1) + 'K'

    const maxCategoryValue = computed(() => {
      if (categoryData.value.length === 0) return 1
      return Math.max(...categoryData.value.map(c => c.value))
    })

    const topProducts = computed(() => {
      // Calculate top products from filtered order data
      const productMap = {}
      const invBySku = new Map(inventoryItems.value.map(i => [i.sku, i]))

      // allOrders is already filtered by API based on: month, warehouse, category, status
      allOrders.value.forEach(order => {
        if (order.items) {
          order.items.forEach(item => {
            const sku = item.sku

            // Find matching inventory item to get full product details
            // Note: inventoryItems is also filtered by API based on: warehouse, category
            const invItem = invBySku.get(sku)

            // Skip products that don't match current inventory filters
            // (e.g., if filtering by warehouse A, don't show products from warehouse B)
            if (!invItem && (selectedLocation.value !== 'all' || selectedCategory.value !== 'all')) {
              return // Skip this product as it doesn't match inventory filters
            }

            if (!productMap[sku]) {
              productMap[sku] = {
                name: item.name,
                sku: sku,
                category: invItem?.category || 'Unknown',
                warehouse: invItem?.warehouse || 'Unknown',
                unitsOrdered: 0,
                revenue: 0,
                stockLevel: invItem ? (invItem.quantity_on_hand > invItem.reorder_point ? 'In Stock' : 'Low Stock') : 'Unknown',
                firstOrderDate: order.order_date
              }
            } else {
              // Update to EARLIEST order date (to show January at top when selecting All Months)
              if (order.order_date && (!productMap[sku].firstOrderDate || order.order_date < productMap[sku].firstOrderDate)) {
                productMap[sku].firstOrderDate = order.order_date
              }
            }
            productMap[sku].unitsOrdered += item.quantity
            productMap[sku].revenue += item.quantity * item.unit_price
          })
        }
      })

      // Convert to array, sort by first order date (earliest first = January at top), then by revenue, and take top 12
      return Object.values(productMap)
        .sort((a, b) => {
          // Sort by first order date (earliest first)
          // This ensures products first ordered in January appear before those first ordered in December
          const dateA = new Date(a.firstOrderDate || '9999-12-31')
          const dateB = new Date(b.firstOrderDate || '9999-12-31')
          if (dateA.getTime() !== dateB.getTime()) {
            return dateA.getTime() - dateB.getTime() // Earlier dates come first
          }
          // If dates are equal, sort by revenue (highest first)
          return b.revenue - a.revenue
        })
        .slice(0, 12)
    })

    const allBacklogItems = ref([])

    // Server filters backlog by its linked order (all four filters)
    const backlogItems = computed(() => allBacklogItems.value)

    // One AbortController per loader: a new load cancels the previous in-flight one
    let summaryCtrl = null
    let inventoryCtrl = null

    const loadSummary = async () => {
      summaryCtrl?.abort()
      const ctrl = (summaryCtrl = new AbortController())
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()
        const [summaryData, ordersData, backlogData] = await Promise.all([
          api.getDashboardSummary(filters, { signal: ctrl.signal }),
          api.getOrders(filters, { signal: ctrl.signal }),
          api.getBacklog(filters, { signal: ctrl.signal })
        ])
        summary.value = summaryData
        allOrders.value = ordersData
        allBacklogItems.value = backlogData
      } catch (err) {
        if (isCanceled(err)) return
        error.value = t('common.loadFailed', { message: err.message })
      } finally {
        if (summaryCtrl === ctrl) loading.value = false
      }
    }

    const loadInventory = async () => {
      inventoryCtrl?.abort()
      const ctrl = (inventoryCtrl = new AbortController())
      try {
        const filters = getCurrentFilters()
        inventoryItems.value = await api.getInventory(filters, { signal: ctrl.signal })
      } catch (err) {
        if (isCanceled(err)) return
        error.value = t('common.loadFailed', { message: err.message })
      }
    }

    onBeforeUnmount(() => {
      summaryCtrl?.abort()
      inventoryCtrl?.abort()
    })

    const KPI_GOALS = { turnover: 4.5, fulfilled: 200, fillRate: 95, processing: 3.0 }
    const makeKpi = (value, goal, lowerBetter = false) => {
      if (value == null) return { display: '\u2014', delta: '\u2014', width: 0, good: false }
      const ratio = lowerBetter ? goal / value : value / goal
      const delta = (value / goal - 1) * 100
      return {
        display: value,
        delta: (delta > 0 ? '+' : '') + delta.toFixed(1) + '%',
        width: Math.max(0, Math.min(100, ratio * 100)),
        good: lowerBetter ? value <= goal : value >= goal
      }
    }
    const kpis = computed(() => ({
      turnover: makeKpi(summary.value.inventory_turnover, KPI_GOALS.turnover),
      fulfilled: makeKpi(summary.value.orders_fulfilled, KPI_GOALS.fulfilled),
      fillRate: makeKpi(summary.value.order_fill_rate, KPI_GOALS.fillRate),
      processing: makeKpi(summary.value.avg_processing_days, KPI_GOALS.processing, true)
    }))

    // Compute total orders once for efficiency
    const totalOrders = computed(() => summary.value.total_orders || 0)

    const getCircleSegment = (value) => {
      return totalOrders.value > 0 ? (value / totalOrders.value) * 440 : 0
    }

    const getStockBadge = (level) => {
      if (level === 'In Stock') return 'success'
      if (level === 'Low Stock') return 'warning'
      return 'danger'
    }

    const translateCategory = (category) => {
      const categoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        'Sensors': t('categories.sensors'),
        'Actuators': t('categories.actuators'),
        'Controllers': t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies')
      }
      return categoryMap[category] || category
    }

    const translateStockLevel = (stockLevel) => {
      const stockMap = {
        'In Stock': t('status.inStock'),
        'Low Stock': t('status.lowStock')
      }
      return stockMap[stockLevel] || stockLevel
    }

    const translatePriority = (priority) => {
      const priorityMap = {
        'high': t('priority.high'),
        'medium': t('priority.medium'),
        'low': t('priority.low'),
        'High': t('priority.high'),
        'Medium': t('priority.medium'),
        'Low': t('priority.low')
      }
      return priorityMap[priority] || priority
    }

    const dateFormatter = computed(() =>
      new Intl.DateTimeFormat(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    )
    const formatDate = (dateString) => {
      if (!dateString) return '-'
      const date = new Date(dateString)
      return isNaN(date.getTime()) ? '-' : dateFormatter.value.format(date)
    }

    const showProductDetail = (product) => {
      selectedProduct.value = product
      showProductModal.value = true
    }

    const showBacklogDetail = (item) => {
      selectedBacklogItem.value = item
      showBacklogModal.value = true
    }

    const selectedPOUnitCost = computed(() => {
      const sku = selectedBacklogForPO.value?.item_sku
      const inv = inventoryItems.value.find(i => i.sku === sku)
      return inv ? inv.unit_cost : null
    })

    const openPOModal = (item) => {
      selectedBacklogForPO.value = item
      poModalMode.value = 'create'
      showPOModal.value = true
    }

    const viewPO = (item) => {
      selectedBacklogForPO.value = item
      poModalMode.value = 'view'
      showPOModal.value = true
    }

    const handlePOCreated = (poData) => {
      // Update the backlog item with the new PO ID
      const item = allBacklogItems.value.find(b => b.id === poData.backlog_item_id)
      if (item) {
        item.has_purchase_order = true
        item.purchase_order = poData
      }
      showPOModal.value = false
    }

    // Watch for filter changes and reload data
    // Summary, orders + backlog depend on all filters; inventory only on warehouse/category
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], loadSummary)
    watch([selectedLocation, selectedCategory], loadInventory)

    onMounted(() => {
      loadSummary()
      loadInventory()
    })

    return {
      t,
      loading,
      error,
      summary,
      kpis,
      statusData,
      categoryData,
      maxCategoryValue,
      topProducts,
      backlogItems,
      getCircleSegment,
      getStockBadge,
      translateCategory,
      translateStockLevel,
      translatePriority,
      formatDate,
      formatCategoryValue,
      showProductModal,
      selectedProduct,
      showProductDetail,
      showBacklogModal,
      selectedBacklogItem,
      showBacklogDetail,
      selectedPeriod,
      selectedCurrency: currentCurrency,
      formatCurrency,
      Math,
      translateProductName,
      translateWarehouse,
      showPOModal,
      selectedBacklogForPO,
      selectedPOUnitCost,
      poModalMode,
      openPOModal,
      viewPO,
      handlePOCreated
    }
  }
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-meta {
  font-size: 0.813rem;
  color: var(--text-muted);
}

.kpi-section {
  margin-bottom: 1.5rem;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 1rem;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.kpi-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1rem;
}

.kpi-header {
  margin-bottom: 0.75rem;
}

.kpi-label {
  font-size: 0.813rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.kpi-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 0.5rem;
  letter-spacing: -0.025em;
}

.kpi-goal {
  font-size: 0.813rem;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}

.kpi-progress-bar {
  width: 100%;
  height: 6px;
  background: var(--surface-2);
  border-radius: 3px;
  overflow: hidden;
}

.kpi-progress {
  height: 100%;
  background: #3b82f6;
  border-radius: 3px;
  transition: width 0.6s ease;
}

.kpi-progress.success {
  background: #10b981;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.chart-card.full-width {
  grid-column: 1 / -1;
}

.chart-content {
  padding: 1rem;
}

.donut-chart {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3rem;
}

.donut-svg {
  width: 200px;
  height: 200px;
}

.donut-legend {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  font-size: 0.875rem;
  color: var(--text-3);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

/* Order Health Dashboard Styles */
.order-health-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  align-items: center;
  padding: 1rem;
  min-height: 240px;
}

.order-health-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 0 1rem;
}

.donut-svg-compact {
  width: 200px;
  height: 200px;
}

.donut-center-label {
  font-size: 12px;
  fill: var(--text-muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.donut-center-value {
  font-size: 36px;
  fill: var(--text);
  font-weight: 700;
}

.donut-legend-compact {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.625rem 1.25rem;
}

.legend-item-compact {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-3);
  font-weight: 500;
}

.order-health-metrics {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  justify-content: center;
  align-items: center;
}

.health-metric {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  text-align: center;
  width: 100%;
}

.health-metric-label {
  font-size: 0.688rem;
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.health-metric-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.025em;
}

.metric-good {
  color: #10b981;
}

.metric-warning {
  color: #f59e0b;
}

.metric-bad {
  color: #ef4444;
}

.horizontal-bar-chart {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 0 1rem;
}

.h-bar-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.h-bar-label {
  width: 120px;
  min-width: 120px;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-3);
  flex-shrink: 0;
}

.h-bar-container {
  flex: 1;
  height: 32px;
  background: var(--bg);
  border-radius: 6px;
  overflow: hidden;
}

.h-bar {
  height: 100%;
  min-width: max-content; /* never narrower than its label */
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 0.75rem;
  transition: width 0.6s ease;
}

.h-bar-value {
  font-size: 0.813rem;
  font-weight: 700;
  color: white;
}

.line-chart {
  display: flex;
  gap: 1.5rem;
  height: 280px;
}

.line-y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding-right: 1rem;
  font-size: 0.75rem;
  color: var(--text-faint);
  border-right: 1px solid var(--border);
}

.line-chart-area {
  flex: 1;
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  gap: 0.5rem;
}

.line-bar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 80px;
  gap: 0.5rem;
}

.line-bar-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
}

.line-bar {
  width: 100%;
  max-width: 60px;
  min-height: 8px;
  background: #3b82f6;
  border-radius: 6px 6px 0 0;
  transition: all 0.3s ease;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.line-bar.empty-bar {
  background: var(--border);
  box-shadow: none;
  min-height: 4px;
}

.line-bar:hover {
  background: #2563eb;
  transform: scaleY(1.05);
}

.line-bar.empty-bar:hover {
  background: var(--border-strong);
  transform: none;
}

.line-bar-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  white-space: nowrap;
}

.no-data {
  padding: 2rem;
  text-align: center;
  color: var(--text-faint);
  font-size: 0.875rem;
}

.no-backlog {
  padding: 3rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.success-icon {
  width: 48px;
  height: 48px;
  color: #10b981;
}

.no-backlog-text {
  font-size: 1.125rem;
  color: #10b981;
  font-weight: 600;
  margin: 0;
}

.clickable-row {
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.clickable-row:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: -2px;
}

.clickable-row:hover {
  background: var(--accent-soft) !important;
}

/* Tasks Card Styles */
.tasks-card {
  margin-bottom: 2rem;
}

.tasks-content {
  padding: 1.5rem;
}

.task-input-container {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.task-input {
  flex: 1;
  padding: 0.75rem;
  border: 2px solid var(--border);
  border-radius: 8px;
  font-size: 0.95rem;
  transition: border-color 0.2s ease;
}

.task-input:focus {
  outline: none;
  border-color: #667eea;
}

.task-add-btn {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.task-add-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

.task-add-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.no-tasks {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
  font-style: italic;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--bg);
  border-radius: 8px;
  border: 2px solid transparent;
  transition: all 0.2s ease;
}

.task-item:hover {
  border-color: var(--border);
  background: var(--surface);
}

.task-item.completed {
  opacity: 0.6;
}

.task-item.completed .task-text {
  text-decoration: line-through;
  color: var(--text-faint);
}

.task-checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: #667eea;
}

.task-text {
  flex: 1;
  cursor: pointer;
  user-select: none;
  color: var(--text);
  font-size: 0.95rem;
}

.task-delete-btn {
  width: 28px;
  height: 28px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.task-delete-btn:hover {
  background: #dc2626;
  transform: scale(1.1);
}

.po-button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.po-button.create {
  background: #3b82f6;
  color: white;
}

.po-button.create:hover {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.po-button.view {
  background: var(--text-muted);
  color: white;
}

.po-button.view:hover {
  background: var(--text-3);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(100, 116, 139, 0.3);
}

@media (max-width: 768px) {
  .charts-grid,
  .order-health-container {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
