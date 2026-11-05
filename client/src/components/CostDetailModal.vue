<template>
  <BaseModal
    :is-open="!!(isOpen && costData)"
    :title="t('detailModal.costTitle', { month: costData?.month })"
    max-width="600px"
    @close="close"
  >

          <div class="modal-body">
            <div class="cost-summary">
              <div class="summary-card total">
                <div class="summary-label">{{ t('detailModal.totalCosts') }}</div>
                <div class="summary-value">{{ money(totalCosts) }}</div>
              </div>
            </div>

            <div class="cost-breakdown">
              <div class="cost-item procurement">
                <div class="cost-header">
                  <div class="cost-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <rect x="4" y="6" width="16" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
                      <path d="M8 6V4M16 6V4M4 10H20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <div class="cost-info">
                    <div class="cost-name">{{ t('detailModal.procurement') }}</div>
                    <div class="cost-amount">{{ money(costData.procurement) }}</div>
                  </div>
                </div>
                <div class="cost-percentage">{{ t('detailModal.ofTotal', { pct: getProcurementPercentage() }) }}</div>
              </div>

              <div class="cost-item operational">
                <div class="cost-header">
                  <div class="cost-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="12" r="8" stroke="currentColor" stroke-width="2"/>
                      <path d="M12 8V12L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <div class="cost-info">
                    <div class="cost-name">{{ t('detailModal.operational') }}</div>
                    <div class="cost-amount">{{ money(costData.operational) }}</div>
                  </div>
                </div>
                <div class="cost-percentage">{{ t('detailModal.ofTotal', { pct: getOperationalPercentage() }) }}</div>
              </div>

              <div class="cost-item labor">
                <div class="cost-header">
                  <div class="cost-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="2"/>
                      <path d="M6 20C6 16.6863 8.68629 14 12 14C15.3137 14 18 16.6863 18 20" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <div class="cost-info">
                    <div class="cost-name">{{ t('detailModal.labor') }}</div>
                    <div class="cost-amount">{{ money(costData.labor) }}</div>
                  </div>
                </div>
                <div class="cost-percentage">{{ t('detailModal.ofTotal', { pct: getLaborPercentage() }) }}</div>
              </div>

              <div class="cost-item overhead">
                <div class="cost-header">
                  <div class="cost-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <path d="M3 12L5 10M5 10L12 3L19 10M5 10V20C5 20.5523 5.44772 21 6 21H9M19 10L21 12M19 10V20C19 20.5523 18.5523 21 18 21H15M9 21C9 21 9 18 9 16C9 14 10 14 12 14C14 14 15 14 15 16C15 18 15 21 15 21M9 21H15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <div class="cost-info">
                    <div class="cost-name">{{ t('detailModal.overhead') }}</div>
                    <div class="cost-amount">{{ money(costData.overhead) }}</div>
                  </div>
                </div>
                <div class="cost-percentage">{{ t('detailModal.ofTotal', { pct: getOverheadPercentage() }) }}</div>
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
import { formatCurrencyWithDecimals } from '../utils/currency'
import { useI18n } from '../composables/useI18n'

const { t, currentCurrency } = useI18n()

const money = (n, d = 0) => formatCurrencyWithDecimals(n, currentCurrency.value, d)

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  costData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const totalCosts = computed(() => {
  if (!props.costData) return 0
  return props.costData.procurement + props.costData.operational +
         props.costData.labor + props.costData.overhead
})

const getProcurementPercentage = () => {
  if (!props.costData || totalCosts.value === 0) return 0
  return ((props.costData.procurement / totalCosts.value) * 100).toFixed(1)
}

const getOperationalPercentage = () => {
  if (!props.costData || totalCosts.value === 0) return 0
  return ((props.costData.operational / totalCosts.value) * 100).toFixed(1)
}

const getLaborPercentage = () => {
  if (!props.costData || totalCosts.value === 0) return 0
  return ((props.costData.labor / totalCosts.value) * 100).toFixed(1)
}

const getOverheadPercentage = () => {
  if (!props.costData || totalCosts.value === 0) return 0
  return ((props.costData.overhead / totalCosts.value) * 100).toFixed(1)
}

const close = () => {
  emit('close')
}
</script>

<style scoped>
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.cost-summary {
  margin-bottom: 2rem;
}

.summary-card {
  padding: 1.5rem;
  border-radius: 10px;
  text-align: center;
}

.summary-card.total {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.summary-label {
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  opacity: 0.9;
  margin-bottom: 0.5rem;
}

.summary-value {
  font-size: 2.25rem;
  font-weight: 700;
}

.cost-breakdown {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.cost-item {
  padding: 1.25rem;
  border-radius: 10px;
  border: 2px solid;
}

.cost-item.procurement {
  border-color: #93c5fd;
  background: var(--accent-soft);
}

.cost-item.operational {
  border-color: #c4b5fd;
  background: var(--c-violet-tint);
}

.cost-item.labor {
  border-color: #86efac;
  background: var(--c-green-tint);
}

.cost-item.overhead {
  border-color: #fcd34d;
  background: var(--c-amber-tint);
}

.cost-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.cost-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.cost-item.procurement .cost-icon {
  background: #3b82f6;
  color: white;
}

.cost-item.operational .cost-icon {
  background: #8b5cf6;
  color: white;
}

.cost-item.labor .cost-icon {
  background: #10b981;
  color: white;
}

.cost-item.overhead .cost-icon {
  background: #f59e0b;
  color: white;
}

.cost-info {
  flex: 1;
}

.cost-name {
  font-weight: 600;
  color: var(--text);
  font-size: 1rem;
  margin-bottom: 0.25rem;
}

.cost-amount {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text);
}

.cost-percentage {
  font-size: 0.875rem;
  color: var(--text-muted);
  font-weight: 500;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
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
