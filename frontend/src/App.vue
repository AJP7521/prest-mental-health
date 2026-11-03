<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import WavesChat from './WavesChat.vue'
import TraceWave from './TraceWave.vue'
import { api } from './api'
import { breathingState, groundingSteps } from './exercises'

const screen = ref('login'), skill = ref(''), elapsed = ref(0), step = ref(0)
const sessions = ref([]), loading = ref(false), notice = ref(''), saving = ref(false)
const recentSession = ref(null), recentDismissed = ref(false)
const pendingKey = computed(() => `mental-health-pending-session-${user.value?.id || 'anonymous'}`)
const user = ref(null), authLoading = ref(true), accountBusy = ref(false), registering = ref(false)
const username = ref(''), password = ref(''), displayName = ref(''), animateBreathing = ref(true)
const historyFilter = ref(''), historyOffset = ref(0)
async function restoreLogin() {
  authLoading.value = true
  try { user.value = await api('/profile'); screen.value = 'home'; await recover(); await loadRecentPractice() }
  catch (error) { if (error.status !== 401) notice.value = 'Could not connect. Check the server and try logging in again.' }
  finally { authLoading.value = false; focusHeading() }
}
async function authenticate() {
  accountBusy.value = true; notice.value = ''
  try {
    user.value = await api(registering.value ? '/auth/register' : '/auth/login', {
      method: 'POST', body: JSON.stringify({ username: username.value, password: password.value, display_name: displayName.value }) })
    password.value = ''; screen.value = 'home'; await recover(); await loadRecentPractice(); focusHeading()
  } catch (error) { notice.value = error.message }
  finally { accountBusy.value = false }
}
function showProfile() {
  displayName.value = user.value.display_name; animateBreathing.value = user.value.animate_breathing
  notice.value = ''; screen.value = 'profile'; focusHeading()
}
async function saveProfile() {
  accountBusy.value = true; notice.value = ''
  try {
    user.value = await api('/profile', { method: 'PATCH', body: JSON.stringify({ display_name: displayName.value, animate_breathing: animateBreathing.value }) })
    notice.value = 'Your profile is saved.'
  } catch (error) { notice.value = error.message }
  finally { accountBusy.value = false }
}
async function logout() {
  accountBusy.value = true; notice.value = ''
  try {
    await api('/auth/logout', { method: 'POST' })
    user.value = null; currentRun = null; sessions.value = []; recentSession.value = null
    username.value = ''; password.value = ''; displayName.value = ''; registering.value = false
    screen.value = 'login'; focusHeading()
  } catch (error) { notice.value = error.message }
  finally { accountBusy.value = false }
}
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
const senseEmojis = { see: '👀', feel: '✋', hear: '👂', smell: '👃', taste: '😋' }
const showGroundingHelp = ref(false)
const groundingSuggestions = {
  see: 'You could notice a color, a shape, or an object near you.',
  feel: 'You could notice your feet against the floor or the texture of your clothing.',
  hear: 'You could listen for a nearby sound, like a fan or a distant voice.',
  smell: 'You could notice a scent already in the air. If nothing stands out, you can move on.',
  taste: 'You could notice a taste already in your mouth. If nothing stands out, you can move on.',
}
const skillNames = { breathing: 'Paced breathing', grounding: '5-4-3-2-1 grounding', wave: 'Trace a wave' }
const title = computed(() => skillNames[skill.value])
async function loadRecentPractice() {
  recentDismissed.value = false
  try { recentSession.value = await api('/sessions/recent') }
  catch { recentSession.value = null }
}
async function focusHeading() { await nextTick(); heading.value?.focus() }
function remember(run, duration = 0) {
  if (!run?.id) return
  try { sessionStorage.setItem(pendingKey.value, JSON.stringify({ id: run.id, elapsed_ms: Math.round(duration) })) } catch {}
}
function forget(run) {
  try {
    if (JSON.parse(sessionStorage.getItem(pendingKey.value) || 'null')?.id === run.id) sessionStorage.removeItem(pendingKey.value)
  } catch {}
}
async function prepare(selected) {
  clearInterval(timer)
  skill.value = selected; elapsed.value = 0; step.value = 0; notice.value = ''
  showGroundingHelp.value = false
  screen.value = 'prepare'; startedAt = null
  const run = { id: null, ending: null }
  currentRun = run
  saving.value = true
  run.ready = api('/sessions', { method: 'POST', body: JSON.stringify({ skill: selected }) })
    .then(session => { run.id = session.id; remember(run) })
    .catch(() => { if (currentRun === run) notice.value = 'This session could not be saved. You can still practice and stop at any time.' })
    .finally(() => { if (currentRun === run) saving.value = false })
  focusHeading()
}
async function start() {
  const run = currentRun
  if (!run || run.starting || run.ending) return
  run.starting = true
  await run.ready
  if (run.ending || currentRun !== run) return
  if (run.id) {
    try { await api(`/sessions/${run.id}/begin`, { method: 'POST' }) }
    catch { notice.value = 'Start time could not be saved. You can still practice and stop.' }
  }
  if (run.ending || currentRun !== run) return
  startedAt = performance.now(); screen.value = 'exercise'
  remember(run)
  timer = setInterval(() => {
    elapsed.value = performance.now() - startedAt
    remember(run, elapsed.value)
    if (skill.value === 'breathing' && breath.value.complete) {
      finish(elapsed.value < 90000 ? 'completed' : 'stopped', elapsed.value < 90000 ? 'completed' : 'interrupted')
    }
  }, 100)
  focusHeading()
}
async function finish(status, reason = status) {
  const run = currentRun
  if (!run || run.ending) return
  run.ending = status
  elapsed.value = startedAt === null ? 0 : performance.now() - startedAt
  remember(run, elapsed.value)
  clearInterval(timer)
  screen.value = status
  focusHeading()
  saving.value = true
  await run.ready
  if (run.id) {
    try {
      const ended = await api(`/sessions/${run.id}`, { method: 'PATCH', body: JSON.stringify({ status, end_reason: reason, elapsed_ms: Math.round(elapsed.value) }) })
      if (ended.exercise_started_at) recentSession.value = ended
      forget(run)
    } catch { if (currentRun === run) notice.value = 'Your exercise has ended, but history could not be updated. The next visit will try to mark this session interrupted.' }
  }
  if (currentRun === run) saving.value = false
}
function leave() {
  const run = currentRun
  if (!run || run.ending) return
  const duration = startedAt === null ? 0 : performance.now() - startedAt
  remember(run, duration)
  clearInterval(timer)
  if (run.id) fetch(`/api/sessions/${run.id}`, { method: 'PATCH', keepalive: true,
    headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'mental-health-app' },
    body: JSON.stringify({ status: 'stopped', end_reason: 'interrupted', elapsed_ms: Math.round(duration) }) }).catch(() => {})
}
async function recover() {
  try {
    const pending = JSON.parse(sessionStorage.getItem(pendingKey.value) || 'null')
    if (!pending) return
    await api(`/sessions/${pending.id}`, { method: 'PATCH', body: JSON.stringify({ status: 'stopped', end_reason: 'interrupted', elapsed_ms: pending.elapsed_ms }) })
    forget(pending)
    notice.value = 'Your previous unfinished visit was recorded as interrupted. You can choose a new exercise.'
  } catch { notice.value = 'A previous visit may not have saved its ending. History can show it as unfinished.' }
}
function nextStep() {
  showGroundingHelp.value = false
  if (step.value === groundingSteps.length - 1) finish('completed')
  else { step.value++; focusHeading() }
}
async function showHistory(reset = true) {
  if (reset !== false) historyOffset.value = 0
  screen.value = 'history'; loading.value = true; notice.value = ''; sessions.value = []
  focusHeading()
  try { sessions.value = await api(`/sessions?limit=20&offset=${historyOffset.value}${historyFilter.value ? `&skill=${historyFilter.value}` : ''}`) }
  catch (error) { notice.value = error.message }
  finally { loading.value = false }
}
const deletingSession = ref(null)
async function deleteSession(session) {
  if (deletingSession.value) return
  deletingSession.value = session.id; notice.value = ''
  try {
    await api(`/sessions/${session.id}`, { method: 'DELETE' })
    forget(session)
    if (recentSession.value?.id === session.id) await loadRecentPractice()
    if (sessions.value.length === 1 && historyOffset.value > 0) historyOffset.value -= 20
    await showHistory(false)
  } catch (error) { notice.value = error.message }
  finally { deletingSession.value = null }
}
async function clearHistory() {
  loading.value = true; notice.value = ''
  try { await api('/sessions', { method: 'DELETE' }); sessions.value = []; recentSession.value = null; historyOffset.value = 0 }
  catch (error) { notice.value = error.message }
  finally { loading.value = false }
}
function home() { if (!user.value) { screen.value = 'login'; return }; if ((screen.value === 'prepare' || screen.value === 'exercise') && !currentRun?.ending) { finish('stopped'); return }; screen.value = 'home'; notice.value = ''; focusHeading() }
function restorePage(event) { if (event.persisted) window.location.reload() }
onUnmounted(() => { clearInterval(timer); footerObserver?.disconnect(); window.removeEventListener('pagehide', leave); window.removeEventListener('pageshow', restorePage) })
onMounted(() => {
  window.addEventListener('pagehide', leave)
  window.addEventListener('pageshow', restorePage)
  restoreLogin()
  focusHeading()
  footerObserver = new ResizeObserver(([entry]) => {
    footerHeight.value = entry.target.getBoundingClientRect().height
  })
  footerObserver.observe(supportFooter.value)
})
</script>

