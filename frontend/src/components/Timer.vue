<template>
  <div class="timer" :class="{ warning: isWarning, danger: isDanger }">{{ display }}</div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
const props = defineProps({ durationMinutes: { type: Number, required: true } })
const emit = defineEmits(['expired'])
const remainingSeconds = ref(props.durationMinutes * 60)
let interval = null
const display = computed(() => {
  const m = Math.floor(remainingSeconds.value / 60)
  const s = remainingSeconds.value % 60
  return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
})
const isWarning = computed(() => remainingSeconds.value < props.durationMinutes * 60 * 0.25)
const isDanger = computed(() => remainingSeconds.value < 60)
function tick() { remainingSeconds.value--; if (remainingSeconds.value <= 0) { clearInterval(interval); emit('expired') } }
onMounted(() => { interval = setInterval(tick, 1000) })
onUnmounted(() => { if (interval) clearInterval(interval) })
</script>

<style scoped>
.timer { font-size:1.2rem; font-weight:600; font-family:'Inter', monospace; letter-spacing:0.05em; padding:0.375rem 0.75rem; background:rgba(255,255,255,0.15); border-radius:0.5rem; }
.warning { color:#fbbf24; }
.danger { color:#fca5a5; animation:blink 1s infinite; }
@keyframes blink { 50% { opacity:0.5; } }
</style>
