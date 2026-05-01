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
.timer { font-size:1.2rem; font-weight:bold; font-family:monospace; }
.warning { color:#f59e0b; }
.danger { color:#ef4444; animation:blink 1s infinite; }
@keyframes blink { 50% { opacity:0.5; } }
</style>