<template>
  <div class="app-shell" :class="{ 'is-exercising': screen === 'exercise', 'text-pacing': user && !user.animate_breathing }" :style="{ paddingBottom: `${footerHeight + 24}px` }">
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
    <header><a href="#" class="brand" aria-label="Waves — home" @click.prevent="screen === 'exercise' ? finish('stopped') : home()"><svg class="waves-wordmark" viewBox="0 0 180 72" aria-hidden="true"><g v-for="(letter, index) in 'Waves'" :key="index" class="waves-letter" :style="{ animationDelay: `${-index * 0.32}s` }"><text :x="26 + index * 32" :y="[40, 36, 38, 43, 44][index]" text-anchor="middle">{{ letter }}</text></g><path class="waves-ripple" d="M36 58 C58 47 75 49 94 57 S129 65 149 54" /></svg></a><span class="prototype">LOCAL PROTOTYPE</span></header>
    <nav v-if="user && !['exercise', 'prepare', 'chat'].includes(screen)" class="account-nav" aria-label="Account navigation">
      <button class="text-button" @click="home">Skills</button><button class="text-button" @click="showHistory()">My history</button><button class="text-button" @click="showProfile">My profile</button><button class="text-button" :disabled="accountBusy || saving" @click="logout">Log out</button>
    </nav>
    <main>
      <section v-if="screen === 'login'" class="account-panel">
        <p class="eyebrow">YOUR OWN LITTLE SPACE</p>
        <h1 ref="heading" tabindex="-1">{{ registering ? 'Create an account' : 'Welcome back' }}</h1>
        <p class="lead">Save your profile and follow your practice over time.</p>
        <p>This is a coursework skills prototype, not a therapist or diagnostic tool. Use a fictional name and practice information.</p>
        <p v-if="authLoading" role="status">Checking your login…</p>
        <form v-else @submit.prevent="authenticate" class="account-form">
          <label for="username">Username</label><input id="username" v-model="username" autocomplete="username" required minlength="3" maxlength="40" pattern="[A-Za-z0-9_]{3,40}" aria-describedby="username-help"><small id="username-help">3–40 letters, numbers, or underscores.</small>
          <template v-if="registering"><label for="display-name">Display name</label><input id="display-name" v-model="displayName" required maxlength="60" autocomplete="nickname"></template>
          <label for="password">Password</label><input id="password" v-model="password" type="password" :autocomplete="registering ? 'new-password' : 'current-password'" required minlength="10" maxlength="128" aria-describedby="password-help"><small id="password-help">Use 10–128 characters. Accounts are saved on this local server.</small>
          <button class="primary" :disabled="accountBusy">{{ accountBusy ? 'Please wait…' : registering ? 'Create account' : 'Log in' }}</button>
          <button type="button" class="text-button" :disabled="accountBusy" @click="registering = !registering; notice = ''; password = ''">{{ registering ? 'Already have an account? Log in' : 'New here? Create an account' }}</button>
        </form>
      </section>
      <section v-else-if="screen === 'profile'" class="account-panel">
        <p class="eyebrow">SAVED FOR YOUR NEXT VISIT</p><h1 ref="heading" tabindex="-1">Your profile</h1>
        <p>Username: <strong>{{ user.username }}</strong></p>
        <form @submit.prevent="saveProfile" class="account-form">
          <label for="profile-name">Display name</label><input id="profile-name" v-model="displayName" required maxlength="60" autocomplete="nickname">
          <label class="checkbox-label"><input type="checkbox" v-model="animateBreathing"> Animate the breathing bubble</label>
          <p>Turn this off for text-only pacing. Your system’s reduced-motion preference is always respected.</p>
          <button class="primary" :disabled="accountBusy">{{ accountBusy ? 'Saving…' : 'Save profile' }}</button>
        </form>
        <p>Member since {{ new Date(user.created_at).toLocaleDateString() }}. Your profile and exercise history remain saved when you log out.</p>
        <button class="text-button" @click="home">Return to skills</button>
      </section>
      <template v-else-if="screen === 'home'">
        <div class="intro"><p class="eyebrow">A MOMENT FOR {{ user.display_name }}</p><h1 ref="heading" tabindex="-1">Take a little<br><em>dive</em></h1><p class="lead">Choose a small exercise.<br>Go at your own pace. Stop whenever you like.</p></div>
        <aside v-if="recentSession && !recentDismissed" class="repeat-practice" aria-label="Optional repeat suggestion">
          <p><strong>Your recent practice:</strong> {{ skillNames[recentSession.skill] }}. You can choose it again or try something else.</p>
          <div><button class="text-button" @click="prepare(recentSession.skill)">Practice again</button><button class="text-button" @click="recentDismissed = true">Not now</button></div>
        </aside>
        <div class="skill-grid">
          <button class="skill-card breathing-card" @click="prepare('breathing')"><span class="card-top"><span class="symbol" aria-hidden="true">🫧</span><span class="tag">60 SECONDS</span></span><h2>Paced breathing</h2><p>Follow a gentle rhythm.<br>In for 4, out for 6.</p><span class="card-link">Start breathing <span aria-hidden="true">↗</span></span></button>
          <button class="skill-card grounding-card" @click="prepare('grounding')"><span class="card-top"><span class="symbol" aria-hidden="true">🐚</span><span class="tag">AT YOUR PACE</span></span><h2>Find your surroundings</h2><p>Explore your five senses,<br>one small observation at a time.</p><span class="card-link">Start grounding <span aria-hidden="true">↗</span></span></button>
          <button class="skill-card wave-card" @click="prepare('wave')"><span class="card-top"><span class="symbol" aria-hidden="true">🌊</span><span class="tag">AT YOUR PACE</span></span><h2>Trace a wave</h2><p>Follow the curve with your finger or mouse.<br>No score. Just your own pace.</p><span class="card-link">Start tracing <span aria-hidden="true">↗</span></span></button>
          <button class="skill-card chat-card" @click="screen = 'chat'; notice = ''"><span class="card-top"><span class="symbol" aria-hidden="true">💬</span><span class="tag">OPTIONAL GUIDE</span></span><h2>Chat with Waves</h2><p>Explore your next small step.<br>An AI guide, at your pace.</p><span class="card-link">Start chatting <span aria-hidden="true">↗</span></span></button>
        </div>
        <div class="below-cards"><span>No right way to feel. No need to finish.</span><button class="text-button" @click="showHistory">View practice history →</button></div>
      </template>

      <WavesChat v-else-if="screen === 'chat'" @close="home" />

      <section v-else-if="screen === 'prepare'" class="preparation">
        <p class="eyebrow">YOUR CHOICE</p><h1 ref="heading" tabindex="-1">{{ title }}</h1>
        <p>{{ skill === 'breathing' ? 'Six cycles: inhale 4 seconds, exhale 6 seconds. Target: 60 seconds.' : skill === 'wave' ? 'Move a glowing pebble along a wave using your finger, mouse, or arrow keys. Finish whenever you like.' : 'Notice your senses, one observation at a time.' }} Stop whenever you choose.</p>
        <p v-if="saving" role="status">Preparing session…</p>
        <div class="history-actions"><button class="primary" :disabled="saving" @click="start">{{ skill === 'breathing' ? 'Start 60-second breathing exercise' : skill === 'wave' ? 'Start tracing' : 'Start observations' }}</button><button class="text-button" @click="finish('stopped')">Return without starting</button></div>
      </section>

      <section v-else-if="screen === 'exercise'" class="exercise">
        <p class="eyebrow">{{ title }}</p>
        <template v-if="skill === 'breathing'">
          <div class="breath-orbit" :style="{ '--bubble-scale': bubbleScale }"><div class="breath-bubble" aria-hidden="true"></div><div class="breath-core"><h1 ref="heading" tabindex="-1" aria-live="polite">{{ breath.phase }}</h1><p class="breath-counter" role="timer" aria-live="off" :aria-label="`${breath.counter} seconds ${breath.phase === 'Inhale' ? 'into inhale' : 'left in exhale'}`">{{ breath.counter }}<span aria-hidden="true">s</span></p></div></div>
          <p class="progress-label">Cycle {{ breath.cycle }} of 6 <span aria-hidden="true">·</span> {{ breath.remaining }}s remaining</p>
        </template>
        <template v-else-if="skill === 'wave'">
          <h1 ref="heading" tabindex="-1">Follow the wave.</h1>
          <TraceWave />
          <button class="primary" @click="finish('completed')">Finish tracing</button>
        </template>
        <template v-else>
          <p class="sense-emoji" aria-hidden="true">{{ senseEmojis[grounding.sense] }}</p><h1 ref="heading" tabindex="-1" aria-live="polite">Notice something<br>you can <em>{{ grounding.sense }}.</em></h1><p class="progress-label">{{ grounding.item }} of {{ grounding.total }} things you can {{ grounding.sense }}</p>
          <button class="grounding-help-button" :aria-expanded="showGroundingHelp" aria-controls="grounding-help" @click="showGroundingHelp = !showGroundingHelp">Need Help?</button>
          <div id="grounding-help" role="status" aria-live="polite"><p v-if="showGroundingHelp" class="grounding-suggestion">{{ groundingSuggestions[grounding.sense] }}</p></div>
          <button class="primary" @click="nextStep">{{ step === 14 ? 'Finish exercise' : 'Next observation' }} →</button>
        </template>
        <button class="stop" @click="finish('stopped')">Stop and return</button>
      </section>

      <section v-else-if="screen === 'completed' || screen === 'stopped'" class="outcome">
        <span class="outcome-symbol" aria-hidden="true">◌</span><p class="eyebrow">{{ screen === 'completed' ? 'EXERCISE COMPLETE' : 'EXERCISE STOPPED' }}</p><h1 ref="heading" tabindex="-1">{{ screen === 'completed' ? 'A moment, just for you.' : 'You set the pace.' }}</h1><p class="lead">{{ screen === 'completed' ? 'Take your time before moving on.' : 'You can return whenever you choose.' }}</p><p>Measured exercise time: {{ (elapsed / 1000).toFixed(1) }} seconds.</p><p v-if="saving" role="status">Saving session…</p><p v-if="notice" role="status" class="notice">{{ notice }}</p><button class="primary" @click="home">Return to skills</button>
      </section>

      <section v-else class="history"><p class="eyebrow">YOUR PRACTICE</p><h1 ref="heading" tabindex="-1">Small moments.</h1><p class="lead">{{ user.display_name }}’s saved exercise history. Use fictional data only.</p><div class="history-filter"><label for="history-skill">Exercise</label><select id="history-skill" v-model="historyFilter" :disabled="loading" @change="showHistory()"><option value="">All exercises</option><option value="breathing">Paced breathing</option><option value="grounding">5-4-3-2-1 grounding</option><option value="wave">Trace a wave</option></select><p>Showing up to 20 sessions per page.</p></div><p v-if="loading" role="status">Loading…</p><p v-else-if="!sessions.length && !notice" class="empty">Your practice history will appear here.</p><ul v-else class="history-list"><li v-for="session in sessions" :key="session.id"><div><strong>{{ skillNames[session.skill] }}</strong><small>{{ new Date(session.started_at).toLocaleString() }}</small></div><span class="status">{{ session.status === 'active' ? 'Not recorded as finished' : (session.end_reason || session.status) }}<small>{{ session.elapsed_ms === null ? 'Duration not recorded' : `${(session.elapsed_ms / 1000).toFixed(1)} seconds` }}</small><button class="text-button" :disabled="loading || saving || !!deletingSession" :aria-label="`Delete ${skillNames[session.skill]} session from ${new Date(session.started_at).toLocaleString()}`" title="Delete this session" @click="deleteSession(session)">{{ deletingSession === session.id ? 'Deleting…' : 'Delete' }}</button></span></li></ul><div class="history-actions"><button v-if="historyOffset > 0" class="text-button" :disabled="loading" @click="historyOffset -= 20; showHistory(false)">Previous page</button><button v-if="sessions.length === 20" class="text-button" :disabled="loading" @click="historyOffset += 20; showHistory(false)">Next page</button><button class="primary" @click="home">Return to skills</button><button v-if="sessions.length" class="text-button" :disabled="loading || saving || !!deletingSession" @click="clearHistory">Delete my exercise history</button><button v-if="notice" class="text-button" @click="showHistory">Retry</button></div></section>
      <p v-if="notice && screen !== 'completed' && screen !== 'stopped'" role="status" class="notice">{{ notice }}</p>
    </main>
    <footer ref="supportFooter"><div class="support" aria-label="Fictional crisis support"><p class="support-number">Crisis support · Demo: <strong>000-000-0000</strong></p><p>Fictional number — does not connect to help</p><a href="/support.html">Open fictional support</a></div></footer>
  </div>
</template>
