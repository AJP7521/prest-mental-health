<script setup>
import { computed, ref } from 'vue'
const position = ref(0)
const dragging = ref(null)
const waveY = x => 120 - 65 * Math.sin((x - 30) / 540 * Math.PI * 2)
const x = computed(() => 30 + position.value * 5.4)
const path = Array.from({ length: 181 }, (_, i) => {
  const px = 30 + i * 3
  return `${i ? 'L' : 'M'} ${px} ${waveY(px)}`
}).join(' ')
function move(event) {
  if (dragging.value !== event.pointerId) return
  const svg = event.currentTarget
  const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(svg.getScreenCTM().inverse())
  position.value = Math.max(0, Math.min(100, (point.x - 30) / 5.4))
}
function begin(event) {
  if (!event.isPrimary || event.button !== 0) return
  dragging.value = event.pointerId
  event.currentTarget.focus()
  event.currentTarget.setPointerCapture(event.pointerId)
  move(event)
}
function end(event) {
  if (dragging.value === event.pointerId) dragging.value = null
}
function key(event) {
  const change = { ArrowRight: 2, ArrowUp: 2, ArrowLeft: -2, ArrowDown: -2, PageUp: 10, PageDown: -10 }[event.key]
  if (change !== undefined || ['Home', 'End'].includes(event.key)) {
    event.preventDefault()
    position.value = event.key === 'Home' ? 0 : event.key === 'End' ? 100 : Math.max(0, Math.min(100, position.value + change))
  }
}
</script>

<template>
  <div class="wave-practice">
    <p id="wave-help">Drag along the wave with a finger or mouse. Move back and forth at your own pace.</p>
    <svg class="trace-wave" viewBox="0 0 600 240" tabindex="0" role="slider"
      aria-label="Position along the wave" aria-describedby="wave-help wave-keyboard"
      aria-valuemin="0" aria-valuemax="100" :aria-valuenow="Math.round(position)"
      :aria-valuetext="`${Math.round(position)} percent along the wave`"
      @pointerdown="begin" @pointermove="move" @pointerup="end" @pointercancel="end" @lostpointercapture="end" @keydown="key">
      <path :d="path" class="wave-halo" />
      <path :d="path" class="wave-line" />
      <circle :cx="x" :cy="waveY(x)" r="18" class="wave-marker" />
      <circle :cx="x - 4" :cy="waveY(x) - 5" r="4" fill="#fff" opacity=".7" />
    </svg>
    <p id="wave-keyboard" class="wave-hint">You can also focus the wave and use the arrow keys. No score, no need to stay on the line.</p>
  </div>
</template>

<style scoped>
.wave-practice { width: 100%; max-width: 680px; }
p { color: #d1e6e9; line-height: 1.7; }
.trace-wave { display: block; width: 100%; background: #104455; border: 1px solid #548c9b; border-radius: 24px; touch-action: none; cursor: grab; margin: 24px 0; }
.trace-wave:active { cursor: grabbing; }
.trace-wave:focus-visible { outline: 3px solid #ffe19a; outline-offset: 5px; }
.wave-halo { fill: none; stroke: #9be6e5; stroke-width: 26; opacity: .12; stroke-linecap: round; }
.wave-line { fill: none; stroke: #9be6e5; stroke-width: 4; stroke-linecap: round; }
.wave-marker { fill: #ffe19a; stroke: #082d40; stroke-width: 3; }
.wave-hint { font-size: 13px; margin-bottom: 24px; }
</style>
