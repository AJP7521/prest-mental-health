<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { api } from './api'
import { breathingState, groundingSteps } from './exercises'

const screen = ref('home'), skill = ref(''), elapsed = ref(0), step = ref(0)
const sessions = ref([]), loading = ref(false), notice = ref(''), saving = ref(false)
const heading = ref(null), supportFooter = ref(null), footerHeight = ref(120)
let footerObserver
let timer, startedAt, currentRun
const breath = computed(() => breathingState(elapsed.value))
const bubbleScale = computed(() => {
  const position = (elapsed.value / 1000) % 10
  const expansion = position < 4 ? position / 4 : 1 - (position - 4) / 6
  return 0.85 + 0.27 * (1 - Math.cos(Math.PI * expansion)) / 2
})
const grounding = computed(() => groundingSteps[step.value])
const showGroundingHelp = ref(false)
const groundingSuggestions = {
  see: 'You could notice a color, a shape, or an object near you.',
  feel: 'You could notice your feet against the floor or the texture of your clothing.',
  hear: 'You could listen for a nearby sound, like a fan or a distant voice.',
  smell: 'You could notice a scent already in the air. If nothing stands out, you can move on.',
  taste: 'You could notice a taste already in your mouth. If nothing stands out, you can move on.',
}
const title = computed(() => skill.value === 'breathing' ? 'Paced breathing' : '5-4-3-2-1 grounding')
async function focusHeading() { await nextTick(); heading.value?.focus() }
function start(selected) {
  clearInterval(timer)
  skill.value = selected; elapsed.value = 0; step.value = 0; notice.value = ''
  showGroundingHelp.value = false
  screen.value = 'exercise'; startedAt = performance.now()
  const run = { id: null, ending: null }
  currentRun = run
  saving.value = true
  run.ready = api('/sessions', { method: 'POST', body: JSON.stringify({ skill: selected }) })
    .then(session => { run.id = session.id })
    .catch(() => { if (currentRun === run) notice.value = 'This session could not be saved. You can still practice and stop at any time.' })
    .finally(() => { if (currentRun === run) saving.value = false })
  if (selected === 'breathing') timer = setInterval(() => {
    elapsed.value = performance.now() - startedAt
    if (breath.value.complete) finish('completed')
  }, 100)
  focusHeading()
}
async function finish(status) {
  const run = currentRun
  if (!run || run.ending) return
  run.ending = status
  clearInterval(timer)
  screen.value = status
  focusHeading()
  saving.value = true
  await run.ready
  if (run.id) {
    try { await api(`/sessions/${run.id}`, { method: 'PATCH', body: JSON.stringify({ status }) }) }
    catch { if (currentRun === run) notice.value = 'Your exercise has ended, but history could not be updated.' }
  }
  if (currentRun === run) saving.value = false
}
function nextStep() {
  showGroundingHelp.value = false
  if (step.value === groundingSteps.length - 1) finish('completed')
  else { step.value++; focusHeading() }
}
async function showHistory() {
  screen.value = 'history'; loading.value = true; notice.value = ''; sessions.value = []
  focusHeading()
  try { sessions.value = await api('/sessions') }
  catch (error) { notice.value = error.message }
  finally { loading.value = false }
}
async function clearHistory() {
  loading.value = true; notice.value = ''
  try { await api('/sessions', { method: 'DELETE' }); sessions.value = [] }
  catch (error) { notice.value = error.message }
  finally { loading.value = false }
}
function home() { screen.value = 'home'; notice.value = ''; focusHeading() }
onUnmounted(() => { clearInterval(timer); footerObserver?.disconnect() })
onMounted(() => {
  focusHeading()
  footerObserver = new ResizeObserver(([entry]) => {
    footerHeight.value = entry.target.getBoundingClientRect().height
  })
  footerObserver.observe(supportFooter.value)
})
</script>

