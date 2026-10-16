export function breathingState(elapsedMs) {
  const elapsed = Math.max(0, elapsedMs / 1000)
  const position = elapsed % 10
  return { complete: elapsed >= 60, phase: position < 4 ? 'Inhale' : 'Exhale', remaining: Math.max(0, Math.ceil(60 - elapsed)), cycle: Math.min(6, Math.floor(elapsed / 10) + 1) }
}
export const groundingSteps = [
  ['see', 5], ['feel', 4], ['hear', 3], ['smell', 2], ['taste', 1],
].flatMap(([sense, total]) => Array.from({ length: total }, (_, i) => ({ sense, item: i + 1, total })))
