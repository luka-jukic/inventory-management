import { describe, it, expect, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import BaseModal from '../src/components/BaseModal.vue'

const press = (key, opts = {}) =>
  document.activeElement.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, ...opts }))

let wrapper
let opener

// Opens the modal the way the app does: focus a trigger, then set isOpen
const open = async () => {
  opener = document.createElement('button')
  document.body.appendChild(opener)
  opener.focus()
  wrapper = mount(BaseModal, {
    props: { isOpen: false, title: 'Item details' },
    slots: { default: '<input id="first-field" /><button id="save">Save</button>' },
    attachTo: document.body
  })
  await wrapper.setProps({ isOpen: true })
  await nextTick()
  return document.querySelector('[role="dialog"]')
}

afterEach(() => {
  wrapper?.unmount()
  opener?.remove()
  document.body.innerHTML = ''
})

describe('BaseModal', () => {
  it('renders nothing while closed', () => {
    wrapper = mount(BaseModal, { props: { isOpen: false, title: 'x' }, attachTo: document.body })
    expect(document.querySelector('[role="dialog"]')).toBeNull()
  })

  it('is an accessible modal dialog', async () => {
    const dialog = await open()
    expect(dialog.getAttribute('aria-modal')).toBe('true')
    const title = document.getElementById(dialog.getAttribute('aria-labelledby'))
    expect(title.textContent).toBe('Item details')
    expect(dialog.querySelector('.close-button').getAttribute('aria-label')).toBe('Close')
  })

  it('moves focus into the dialog on open', async () => {
    const dialog = await open()
    expect(dialog.contains(document.activeElement)).toBe(true)
  })

  it('emits close on Escape', async () => {
    await open()
    press('Escape')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('emits close on overlay click but not on dialog click', async () => {
    const dialog = await open()
    dialog.click()
    expect(wrapper.emitted('close')).toBeUndefined()
    document.querySelector('.modal-overlay').click()
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('traps Tab inside the dialog', async () => {
    await open()
    const close = document.querySelector('.close-button')
    const save = document.getElementById('save')
    save.focus()
    press('Tab')
    expect(document.activeElement).toBe(close)
    press('Tab', { shiftKey: true })
    expect(document.activeElement).toBe(save)
  })

  it('returns focus to the opener on close', async () => {
    await open()
    await wrapper.setProps({ isOpen: false })
    expect(document.activeElement).toBe(opener)
  })
})
