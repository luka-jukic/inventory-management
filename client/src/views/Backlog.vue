<template>
  <div class="backlog">
    <div class="page-header">
      <h2>{{ t('backlog.title') }}</h2>
      <p>{{ t('backlog.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('backlog.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card danger">
          <div class="stat-label">{{ t('backlog.highPriority') }}</div>
          <div class="stat-value">{{ getBacklogByPriority('high').length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('backlog.mediumPriority') }}</div>
          <div class="stat-value">{{ getBacklogByPriority('medium').length }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('backlog.lowPriority') }}</div>
          <div class="stat-value">{{ getBacklogByPriority('low').length }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('backlog.totalItems') }}</div>
          <div class="stat-value">{{ backlogItems.length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('backlog.itemsTitle') }}</h3>
        </div>
        <div v-if="backlogItems.length === 0" style="padding: 3rem; text-align: center;">
          <p style="font-size: 1.125rem; color: #10b981; font-weight: 600;">
            ✓ {{ t('backlog.empty') }}
          </p>
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('backlog.table.orderId') }}</th>
                <th>{{ t('backlog.table.sku') }}</th>
                <th>{{ t('backlog.table.itemName') }}</th>
                <th>{{ t('backlog.table.quantityNeeded') }}</th>
                <th>{{ t('backlog.table.quantityAvailable') }}</th>
                <th>{{ t('backlog.table.shortage') }}</th>
                <th>{{ t('backlog.table.daysDelayed') }}</th>
                <th>{{ t('backlog.table.priority') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in backlogItems" :key="item.id">
                <td><strong>{{ item.order_number }}</strong></td>
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ translateProductName(item.item_name) }}</td>
                <td>{{ item.quantity_needed }}</td>
                <td>{{ item.quantity_available }}</td>
                <td>
                  <span class="badge danger">
                    {{ t('backlog.unitsShort', { count: item.quantity_needed - item.quantity_available }) }}
                  </span>
                </td>
                <td>
                  <span :style="{ color: item.days_delayed > 7 ? '#ef4444' : '#f59e0b' }">
                    {{ t('backlog.daysCount', { count: item.days_delayed }) }}
                  </span>
                </td>
                <td>
                  <span :class="['badge', item.priority]">
                    {{ t('priority.' + item.priority) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { api, isCanceled } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Backlog',
  setup() {
    const { t, translateProductName } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const backlogItems = ref([])

    // Use shared filters; the server filters backlog by its linked order
    const { selectedPeriod, selectedLocation, selectedCategory, selectedStatus, getCurrentFilters } = useFilters()

    let ctrl = null
    const loadBacklog = async () => {
      ctrl?.abort()
      const current = (ctrl = new AbortController())
      try {
        loading.value = true
        error.value = null
        backlogItems.value = await api.getBacklog(getCurrentFilters(), { signal: current.signal })
      } catch (err) {
        if (isCanceled(err)) return
        error.value = t('backlog.loadFailed') + err.message
      } finally {
        if (ctrl === current) loading.value = false
      }
    }

    const getBacklogByPriority = (priority) => {
      return backlogItems.value.filter(item => item.priority === priority)
    }

    // Watch for filter changes and reload data
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], loadBacklog)

    onMounted(loadBacklog)
    onUnmounted(() => ctrl?.abort())

    return {
      t,
      translateProductName,
      loading,
      error,
      backlogItems,
      getBacklogByPriority
    }
  }
}
</script>
