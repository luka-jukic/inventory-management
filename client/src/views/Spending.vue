<template>
  <div class="spending">
    <div class="page-header">
      <h2>{{ t('finance.title') }}</h2>
      <p>{{ t('finance.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Revenue & Financial KPIs -->
      <div class="stats-grid-finance">
        <div class="stat-card revenue-card">
          <div class="stat-label">{{ t('finance.totalRevenue') }}</div>
          <div class="stat-value">{{ formatCurrency(revenueMetrics.totalRevenue) }}</div>
          <div class="stat-change positive">
            <span class="change-icon">↑</span>
            {{ t('finance.fromOrders', { count: revenueMetrics.orderCount }) }}
          </div>
        </div>
        <div class="stat-card cost-card">
          <div class="stat-label">{{ t('finance.totalCosts') }}</div>
          <div class="stat-value">{{ formatCurrency(totalCosts) }}</div>
          <div class="stat-meta">{{ t('finance.costBreakdown') }}</div>
        </div>
        <div class="stat-card profit-card">
          <div class="stat-label">{{ t('finance.netProfit') }}</div>
          <div class="stat-value">{{ formatCurrency(netProfit) }}</div>
          <div class="stat-meta">{{ profitMargin }}% {{ t('finance.margin') }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('finance.avgOrderValue') }}</div>
          <div class="stat-value">{{ formatCurrency(revenueMetrics.avgOrderValue) }}</div>
          <div class="stat-meta">{{ t('finance.perOrderRevenue') }}</div>
        </div>
      </div>

      <!-- Monthly Revenue vs Cost Chart -->
      <div class="card chart-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('finance.revenueVsCosts.title') }}</h3>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot revenue-color"></span>{{ t('finance.revenueVsCosts.revenue') }}</span>
            <span class="legend-item"><span class="legend-dot cost-color"></span>{{ t('finance.revenueVsCosts.costs') }}</span>
          </div>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div class="y-axis">
              <span>{{ axis(maxRevenueValue) }}</span>
              <span>{{ axis(Math.round(maxRevenueValue * 0.75)) }}</span>
              <span>{{ axis(Math.round(maxRevenueValue * 0.5)) }}</span>
              <span>{{ axis(Math.round(maxRevenueValue * 0.25)) }}</span>
              <span>{{ money(0) }}</span>
            </div>
            <div class="chart-area">
              <div v-for="month in monthlyRevenue" :key="month.month" class="bar-group-revenue">
                <div class="revenue-bars">
                  <div class="revenue-bar" :style="{ height: getRevenueBarHeight(month.revenue) + '%' }" :title="`${t('finance.revenueVsCosts.revenue')}: ${money(month.revenue)}`"></div>
                  <div class="cost-bar" :style="{ height: getRevenueBarHeight(month.costs) + '%' }" :title="`${t('finance.revenueVsCosts.costs')}: ${money(month.costs)}`"></div>
                </div>
                <span class="bar-label">{{ translateMonth(month.month) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Monthly Cost Flow Chart -->
      <div class="card chart-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('finance.monthlyCostFlow.title') }}</h3>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot procurement"></span>{{ t('finance.monthlyCostFlow.procurement') }}</span>
            <span class="legend-item"><span class="legend-dot operational"></span>{{ t('finance.monthlyCostFlow.operational') }}</span>
            <span class="legend-item"><span class="legend-dot labor"></span>{{ t('finance.monthlyCostFlow.labor') }}</span>
            <span class="legend-item"><span class="legend-dot overhead"></span>{{ t('finance.monthlyCostFlow.overhead') }}</span>
          </div>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div class="y-axis">
              <span>{{ axis(25) }}</span>
              <span>{{ axis(20) }}</span>
              <span>{{ axis(15) }}</span>
              <span>{{ axis(10) }}</span>
              <span>{{ axis(5) }}</span>
              <span>{{ money(0) }}</span>
            </div>
            <div class="chart-area">
              <div v-for="month in monthlySpending" :key="month.month" class="bar-group">
                <div
                  class="stacked-bar"
                  role="button"
                  tabindex="0"
                  :aria-label="`${t('finance.monthlyCostFlow.title')}: ${translateMonth(month.month)}`"
                  @click="showCostDetail(month)"
                  @keydown.enter="showCostDetail(month)"
                  @keydown.space.prevent="showCostDetail(month)"
                >
                  <div class="bar-segment procurement" :style="{ height: getBarHeight(month.procurement) + '%' }" :title="`${t('finance.monthlyCostFlow.procurement')}: ${money(month.procurement)}`"></div>
                  <div class="bar-segment operational" :style="{ height: getBarHeight(month.operational) + '%' }" :title="`${t('finance.monthlyCostFlow.operational')}: ${money(month.operational)}`"></div>
                  <div class="bar-segment labor" :style="{ height: getBarHeight(month.labor) + '%' }" :title="`${t('finance.monthlyCostFlow.labor')}: ${money(month.labor)}`"></div>
                  <div class="bar-segment overhead" :style="{ height: getBarHeight(month.overhead) + '%' }" :title="`${t('finance.monthlyCostFlow.overhead')}: ${money(month.overhead)}`"></div>
                </div>
                <span class="bar-label">{{ translateMonth(month.month) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="two-column-grid">
        <!-- Category Spending Breakdown -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('finance.categorySpending.title') }}</h3>
          </div>
          <div class="category-list">
            <div v-for="category in categorySpending" :key="category.category" class="category-item">
              <div class="category-info">
                <div class="category-name">{{ translateCategory(category.category) }}</div>
                <div class="category-amount">{{ money(category.amount) }}</div>
              </div>
              <div class="category-bar-container">
                <div class="category-bar" :style="{ width: category.percentage + '%' }"></div>
              </div>
              <div class="category-meta">
                <span class="percentage">{{ category.percentage }}% {{ t('finance.categorySpending.ofTotal') }}</span>
                <span class="change" :class="{ positive: category.change > 0, negative: category.change < 0 }">
                  {{ category.change > 0 ? '+' : '' }}{{ category.change }}%
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Transactions -->
        <div class="card transactions-card">
          <div class="card-header">
            <h3 class="card-title">{{ t('finance.transactions.title') }}</h3>
          </div>
          <div class="transactions-table-container">
            <table class="transactions-table">
              <thead>
                <tr>
                  <th>{{ t('finance.transactions.id') }}</th>
                  <th>{{ t('finance.transactions.description') }}</th>
                  <th>{{ t('finance.transactions.vendor') }}</th>
                  <th>{{ t('finance.transactions.date') }}</th>
                  <th class="text-right">{{ t('finance.transactions.amount') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="transaction in recentTransactions"
                  :key="transaction.id"
                  class="clickable-row"
                  tabindex="0"
                  @click="handleTransactionClick(transaction, $event)"
                  @keydown.enter="handleTransactionClick(transaction, $event)"
                  @keydown.space.prevent="handleTransactionClick(transaction, $event)"
                >
                  <td class="transaction-id">{{ transaction.id.toString().padStart(3, '0') }}</td>
                  <td class="transaction-description">{{ transaction.description }}</td>
                  <td class="transaction-vendor">{{ transaction.vendor }}</td>
                  <td class="transaction-date">{{ formatDateShort(transaction.date) }}</td>
                  <td class="transaction-amount text-right">{{ money(transaction.amount) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedTransaction" class="tx-backdrop" @click.self="closeTransaction">
      <div
        ref="txDialog"
        class="tx-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="tx-dialog-title"
        tabindex="-1"
        @keydown.esc="closeTransaction"
      >
        <h3 id="tx-dialog-title">{{ t('finance.transactions.details') }}</h3>
        <dl class="tx-list">
          <dt>{{ t('finance.transactions.id') }}</dt>
          <dd>{{ selectedTransaction.id.toString().padStart(3, '0') }}</dd>
          <dt>{{ t('finance.transactions.description') }}</dt>
          <dd>{{ selectedTransaction.description }}</dd>
          <dt>{{ t('finance.transactions.vendor') }}</dt>
          <dd>{{ selectedTransaction.vendor }}</dd>
          <dt>{{ t('finance.transactions.date') }}</dt>
          <dd>{{ formatDateShort(selectedTransaction.date) }}</dd>
          <dt>{{ t('finance.transactions.amount') }}</dt>
          <dd>{{ money(selectedTransaction.amount) }}</dd>
        </dl>
        <button type="button" class="tx-close" @click="closeTransaction">{{ t('common.close') }}</button>
      </div>
    </div>

    <CostDetailModal
      :is-open="showCostModal"
      :cost-data="selectedCostData"
      @close="showCostModal = false"
    />
  </div>
</template>

<script>
import { ref, nextTick, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { api, isCanceled } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency as formatCurrencyUtil } from '../utils/currency'
import CostDetailModal from '../components/CostDetailModal.vue'

export default {
  name: 'Spending',
  components: {
    CostDetailModal
  },
  setup() {
    const { t, currentCurrency } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const allMonthlySpending = ref([])
    const allCategorySpending = ref([])
    const recentTransactions = ref([])
    const summaryData = ref({})
    const dashSummary = ref({})
    const trends = ref([])

    // Modal state
    const showCostModal = ref(false)
    const selectedCostData = ref(null)

    // Use shared filters
    const { selectedPeriod, getCurrentFilters } = useFilters()

    // Monthly spending chart always shows all months (not filtered)
    const monthlySpending = computed(() => {
      return allMonthlySpending.value
    })

    const categorySpending = computed(() => allCategorySpending.value)

    // Revenue metrics come from the server (month-filtered, same scope as the costs)
    const revenueMetrics = computed(() => ({
      totalRevenue: dashSummary.value.total_orders_value || 0,
      orderCount: dashSummary.value.total_orders || 0,
      avgOrderValue: dashSummary.value.avg_order_value || 0
    }))

    // Total costs from summary
    const totalCosts = computed(() => {
      return summaryData.value.total_procurement_cost +
             summaryData.value.total_operational_cost +
             summaryData.value.total_labor_cost +
             summaryData.value.total_overhead
    })

    // Net profit
    const netProfit = computed(() => {
      return revenueMetrics.value.totalRevenue - totalCosts.value
    })

    // Profit margin percentage
    const profitMargin = computed(() => {
      if (revenueMetrics.value.totalRevenue === 0) return 0
      return ((netProfit.value / revenueMetrics.value.totalRevenue) * 100).toFixed(1)
    })

    // Monthly revenue data for chart
    const monthlyRevenue = computed(() => {
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

      // Initialize all months
      const revenueByMonth = monthNames.map(month => ({
        month,
        revenue: 0,
        costs: 0
      }))

      // Revenue per month from server-side trends ('YYYY-MM')
      trends.value.forEach(row => {
        const monthIndex = parseInt(row.month.slice(5, 7), 10) - 1
        if (monthIndex >= 0 && monthIndex < 12) {
          revenueByMonth[monthIndex].revenue = row.revenue || 0
        }
      })

      // Add costs from spending data
      allMonthlySpending.value.forEach(spending => {
        const monthIndex = monthNames.indexOf(spending.month)
        if (monthIndex >= 0) {
          revenueByMonth[monthIndex].costs = spending.procurement + spending.operational + spending.labor + spending.overhead
        }
      })

      return revenueByMonth
    })

    // Max value for chart scaling
    const maxRevenueValue = computed(() => {
      const maxRevenue = Math.max(...monthlyRevenue.value.map(m => m.revenue))
      const maxCost = Math.max(...monthlyRevenue.value.map(m => m.costs))
      const max = Math.max(maxRevenue, maxCost)
      return Math.ceil(max / 1000) // Return in K
    })

    let ctrl = null
    const loadData = async () => {
      ctrl?.abort()
      const mine = (ctrl = new AbortController())
      const opts = { signal: mine.signal }
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()
        // Costs and revenue are scoped by period only (costs have no warehouse/category)
        // Month only, on purpose: costs have no warehouse/category, so filtering revenue by them would skew profit and margin
        const periodFilters = { month: filters.month }
        const [summaryRes, monthlyRes, categoryRes, transactionsRes, dashRes, trendsRes] = await Promise.all([
          api.getSpendingSummary(periodFilters, opts),
          api.getMonthlySpending(opts),
          api.getCategorySpending(opts),
          api.getTransactions(periodFilters, opts),
          api.getDashboardSummary(periodFilters, opts),
          api.getMonthlyTrends({}, opts)
        ])

        summaryData.value = summaryRes
        allMonthlySpending.value = monthlyRes
        allCategorySpending.value = categoryRes
        recentTransactions.value = transactionsRes
        dashSummary.value = dashRes
        trends.value = trendsRes
      } catch (err) {
        if (isCanceled(err)) return
        error.value = t('common.loadFailed', { message: err.message })
      } finally {
        if (ctrl === mine) loading.value = false
      }
    }

    onBeforeUnmount(() => ctrl?.abort())

    const formatCurrency = (value) => {
      return formatCurrencyUtil(value, currentCurrency.value)
    }

    const money = (value) => formatCurrency(value)

    // Axis label for a value in thousands of USD, e.g. $25K / ¥3,750K
    const axis = (thousands) => formatCurrency(thousands) + 'K'

    const getBarHeight = (value) => {
      const maxValue = 25000
      return (value / maxValue) * 100
    }

    const getRevenueBarHeight = (value) => {
      const maxValue = maxRevenueValue.value * 1000
      return (value / maxValue) * 100
    }

    // Date-only string (YYYY-MM-DD): read the parts directly, no timezone shift
    const formatDateShort = (dateString) => {
      const [year, month, day] = dateString.split('-')
      return `${month}/${day}/${year.slice(-2)}`
    }

    const translateMonth = (month) => {
      const monthMap = {
        'Jan': t('months.jan'),
        'Feb': t('months.feb'),
        'Mar': t('months.mar'),
        'Apr': t('months.apr'),
        'May': t('months.may'),
        'Jun': t('months.jun'),
        'Jul': t('months.jul'),
        'Aug': t('months.aug'),
        'Sep': t('months.sep'),
        'Oct': t('months.oct'),
        'Nov': t('months.nov'),
        'Dec': t('months.dec')
      }
      return monthMap[month] || month
    }

    const translateCategory = (category) => {
      // First try spending categories
      const spendingCategoryMap = {
        'Raw Materials': t('spendingCategories.rawMaterials'),
        'Components': t('spendingCategories.components'),
        'Equipment': t('spendingCategories.equipment'),
        'Consumables': t('spendingCategories.consumables')
      }

      // Then try product categories
      const productCategoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        'Sensors': t('categories.sensors'),
        'Actuators': t('categories.actuators'),
        'Controllers': t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies')
      }

      return spendingCategoryMap[category] || productCategoryMap[category] || category
    }

    // Transaction detail dialog: Escape closes, focus returns to the opener
    const selectedTransaction = ref(null)
    const txDialog = ref(null)
    let txOpener = null

    const handleTransactionClick = async (transaction, event) => {
      txOpener = event?.currentTarget || null
      selectedTransaction.value = transaction
      await nextTick()
      txDialog.value?.focus()
    }

    const closeTransaction = () => {
      selectedTransaction.value = null
      txOpener?.focus()
      txOpener = null
    }

    const showCostDetail = (monthData) => {
      selectedCostData.value = monthData
      showCostModal.value = true
    }

    watch(selectedPeriod, loadData)
    onMounted(loadData)

    return {
      t,
      loading,
      error,
      monthlySpending,
      categorySpending,
      recentTransactions,
      revenueMetrics,
      totalCosts,
      netProfit,
      profitMargin,
      monthlyRevenue,
      maxRevenueValue,
      formatCurrency,
      money,
      axis,
      getBarHeight,
      getRevenueBarHeight,
      formatDateShort,
      translateMonth,
      translateCategory,
      handleTransactionClick,
      selectedTransaction,
      txDialog,
      closeTransaction,
      showCostModal,
      selectedCostData,
      showCostDetail,
      Math
    }
  }
}
</script>

<style scoped>
.stat-change {
  margin-top: 0.75rem;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.stat-change.positive {
  color: #059669;
}

.stat-change.negative {
  color: #dc2626;
}

.change-icon {
  font-weight: 700;
  font-size: 1rem;
}

.chart-card {
  margin-bottom: 1.75rem;
}

.chart-legend {
  display: flex;
  gap: 1.5rem;
  font-size: 0.875rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-muted);
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.legend-dot.procurement { background: #3b82f6; }
.legend-dot.operational { background: #8b5cf6; }
.legend-dot.labor { background: #10b981; }
.legend-dot.overhead { background: #f59e0b; }
.legend-dot.revenue-color { background: var(--text); }
.legend-dot.cost-color { background: #ef4444; }

.stats-grid-finance {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.revenue-card {
  border-left: 4px solid var(--text);
}

.cost-card {
  border-left: 4px solid #ef4444;
}

.profit-card {
  border-left: 4px solid #3b82f6;
}

.stat-meta {
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: var(--text-muted);
}

.bar-group-revenue {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  height: 100%;
}

.revenue-bars {
  width: 100%;
  max-width: 80px;
  display: flex;
  gap: 6px;
  justify-content: center;
  align-items: flex-end;
  height: 100%;
  padding-bottom: 2rem;
}

.revenue-bar, .cost-bar {
  width: 50%;
  max-width: 30px;
  border-radius: 6px 6px 0 0;
  transition: all 0.3s ease;
  cursor: pointer;
  min-height: 4px;
}

.revenue-bar {
  background: var(--text);
}

.cost-bar {
  background: #ef4444;
}

.revenue-bar:hover, .cost-bar:hover {
  opacity: 0.8;
  transform: scaleY(1.05);
}

.chart-container {
  padding: 1.5rem 0;
}

.bar-chart {
  display: flex;
  gap: 1.5rem;
  height: 350px;
}

.y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding-right: 1rem;
  font-size: 0.75rem;
  color: var(--text-faint);
  border-right: 1px solid var(--border);
}

.chart-area {
  flex: 1;
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  gap: 0.5rem;
}

.bar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  height: 100%;
}

.stacked-bar {
  width: 100%;
  max-width: 60px;
  display: flex;
  flex-direction: column-reverse;
  align-items: stretch;
  height: 100%;
  padding-bottom: 2rem;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.stacked-bar:hover {
  opacity: 0.85;
}

.bar-segment {
  width: 100%;
  transition: all 0.3s ease;
  cursor: pointer;
  display: block;
}

.bar-segment:first-child {
  border-radius: 0 0 6px 6px;
}

.bar-segment:last-child {
  border-radius: 6px 6px 0 0;
}

.bar-segment.procurement { background: #3b82f6; }
.bar-segment.operational { background: #8b5cf6; }
.bar-segment.labor { background: #10b981; }
.bar-segment.overhead { background: #f59e0b; }

.bar-segment:hover {
  opacity: 0.8;
}

.bar-label {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
}

.two-column-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 450px), 1fr));
  gap: 1.75rem;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.category-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.category-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.category-name {
  font-weight: 600;
  color: var(--text);
}

.category-amount {
  font-weight: 700;
  color: #2563eb;
  font-size: 1.125rem;
}

.category-bar-container {
  width: 100%;
  height: 8px;
  background: var(--surface-2);
  border-radius: 4px;
  overflow: hidden;
}

.category-bar {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 4px;
  transition: width 0.6s ease;
}

.category-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.813rem;
}

.percentage {
  color: var(--text-muted);
}

.change {
  font-weight: 600;
}

.change.positive {
  color: #059669;
}

.change.negative {
  color: #dc2626;
}

.transactions-card {
  display: flex;
  flex-direction: column;
}

.transactions-table-container {
  overflow-y: auto;
  max-height: 400px;
}

.transactions-table {
  width: 100%;
  border-collapse: collapse;
}

.transactions-table thead {
  position: sticky;
  top: 0;
  background: var(--bg);
  z-index: 1;
}

.transactions-table th {
  text-align: left;
  padding: 0.625rem 0.75rem;
  font-weight: 600;
  color: var(--text-3);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border);
}

.transactions-table th.text-right {
  text-align: right;
}

.transactions-table td {
  padding: 0.75rem 0.75rem;
  border-bottom: 1px solid var(--border-soft);
  font-size: 0.875rem;
}

.transactions-table tbody tr {
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.transactions-table tbody tr:hover {
  background: var(--bg);
}

.transactions-table tbody tr.clickable-row:focus-visible,
.stacked-bar:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: -2px;
}

.tx-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 1000;
}

.tx-dialog {
  background: var(--surface);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.5rem;
  width: min(420px, 100%);
}

.tx-dialog:focus {
  outline: none;
}

.tx-list {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.5rem 1rem;
  margin: 1rem 0;
}

.tx-list dt {
  color: var(--text-muted);
}

.tx-list dd {
  margin: 0;
  font-weight: 500;
}

.tx-close {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-strong);
  border-radius: 8px;
  background: var(--bg);
  color: var(--text);
  cursor: pointer;
}

.transactions-table tbody tr.clickable-row:hover {
  background: var(--accent-soft);
}

.transaction-id {
  color: var(--text-muted);
  font-weight: 500;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.813rem;
}

.transaction-description {
  color: var(--text);
  font-weight: 500;
}

.transaction-vendor {
  color: var(--text-muted);
}

.transaction-date {
  color: var(--text-muted);
  font-size: 0.813rem;
}

.transaction-amount {
  font-weight: 700;
  color: var(--text);
}

.text-right {
  text-align: right;
}
</style>
