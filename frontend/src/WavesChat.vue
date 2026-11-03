<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { api } from './api'
defineEmits(['close'])
const messages = ref([]), question = ref(''), busy = ref(false), loading = ref(true), error = ref(''), mode = ref('unavailable')
const heading = ref(null)
const animatedReply = ref(null), readingId = ref(null), speechNotice = ref('')
const speechSupported = typeof window !== 'undefined' && 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window
const readAloud = ref(true)
const voices = ref([]), voiceURI = ref(''), speechRate = ref(0.9)
const voiceSettingsKey = 'waves-speech-settings'
function refreshVoices() {
  voices.value = window.speechSynthesis.getVoices().slice().sort((a, b) =>
    a.lang.localeCompare(b.lang) || a.name.localeCompare(b.name))
}
function restoreVoiceSettings() {
  try {
    const saved = JSON.parse(localStorage.getItem(voiceSettingsKey) || 'null')
    if (typeof saved?.voiceURI === 'string') voiceURI.value = saved.voiceURI
    if (typeof saved?.rate === 'number' && saved.rate >= 0.5 && saved.rate <= 1.5) speechRate.value = saved.rate
  } catch {}
}
function saveVoiceSettings() {
  const wasReading = readingId.value !== null
  stopReading()
  speechNotice.value = wasReading ? 'Voice settings updated. Press Read aloud to restart with your new settings.' : ''
  try { localStorage.setItem(voiceSettingsKey, JSON.stringify({ voiceURI: voiceURI.value, rate: speechRate.value })) } catch {}
}
let active = true, utterance = null
function stopReading() {
  utterance = null
  if (speechSupported) window.speechSynthesis.cancel()
  readingId.value = null
}
function speak(message) {
  stopReading(); speechNotice.value = ''
  if (!active || !speechSupported) return
  const speech = new SpeechSynthesisUtterance(message.content)
  utterance = speech
  const voice = voices.value.find(item => item.voiceURI === voiceURI.value)
  if (voice) speech.voice = voice
  speech.lang = voice?.lang || 'en-US'; speech.rate = speechRate.value
  readingId.value = message.id
  speech.onend = () => { if (utterance === speech) { readingId.value = null; utterance = null } }
  speech.onerror = () => {
    if (utterance !== speech) return
    readingId.value = null; utterance = null
    speechNotice.value = 'Audio could not start. Try the Read aloud button, or check your browser’s audio settings.'
  }
  window.speechSynthesis.speak(speech)
}
function toggleReading() { if (!readAloud.value) stopReading() }
function waveParts(text) { return text.match(/\S+\s*|\s+/g) || [] }
function waveDelay(index, text) { return `${index * Math.min(80, 4500 / Math.max(1, waveParts(text).length))}ms` }
onUnmounted(() => { active = false; stopReading(); window.removeEventListener('pagehide', stopReading); if (speechSupported) window.speechSynthesis.removeEventListener('voiceschanged', refreshVoices) })
const prompts = ['Help me choose an exercise', 'How does grounding work?', 'How do I trace a wave?']
async function load() {
  stopReading(); animatedReply.value = null
  loading.value = true; error.value = ''
  try {
    const [config, history] = await Promise.all([api('/coaching'), api('/chat/messages')])
    mode.value = config.mode; messages.value = history
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}
async function send(prompt) {
  if (busy.value || loading.value || mode.value !== 'live') return
  if (typeof prompt === 'string') question.value = prompt
  if (!question.value.trim()) return
  stopReading(); animatedReply.value = null
  busy.value = true; error.value = ''
  try {
    const result = await api('/chat/messages', { method: 'POST', body: JSON.stringify({content: question.value}) }, 20000)
    if (!active) return
    messages.value = result
    const reply = result.filter(message => message.role === 'assistant').at(-1)
    animatedReply.value = reply?.id
    if (reply && readAloud.value) speak(reply)
    question.value = ''
  } catch (e) {
    error.value = e.message
    try { messages.value = await api('/chat/messages') } catch {}
  } finally { busy.value = false }
}
async function clear() {
  stopReading(); animatedReply.value = null
  busy.value = true; error.value = ''
  try { await api('/chat/messages', {method:'DELETE'}); messages.value = []; question.value = '' }
  catch(e) { error.value = e.message }
  finally { busy.value = false }
}
onMounted(() => {
  heading.value?.focus()
  restoreVoiceSettings()
  if (speechSupported) {
    refreshVoices()
    window.speechSynthesis.addEventListener('voiceschanged', refreshVoices)
  }
  window.addEventListener('pagehide', stopReading)
  load()
})
</script>
<template>
  <section class="preparation">
    <p class="eyebrow">YOUR OPTIONAL EXERCISE GUIDE</p>
    <h1 ref="heading" tabindex="-1">Chat with Waves</h1>
    <p>Explore breathing, grounding, or tracing a wave. This AI guide is not a therapist. Use fictional practice questions only.</p>
    <p v-if="loading" role="status">Connecting to chat…</p>
    <p v-else-if="mode === 'live'">GPT-6 Luna · Live AI configured</p>
    <p v-else class="notice">Live chat is not configured. Run python3 backend/setup_api_key.py in your terminal, then refresh the connection. The exercises are still available.</p>
    <div class="chat-starters"><button v-for="prompt in prompts" :key="prompt" class="chat-starter" :disabled="busy || loading || mode !== 'live'" @click="send(prompt)">{{ prompt }}</button></div>
    <div class="speech-controls" v-if="speechSupported">
      <label><input type="checkbox" v-model="readAloud" @change="toggleReading"> Read new replies aloud</label>
      <button v-if="readingId !== null" class="text-button" @click="stopReading">Stop reading</button>
    </div>
    <p v-else class="chat-privacy">Read aloud is not supported in this browser. Replies are still available as text.</p>
    <fieldset v-if="speechSupported" class="voice-settings">
      <legend>Voice and speed</legend>
      <div class="voice-choice">
        <label for="chat-voice">Voice</label>
        <select id="chat-voice" v-model="voiceURI" @change="saveVoiceSettings">
          <option value="">Browser default</option>
          <option v-if="voiceURI && !voices.some(voice => voice.voiceURI === voiceURI)" :value="voiceURI">Saved voice unavailable — using browser default</option>
          <option v-for="voice in voices" :key="voice.voiceURI" :value="voice.voiceURI">{{ voice.name }} · {{ voice.lang }}</option>
        </select>
      </div>
      <div class="voice-speed">
        <label for="chat-speed">Speaking speed · {{ Number(speechRate).toFixed(1) }}×</label>
        <input id="chat-speed" type="range" v-model.number="speechRate" min="0.5" max="1.5" step="0.1" :aria-valuetext="`${speechRate} times normal speed`" @input="saveVoiceSettings">
        <div class="speed-labels"><span>Slower</span><span>Faster</span></div>
      </div>
      <button class="text-button" @click="speak({ id: 'preview', content: 'Hello, I’m Waves. Take your time and go at your own pace.' })">Preview voice</button>
      <p class="chat-privacy">Saved in this browser. Available voices depend on your device.</p>
    </fieldset>
    <p v-if="speechNotice" role="status">{{ speechNotice }}</p>
    <ol class="conversation" v-if="messages.length" aria-label="Conversation" aria-live="polite"><li v-for="message in messages" :key="message.id"><strong>{{ message.role === 'assistant' ? 'Waves · GPT-6 Luna' : 'You' }}</strong>
      <p v-if="message.id === animatedReply"><span class="screen-reader-text">{{ message.content }}</span><span aria-hidden="true"><span v-for="(word, index) in waveParts(message.content)" :key="index" class="reply-wave-word" :style="{ animationDelay: waveDelay(index, message.content) }">{{ word }}</span></span></p>
      <p v-else>{{ message.content }}</p>
      <button v-if="message.role === 'assistant' && speechSupported" class="text-button" @click="readingId === message.id ? stopReading() : speak(message)">{{ readingId === message.id ? 'Stop reading' : 'Read aloud' }}</button>
      <button v-if="message.id === animatedReply" class="text-button reveal-all" @click="animatedReply = null">Show full reply</button>
    </li></ol>
    <form @submit.prevent="send">
      <label for="chat-question">Fictional practice question</label>
      <textarea id="chat-question" v-model="question" maxlength="1000" :disabled="busy || loading || mode !== 'live'" placeholder="What can I try first?" />
      <button class="primary" :disabled="busy || loading || !question.trim() || mode !== 'live'">{{ busy ? 'Please wait…' : 'Send question' }}</button>
    </form>
    <p v-if="error" class="notice" role="alert">{{ error }}</p>
    <p class="chat-privacy">Questions and recent chat history are sent to OpenAI. Messages are saved locally to your account; the latest 100 appear here. Up to 6 requests per minute and 20 per hour. You can leave at any time.</p>
    <div class="history-actions"><button class="primary" @click="$emit('close')">Return to exercises</button><button v-if="messages.length" class="text-button" :disabled="busy || loading" @click="clear">Delete chat history</button><button v-if="!busy && !loading" class="text-button" @click="load">Refresh connection</button></div>
  </section>
</template>
<style scoped>
.chat-starters { display:flex; flex-wrap:wrap; gap:10px; margin:24px 0; }
.chat-starter { background:#104455; border:1px solid #80d0d3; border-radius:24px; padding:10px 16px; }
.conversation { list-style:none; padding:0; max-height:400px; overflow:auto; overflow-wrap:anywhere; }
.conversation li { background:#104455; padding:16px; margin:12px 0; border-radius:12px; }
.conversation p { white-space:pre-wrap; margin-bottom:0; }
textarea { display:block; width:100%; min-height:100px; margin:12px 0; padding:14px; font:inherit; color:inherit; background:#104455; border:1px solid #80d0d3; border-radius:12px; }
textarea:focus-visible { outline:3px solid #ffe19a; outline-offset:3px; }
.chat-privacy { font-size:12px; color:#d1e6e9; }
.speech-controls { display:flex; align-items:center; flex-wrap:wrap; gap:20px; margin-bottom:16px; }
.speech-controls label { display:flex; align-items:center; gap:8px; }
.speech-controls input { width:20px; height:20px; }
.voice-settings { border:1px solid #548c9b; border-radius:12px; padding:16px; margin:0 0 24px; display:flex; flex-wrap:wrap; gap:16px 24px; align-items:center; min-width:0; }
.voice-settings legend { padding:0 8px; }
.voice-choice { flex:1 1 230px; min-width:0; }
.voice-settings label { display:block; margin-bottom:8px; }
.voice-choice select { max-width:100%; }
.voice-speed { flex:1 1 180px; }
.voice-speed input { width:100%; accent-color:#9be6e5; }
.voice-speed input:focus-visible { outline:3px solid #ffe19a; outline-offset:4px; }
.speed-labels { display:flex; justify-content:space-between; font-size:12px; color:#d1e6e9; }
.voice-settings .chat-privacy { flex-basis:100%; margin:0; }
.reply-wave-word { display:inline-block; white-space:pre-wrap; animation: reply-wave .8s ease-out both; }
@keyframes reply-wave {
  0% { opacity:0; transform:translateY(7px); }
  50% { opacity:1; transform:translateY(-4px); }
  100% { opacity:1; transform:translateY(0); }
}
.screen-reader-text { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip-path:inset(50%); white-space:nowrap; }
.reveal-all { margin-left:18px; }
@media (prefers-reduced-motion: reduce) {
  .reply-wave-word { animation:none; opacity:1; transform:none; }
}
</style>