<template>
  <div class="app-shell" :class="{ 'is-exercising': screen === 'exercise' }" :style="{ paddingBottom: `${footerHeight + 24}px` }">
    <div class="ocean-backdrop" aria-hidden="true"></div>
    <div class="swimming-fish" aria-hidden="true">
      <div v-for="fish in 4" :key="fish" class="fish-track" :class="`fish-track-${fish}`">
        <svg class="fish-sprite" viewBox="0 0 32 18" focusable="false" shape-rendering="crispEdges">
          <path fill="currentColor" d="M0 3h4v3h4V4h4V2h10v2h4v3h4v6h-4v3H12v-2H8v-2H4v3H0z" />
          <path fill="#fff0c0" opacity=".65" d="M12 4h10v2H12zM10 12h14v2H10z" />
          <path fill="#082d40" d="M24 7h2v2h-2z" />
          <path fill="#082d40" opacity=".25" d="M14 8h4v4h-2v-2h-2z" />
        </svg>
      </div>
    </div>
    <header><a href="#" class="brand" @click.prevent="screen === 'exercise' ? finish('stopped') : home()"><span class="brand-mark">◌</span> a little space</a><span class="prototype">LOCAL PROTOTYPE</span></header>
    <main>
      <template v-if="screen === 'home'">
        <div class="intro"><p class="eyebrow">A MOMENT FOR YOU</p><h1 ref="heading" tabindex="-1">Take a little<br><em>dive</em></h1><p class="lead">Choose a small exercise.<br>Go at your own pace. Stop whenever you like.</p></div>
        <div class="skill-grid">
          <button class="skill-card breathing-card" @click="start('breathing')"><span class="card-top"><span class="symbol" aria-hidden="true">🫧</span><span class="tag">60 SECONDS</span></span><h2>Paced breathing</h2><p>Follow a gentle rhythm.<br>In for 4, out for 6.</p><span class="card-link">Start breathing <span aria-hidden="true">↗</span></span></button>
          <button class="skill-card grounding-card" @click="start('grounding')"><span class="card-top"><span class="symbol" aria-hidden="true">🐚</span><span class="tag">AT YOUR PACE</span></span><h2>Find your surroundings</h2><p>Explore your five senses,<br>one small observation at a time.</p><span class="card-link">Start grounding <span aria-hidden="true">↗</span></span></button>
        </div>
        <div class="below-cards"><span>No right way to feel. No need to finish.</span><button class="text-button" @click="showHistory">View practice history →</button></div>
      </template>

      <section v-else-if="screen === 'exercise'" class="exercise">
        <p class="eyebrow">{{ title }}</p>
        <template v-if="skill === 'breathing'">
          <div class="breath-orbit" :style="{ '--bubble-scale': bubbleScale }"><div class="breath-bubble" aria-hidden="true"></div><div class="breath-core"><h1 ref="heading" tabindex="-1" aria-live="polite">{{ breath.phase }}</h1><p class="breath-counter" role="timer" aria-live="off" :aria-label="`${breath.counter} seconds ${breath.phase === 'Inhale' ? 'into inhale' : 'left in exhale'}`">{{ breath.counter }}<span aria-hidden="true">s</span></p></div></div>
          <p class="progress-label">Cycle {{ breath.cycle }} of 6 <span aria-hidden="true">·</span> {{ breath.remaining }}s remaining</p>
        </template>
        <template v-else>
          <p class="sense-number" aria-hidden="true">{{ grounding.total }}</p><h1 ref="heading" tabindex="-1" aria-live="polite">Notice something<br>you can <em>{{ grounding.sense }}.</em></h1><p class="progress-label">{{ grounding.item }} of {{ grounding.total }} things you can {{ grounding.sense }}</p>
          <button class="grounding-help-button" :aria-expanded="showGroundingHelp" aria-controls="grounding-help" @click="showGroundingHelp = !showGroundingHelp">Need Help?</button>
          <div id="grounding-help" role="status" aria-live="polite"><p v-if="showGroundingHelp" class="grounding-suggestion">{{ groundingSuggestions[grounding.sense] }}</p></div>
          <button class="primary" @click="nextStep">{{ step === 14 ? 'Finish exercise' : 'Next observation' }} →</button>
        </template>
        <button class="stop" @click="finish('stopped')">Stop and return</button>
      </section>

      <section v-else-if="screen === 'completed' || screen === 'stopped'" class="outcome">
        <span class="outcome-symbol" aria-hidden="true">◌</span><p class="eyebrow">{{ screen === 'completed' ? 'EXERCISE COMPLETE' : 'EXERCISE STOPPED' }}</p><h1 ref="heading" tabindex="-1">{{ screen === 'completed' ? 'A moment, just for you.' : 'You set the pace.' }}</h1><p class="lead">{{ screen === 'completed' ? 'Take your time before moving on.' : 'You can return whenever you choose.' }}</p><p v-if="saving" role="status">Saving session…</p><button class="primary" @click="home">Return to skills</button>
      </section>

      <section v-else class="history"><p class="eyebrow">YOUR PRACTICE</p><h1 ref="heading" tabindex="-1">Small moments.</h1><p class="lead">Session history on this device. Use fictional data only.</p><p v-if="loading" role="status">Loading…</p><p v-else-if="!sessions.length && !notice" class="empty">Your practice history will appear here.</p><ul v-else class="history-list"><li v-for="session in sessions" :key="session.id"><div><strong>{{ session.skill === 'breathing' ? 'Paced breathing' : '5-4-3-2-1 grounding' }}</strong><small>{{ new Date(session.started_at).toLocaleString() }}</small></div><span class="status">{{ session.status === 'active' ? 'Not recorded as finished' : session.status }}</span></li></ul><div class="history-actions"><button class="primary" @click="home">Return to skills</button><button v-if="sessions.length" class="text-button" :disabled="loading || saving" @click="clearHistory">Delete all prototype history</button><button v-if="notice" class="text-button" @click="showHistory">Retry</button></div></section>
      <p v-if="notice" role="status" class="notice">{{ notice }}</p>
    </main>
    <footer ref="supportFooter"><div class="support" aria-label="Fictional crisis support"><p class="support-number">Crisis support · Demo: <strong>000-000-0000</strong></p><p>Fictional number — does not connect to help</p></div></footer>
  </div>
</template>
