import { describe, expect, it } from 'vitest'
import { breathingState, groundingSteps } from './exercises'

describe('exercise requirements', () => {
  it('uses six 4-second inhale and 6-second exhale cycles', () => {
    for (let cycle = 0; cycle < 6; cycle++) {
      expect(breathingState(cycle * 10000).phase).toBe('Inhale')
      expect(breathingState(cycle * 10000 + 3999).phase).toBe('Inhale')
      expect(breathingState(cycle * 10000 + 4000).phase).toBe('Exhale')
      expect(breathingState(cycle * 10000 + 9999).phase).toBe('Exhale')
    }
    expect(breathingState(59999).complete).toBe(false)
    expect(breathingState(60000).complete).toBe(true)
    expect(breathingState(95000).remaining).toBe(0)
  })
  it('counts up on inhale and down on exhale, including endpoints each cycle', () => {
    for (let cycle = 0; cycle < 6; cycle++) {
      const start = cycle * 10000
      expect([0, 1000, 2000, 3000, 3999].map(ms => breathingState(start + ms).counter)).toEqual([0, 1, 2, 3, 4])
      expect([4000, 5000, 6000, 7000, 8000, 9000, 9999].map(ms => breathingState(start + ms).counter)).toEqual([6, 5, 4, 3, 2, 1, 0])
    }
    expect(breathingState(60000).counter).toBe(0)
    expect(breathingState(95000).counter).toBe(0)
  })
  it('presents all 15 grounding items in the required order', () => {
    expect(groundingSteps.map(s => s.sense)).toEqual([
      ...Array(5).fill('see'), ...Array(4).fill('feel'), ...Array(3).fill('hear'), ...Array(2).fill('smell'), 'taste',
    ])
    expect(groundingSteps[0]).toEqual({ sense: 'see', item: 1, total: 5 })
    expect(groundingSteps.at(-1)).toEqual({ sense: 'taste', item: 1, total: 1 })
  })
})
