<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="modal-overlay" @click="$emit('close')">
        <div
          ref="dialog"
          class="modal-container"
          :class="{ large }"
          :style="{ maxWidth }"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="titleId"
          @click.stop
        >
          <div class="modal-header">
            <h3 :id="titleId" class="modal-title">{{ title }}</h3>
            <button type="button" class="close-button" :aria-label="t('common.close')" @click="$emit('close')">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick, onBeforeUnmount, useId } from 'vue'
import { useI18n } from '../composables/useI18n'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  title: { type: String, default: '' },
  maxWidth: { type: String, default: '700px' },
  large: { type: Boolean, default: false }
})
const emit = defineEmits(['close'])

const { t } = useI18n()
const titleId = useId()
const dialog = ref(null)
let previouslyFocused = null

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
const focusables = () => (dialog.value ? [...dialog.value.querySelectorAll(FOCUSABLE)] : [])

const onKeydown = (e) => {
  if (e.key === 'Escape') {
    emit('close')
    return
  }
  if (e.key !== 'Tab') return
  const items = focusables()
  if (!items.length) return
  const first = items[0]
  const last = items[items.length - 1]
  const active = document.activeElement
  if (!dialog.value?.contains(active)) {
    e.preventDefault()
    first.focus()
  } else if (e.shiftKey && active === first) {
    e.preventDefault()
    last.focus()
  } else if (!e.shiftKey && active === last) {
    e.preventDefault()
    first.focus()
  }
}

const release = () => {
  document.removeEventListener('keydown', onKeydown)
  if (previouslyFocused && previouslyFocused.isConnected) previouslyFocused.focus()
  previouslyFocused = null
}

watch(() => props.isOpen, async (open) => {
  if (open) {
    previouslyFocused = document.activeElement
    document.addEventListener('keydown', onKeydown)
    await nextTick()
    focusables()[0]?.focus()
  } else if (previouslyFocused) {
    release()
  }
}, { immediate: true })

onBeforeUnmount(() => {
  if (props.isOpen) release()
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: var(--surface);
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
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
  padding: 1.5rem;
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
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-button:hover {
  background: var(--surface-2);
  color: var(--text);
}

/* Tasks modal look */
.modal-container.large {
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-height: 85vh;
}

.large .modal-header {
  padding: 1.5rem 2rem;
  border-bottom-width: 2px;
}

.large .modal-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  letter-spacing: normal;
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
