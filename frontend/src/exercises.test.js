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
  it('presents all 15 grounding items in the required order', () => {
    expect(groundingSteps.map(s => s.sense)).toEqual([
      ...Array(5).fill('see'), ...Array(4).fill('feel'), ...Array(3).fill('hear'), ...Array(2).fill('smell'), 'taste',
    ])
    expect(groundingSteps[0]).toEqual({ sense: 'see', item: 1, total: 5 })
    expect(groundingSteps.at(-1)).toEqual({ sense: 'taste', item: 1, total: 1 })
  })
})
