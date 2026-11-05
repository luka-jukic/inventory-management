import { describe, it, expect } from 'vitest'
import en from '../src/locales/en.js'
import ja from '../src/locales/ja.js'

// Flatten nested translation objects into dotted keys
const keys = (obj, prefix = '') =>
  Object.entries(obj).flatMap(([k, v]) =>
    v && typeof v === 'object' ? keys(v, `${prefix}${k}.`) : [`${prefix}${k}`]
  )

// Name lookup tables that only exist in Japanese
const JA_ONLY = ['productNames.', 'customerNames.']

describe('locales', () => {
  it('ja has every English key', () => {
    const jaKeys = new Set(keys(ja))
    expect(keys(en).filter((k) => !jaKeys.has(k))).toEqual([])
  })

  it('ja has no keys missing in English', () => {
    const enKeys = new Set(keys(en))
    const extra = keys(ja).filter((k) => !enKeys.has(k) && !JA_ONLY.some((p) => k.startsWith(p)))
    expect(extra).toEqual([])
  })

  it('has no empty translations', () => {
    const empty = (obj) => keys(obj).filter((k) => k.split('.').reduce((o, p) => o[p], obj) === '')
    expect(empty(en)).toEqual([])
    expect(empty(ja)).toEqual([])
  })
})
