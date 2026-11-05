<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div
          class="modal-container"
          role="dialog"
          aria-modal="true"
          aria-labelledby="po-modal-title"
          @click.stop
        >
          <div class="modal-header">
            <h3 id="po-modal-title" class="modal-title">
              {{ mode === 'view' ? t('purchaseOrder.viewTitle') : t('purchaseOrder.createTitle') }}
            </h3>
            <button class="close-button" :aria-label="t('purchaseOrder.close')" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="item-summary">
              <div class="info-item">
                <div class="info-label">{{ t('purchaseOrder.item') }}</div>
                <div class="info-value">{{ translateProductName(backlogItem.item_name) }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">SKU</div>
                <div class="info-value mono">{{ backlogItem.item_sku }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">{{ t('purchaseOrder.orderId') }}</div>
                <div class="info-value mono">{{ backlogItem.order_id }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">{{ t('purchaseOrder.shortage') }}</div>
                <div class="info-value danger">{{ shortage }} {{ t('purchaseOrder.units') }}</div>
              </div>
            </div>

            <!-- View mode -->
            <template v-if="mode === 'view'">
              <div v-if="loading" class="state-text">{{ t('purchaseOrder.loading') }}</div>
              <div v-else-if="error" class="error-text" role="alert">{{ error }}</div>
              <div v-else-if="po" class="info-grid">
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.supplier') }}</div>
                  <div class="info-value">{{ po.supplier_name }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.status') }}</div>
                  <div class="info-value"><span class="badge">{{ po.status }}</span></div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.quantity') }}</div>
                  <div class="info-value">{{ po.quantity }} {{ t('purchaseOrder.units') }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.unitCost') }}</div>
                  <div class="info-value">{{ money(po.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.total') }}</div>
                  <div class="info-value">{{ money(po.quantity * po.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.expectedDelivery') }}</div>
                  <div class="info-value">{{ po.expected_delivery_date }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.createdDate') }}</div>
                  <div class="info-value">{{ po.created_date }}</div>
                </div>
                <div class="info-item full">
                  <div class="info-label">{{ t('purchaseOrder.notes') }}</div>
                  <div class="info-value">{{ po.notes || '-' }}</div>
                </div>
              </div>
            </template>

            <!-- Create mode -->
            <form v-else id="po-form" class="po-form" @submit.prevent="submit">
              <div class="field">
                <label for="po-supplier">{{ t('purchaseOrder.supplier') }}</label>
                <input id="po-supplier" v-model.trim="form.supplier_name" type="text" required />
              </div>
              <div class="field-row">
                <div class="field">
                  <label for="po-quantity">{{ t('purchaseOrder.quantity') }}</label>
                  <input id="po-quantity" v-model.number="form.quantity" type="number" min="1" step="1" required />
                </div>
                <div class="field">
                  <label for="po-unit-cost">{{ t('purchaseOrder.unitCost') }} (USD)</label>
                  <input id="po-unit-cost" v-model.number="form.unit_cost" type="number" min="0.01" step="0.01" required />
                </div>
              </div>
              <div class="field">
                <label for="po-delivery">{{ t('purchaseOrder.expectedDelivery') }}</label>
                <input id="po-delivery" v-model="form.expected_delivery_date" type="date" :min="today" required />
              </div>
              <div class="field">
                <label for="po-notes">{{ t('purchaseOrder.notes') }}</label>
                <textarea id="po-notes" v-model="form.notes" rows="3"></textarea>
              </div>
              <div class="total-row">
                <span>{{ t('purchaseOrder.total') }}</span>
                <strong>{{ money(total) }}</strong>
              </div>
              <div v-if="error" class="error-text" role="alert">{{ error }}</div>
            </form>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn-secondary" @click="close">{{ t('purchaseOrder.close') }}</button>
            <button
              v-if="mode !== 'view'"
              type="submit"
              form="po-form"
              class="btn-primary"
              :disabled="!isValid || saving"
            >
              {{ saving ? t('purchaseOrder.saving') : t('purchaseOrder.submit') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'PurchaseOrderModal',
  props: {
    isOpen: { type: Boolean, default: false },
    backlogItem: { type: Object, default: null },
    mode: { type: String, default: 'create' },
    unitCost: { type: Number, default: null }
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    const { t, currentCurrency, translateProductName } = useI18n()

    const form = reactive({
      supplier_name: '',
      quantity: 1,
      unit_cost: null,
      expected_delivery_date: '',
      notes: ''
    })
    const po = ref(null)
    const loading = ref(false)
    const saving = ref(false)
    const error = ref(null)

    // Local date, not UTC, so "today" matches the user's calendar
    const today = computed(() => {
      const d = new Date()
      const pad = (n) => String(n).padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
    })

    const shortage = computed(() =>
      props.backlogItem ? props.backlogItem.quantity_needed - props.backlogItem.quantity_available : 0
    )
    const total = computed(() => (Number(form.quantity) || 0) * (Number(form.unit_cost) || 0))
    const isValid = computed(() =>
      form.supplier_name.length > 0 &&
      Number.isInteger(form.quantity) && form.quantity >= 1 &&
      Number(form.unit_cost) > 0 &&
      form.expected_delivery_date >= today.value && form.expected_delivery_date !== ''
    )

    const money = (amount) => formatCurrencyWithDecimals(amount, currentCurrency.value, 2)

    const loadPO = async () => {
      loading.value = true
      po.value = null
      try {
        po.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
      } catch (err) {
        error.value = err.response?.data?.detail || t('purchaseOrder.loadError')
        console.error('Failed to load purchase order:', err)
      } finally {
        loading.value = false
      }
    }

    const submit = async () => {
      if (!isValid.value || saving.value) return
      saving.value = true
      error.value = null
      try {
        const created = await api.createPurchaseOrder({
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.supplier_name,
          quantity: form.quantity,
          unit_cost: form.unit_cost,
          expected_delivery_date: form.expected_delivery_date,
          notes: form.notes || null
        })
        emit('po-created', created)
      } catch (err) {
        const detail = err.response?.data?.detail
        error.value = typeof detail === 'string' ? detail : t('purchaseOrder.saveError')
        console.error('Failed to create purchase order:', err)
      } finally {
        saving.value = false
      }
    }

    const close = () => emit('close')

    // Reset state each time the modal opens
    watch(() => props.isOpen, (open) => {
      if (!open || !props.backlogItem) return
      error.value = null
      saving.value = false
      po.value = null
      if (props.mode === 'view') {
        loadPO()
      } else {
        form.supplier_name = ''
        form.quantity = Math.max(1, shortage.value)
        form.unit_cost = props.unitCost
        form.expected_delivery_date = ''
        form.notes = ''
      }
    }, { immediate: true })

    const onKeydown = (e) => {
      if (e.key === 'Escape' && props.isOpen) close()
    }
    onMounted(() => document.addEventListener('keydown', onKeydown))
    onUnmounted(() => document.removeEventListener('keydown', onKeydown))

    return {
      t, translateProductName, form, po, loading, saving, error,
      today, shortage, total, isValid, money, submit, close
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: var(--space-4);
}

.modal-container {
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5);
  border-bottom: 1px solid var(--border);
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: var(--space-2);
  display: flex;
  border-radius: var(--radius-sm);
  transition: all 0.15s ease;
}

.close-button:hover {
  background: #f1f5f9;
  color: var(--text);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.item-summary,
.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
}

.item-summary {
  padding: var(--space-4);
  background: var(--accent-soft);
  border-radius: var(--radius);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-width: 0;
}

.info-item.full {
  grid-column: 1 / -1;
}

.info-label,
.field label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.info-value {
  font-size: 0.938rem;
  font-weight: 500;
  color: var(--text);
  overflow-wrap: anywhere;
}

.info-value.mono {
  font-family: 'Monaco', 'Courier New', monospace;
  color: var(--accent);
}

.info-value.danger {
  color: var(--danger);
  font-weight: 700;
}

.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-sm);
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: capitalize;
}

.po-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  flex: 1;
}

.field-row {
  display: flex;
  gap: var(--space-4);
}

.field input,
.field textarea {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: 0.938rem;
  color: var(--text);
  background: var(--surface);
}

.field input:focus,
.field textarea:focus {
  outline: 2px solid var(--accent);
  outline-offset: -1px;
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--space-3);
  border-top: 1px solid var(--border);
  color: var(--text-muted);
}

.total-row strong {
  font-size: 1.25rem;
  color: var(--text);
}

.state-text {
  color: var(--text-muted);
}

.error-text {
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: var(--danger);
  font-size: 0.875rem;
}

.modal-footer {
  padding: var(--space-5);
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.btn-secondary,
.btn-primary {
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary {
  background: #f1f5f9;
  border: 1px solid var(--border);
  color: #334155;
}

.btn-secondary:hover {
  background: var(--border);
  border-color: #cbd5e1;
}

.btn-primary {
  background: var(--accent);
  border: 1px solid var(--accent);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
