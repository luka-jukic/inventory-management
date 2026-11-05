<template>
  <BaseModal
    :is-open="!!(isOpen && inventoryItem)"
    :title="t('detailModal.inventoryTitle')"
    max-width="700px"
    @close="close"
  >

          <div class="modal-body">
            <div class="item-header">
              <div class="item-icon" :class="getStockIconClass()">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                  <rect x="8" y="12" width="32" height="28" rx="2" stroke="currentColor" stroke-width="2.5"/>
                  <path d="M16 8V16M32 8V16M8 20H40" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                  <path d="M16 28H32M16 34H24" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="item-title-section">
                <h4 class="item-name">{{ translateProductName(inventoryItem.name) }}</h4>
                <div class="item-sku">SKU: {{ inventoryItem.sku }}</div>
              </div>
              <span class="stock-badge" :class="getStockStatusClass()">
                {{ getStockLabel() }}
              </span>
            </div>

            <div class="stock-summary">
              <div class="summary-card primary">
                <div class="summary-label">{{ t('inventory.table.quantityOnHand') }}</div>
                <div class="summary-value">{{ t('detailModal.units', { count: inventoryItem.quantity_on_hand }) }}</div>
              </div>
              <div class="summary-card" :class="getSummaryCardClass()">
                <div class="summary-label">{{ t('detailModal.stockLevel') }}</div>
                <div class="summary-value">{{ stockPercentage }}%</div>
                <div class="summary-subtitle">{{ t('detailModal.vsReorder') }}</div>
              </div>
            </div>

            <div class="info-grid">
              <div class="info-item">
                <div class="info-label">{{ t('inventory.table.category') }}</div>
                <div class="info-value">{{ inventoryItem.category }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('inventory.table.location') }}</div>
                <div class="info-value">{{ inventoryItem.location }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('inventory.table.reorderPoint') }}</div>
                <div class="info-value">{{ t('detailModal.units', { count: inventoryItem.reorder_point }) }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('detailModal.unitsRemaining') }}</div>
                <div class="info-value">
                  <span :style="{ color: inventoryItem.quantity_on_hand <= inventoryItem.reorder_point ? '#ef4444' : '#10b981' }">
                    {{ t('detailModal.units', { count: inventoryItem.quantity_on_hand - inventoryItem.reorder_point }) }}
                  </span>
                </div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('inventory.table.unitCost') }}</div>
                <div class="info-value">{{ currencySymbol }}{{ inventoryItem.unit_cost.toFixed(2) }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('inventory.table.totalValue') }}</div>
                <div class="info-value total-value">
                  {{ currencySymbol }}{{ totalValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}
                </div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('inventory.table.warehouse') }}</div>
                <div class="info-value">{{ translateWarehouse(inventoryItem.location) }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('inventory.table.status') }}</div>
                <div class="info-value">
                  <span :class="['badge', getStockStatusClass()]">
                    {{ getStockLabel() }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">{{ t('common.close') }}</button>
          </div>
  </BaseModal>
</template>

<script setup>
import BaseModal from './BaseModal.vue'
import { computed } from 'vue'
import { useI18n } from '../composables/useI18n'

const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

const currencySymbol = computed(() => {
  return currentCurrency.value === 'JPY' ? '¥' : '$'
})

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  inventoryItem: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const totalValue = computed(() => {
  if (!props.inventoryItem) return 0
  return props.inventoryItem.quantity_on_hand * props.inventoryItem.unit_cost
})

const stockPercentage = computed(() => {
  if (!props.inventoryItem || props.inventoryItem.reorder_point === 0) return 0
  return Math.round((props.inventoryItem.quantity_on_hand / props.inventoryItem.reorder_point) * 100)
})

const close = () => {
  emit('close')
}

const getStockStatus = () => {
  if (!props.inventoryItem) return 'Unknown'
  if (props.inventoryItem.quantity_on_hand <= props.inventoryItem.reorder_point) {
    return 'Low Stock'
  } else if (props.inventoryItem.quantity_on_hand <= props.inventoryItem.reorder_point * 1.5) {
    return 'Adequate'
  } else {
    return 'In Stock'
  }
}

const getStockLabel = () => {
  const status = getStockStatus()
  if (status === 'Low Stock') return t('status.lowStock')
  if (status === 'Adequate') return t('status.adequate')
  if (status === 'In Stock') return t('status.inStock')
  return t('detailModal.unknown')
}

const getStockStatusClass = () => {
  const status = getStockStatus()
  if (status === 'Low Stock') return 'danger'
  if (status === 'Adequate') return 'warning'
  return 'success'
}

const getStockIconClass = () => {
  const status = getStockStatus()
  if (status === 'Low Stock') return 'danger-icon'
  if (status === 'Adequate') return 'warning-icon'
  return 'success-icon'
}

const getSummaryCardClass = () => {
  const status = getStockStatus()
  if (status === 'Low Stock') return 'danger-card'
  if (status === 'Adequate') return 'warning-card'
  return 'success-card'
}
</script>

<style scoped>
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 1.5rem;
}

.item-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.item-icon.success-icon {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.item-icon.warning-icon {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.item-icon.danger-icon {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.item-title-section {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 0.5rem 0;
}

.item-sku {
  font-size: 0.875rem;
  color: var(--text-muted);
  font-family: 'Monaco', 'Courier New', monospace;
}

.stock-badge {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.stock-badge.success {
  background: var(--c-green-bg);
  color: var(--c-green-fg);
}

.stock-badge.warning {
  background: var(--c-orange-bg);
  color: var(--c-orange-fg);
}

.stock-badge.danger {
  background: var(--c-red-bg);
  color: var(--c-red-fg);
}

.stock-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}

.summary-card {
  padding: 1.25rem;
  border-radius: 10px;
  border: 2px solid;
}

.summary-card.primary {
  border-color: #bfdbfe;
  background: var(--accent-soft);
}

.summary-card.success-card {
  border-color: #a7f3d0;
  background: var(--c-green-bg);
}

.summary-card.warning-card {
  border-color: var(--c-orange-bg);
  background: var(--c-amber-tint);
}

.summary-card.danger-card {
  border-color: var(--c-red-bg);
  background: var(--c-red-tint);
}

.summary-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.summary-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--text);
}

.summary-subtitle {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.info-value {
  font-size: 0.938rem;
  color: var(--text);
  font-weight: 500;
}

.info-value.total-value {
  font-size: 1.125rem;
  color: #2563eb;
  font-weight: 700;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-secondary {
  padding: 0.625rem 1.25rem;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary:hover {
  background: var(--border);
  border-color: var(--border-strong);
}

/* Modal transition animations */
</style>
