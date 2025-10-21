import { describe, it, expect } from 'vitest'
import { formatDuration } from './formatters'

describe('formatDuration', () => {
  it('має правильно форматувати час менше години', () => {
    expect(formatDuration(846)).toBe('14 хв 06 сек')
  }),
  it('має додавати години, якщо тривалість більше години', () => {
    expect(formatDuration(3661)).toBe('01 год 01 хв 01 сек');
  })
})