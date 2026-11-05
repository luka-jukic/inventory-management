<template>
  <BaseModal
    :is-open="!!(isOpen && backlogItem)"
    :title="t('detailModal.backlogTitle')"
    max-width="700px"
    @close="close"
  >

          <div class="modal-body">
            <div class="shortage-header">
              <div class="shortage-icon">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                  <path d="M24 8L24 28M24 34L24 36" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                  <circle cx="24" cy="24" r="18" stroke="currentColor" stroke-width="3"/>
                </svg>
              </div>
              <div class="shortage-title-section">
                <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
                <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
              </div>
              <span class="priority-badge" :class="backlogItem.priority">
                {{ t('detailModal.priorityBadge', { priority: t('priority.' + backlogItem.priority) }) }}
              </span>
            </div>

            <div class="shortage-summary">
              <div class="summary-card danger">
                <div class="summary-label">{{ t('detailModal.shortageAmount') }}</div>
                <div class="summary-value">{{ t('detailModal.units', { count: shortage }) }}</div>
              </div>
              <div class="summary-card warning">
                <div class="summary-label">{{ t('detailModal.daysDelayed') }}</div>
                <div class="summary-value">{{ t('detailModal.days', { count: backlogItem.days_delayed }) }}</div>
              </div>
            </div>

            <div class="info-grid">
              <div class="info-item">
                <div class="info-label">{{ t('detailModal.orderId') }}</div>
                <div class="info-value order-id">{{ backlogItem.order_number }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('detailModal.itemSku') }}</div>
                <div class="info-value sku">{{ backlogItem.item_sku }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('detailModal.quantityNeeded') }}</div>
                <div class="info-value">{{ t('detailModal.units', { count: backlogItem.quantity_needed }) }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('detailModal.quantityAvailable') }}</div>
                <div class="info-value">{{ t('detailModal.units', { count: backlogItem.quantity_available }) }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">{{ t('inventory.table.status') }}</div>
                <div class="info-value">
                  <span class="badge danger">{{ t('status.backordered') }}</span>
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

const { t, translateProductName } = useI18n()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  backlogItem: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
})

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

.shortage-header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 1.5rem;
}

.shortage-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.shortage-title-section {
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

.priority-badge {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.priority-badge.high {
  background: var(--c-red-bg);
  color: var(--c-red-fg);
}

.priority-badge.medium {
  background: var(--c-orange-bg);
  color: var(--c-orange-fg);
}

.priority-badge.low {
  background: var(--c-blue-bg);
  color: var(--c-blue-fg);
}

.shortage-summary {
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

.summary-card.danger {
  border-color: var(--c-red-bg);
  background: var(--c-red-tint);
}

.summary-card.warning {
  border-color: var(--c-orange-bg);
  background: var(--c-amber-tint);
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

.summary-card.danger .summary-value {
  color: #dc2626;
}

.summary-card.warning .summary-value {
  color: #f59e0b;
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

.info-value.order-id,
.info-value.sku {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
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
