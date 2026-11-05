<template>
  <BaseModal
    :is-open="!!(isOpen && product)"
    :title="t('detailModal.productTitle')"
    max-width="700px"
    @close="close"
  >

          <div class="modal-body">
            <div class="product-header">
              <div class="product-icon">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                  <rect x="8" y="12" width="32" height="28" rx="2" stroke="currentColor" stroke-width="2.5"/>
                  <path d="M16 8V16M32 8V16M8 20H40" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="product-title-section">
                <h4 class="product-name">{{ product.name }}</h4>
                <div class="product-sku">SKU: {{ product.sku }}</div>
              </div>
              <span class="stock-badge" :class="getStockBadgeClass(product.stockLevel)">
                {{ getStockLabel(product.stockLevel) }}
              </span>
            </div>

            <div class="info-grid">
              <div class="info-item">
                <div class="info-label">{{ t('inventory.table.category') }}</div>
                <div class="info-value">{{ product.category }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('inventory.table.warehouse') }}</div>
                <div class="info-value">{{ product.warehouse }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('detailModal.unitsOrdered') }}</div>
                <div class="info-value">{{ product.unitsOrdered }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('detailModal.totalRevenue') }}</div>
                <div class="info-value">{{ money(product.revenue) }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('detailModal.currentStock') }}</div>
                <div class="info-value">{{ t('detailModal.units', { count: product.quantityOnHand }) }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('inventory.table.reorderPoint') }}</div>
                <div class="info-value">{{ t('detailModal.units', { count: product.reorderPoint }) }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('detailModal.firstOrderDate') }}</div>
                <div class="info-value">{{ formatDate(product.firstOrderDate) }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('detailModal.stockStatus') }}</div>
                <div class="info-value">
                  <span :class="['badge', getStockBadgeClass(product.stockLevel)]">
                    {{ getStockLabel(product.stockLevel) }}
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
import { formatCurrencyWithDecimals } from '../utils/currency'
import { useI18n } from '../composables/useI18n'

const { t, currentLocale, currentCurrency } = useI18n()

const money = (n, d = 0) => formatCurrencyWithDecimals(n, currentCurrency.value, d)

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  product: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const close = () => {
  emit('close')
}

const formatDate = (dateString) => {
  if (!dateString) return t('detailModal.notAvailable')
  const date = new Date(dateString)
  return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const getStockLabel = (stockLevel) => {
  if (stockLevel === 'in_stock') return t('status.inStock')
  if (stockLevel === 'adequate') return t('status.adequate')
  if (stockLevel === 'low_stock') return t('status.lowStock')
  return stockLevel
}

const getStockBadgeClass = (stockLevel) => {
  if (stockLevel === 'in_stock') return 'success'
  if (stockLevel === 'adequate' || stockLevel === 'low_stock') return 'warning'
  return 'info'
}
</script>

<style scoped>
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.product-header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 2rem;
}

.product-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.product-title-section {
  flex: 1;
  min-width: 0;
}

.product-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 0.5rem 0;
}

.product-sku {
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
