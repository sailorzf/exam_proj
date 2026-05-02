<template>
  <div class="exam" v-if="questions.length">
    <div class="header">
      <Timer :duration-minutes="duration" @expired="handleSubmit" />
      <span>题目 {{ ci+1 }}/{{ questions.length }}</span>
      <button @click="next" :disabled="ci>=questions.length-1">下一题</button>
    </div>
    <div class="body">
      <QuestionRenderer :question="questions[ci]" v-model="answers[ci]" :label="ci+1" />
    </div>
    <div class="footer">
      <button @click="prev" :disabled="ci===0">上一题</button>
      <button @click="toggleMark" :class="{marked:marked.has(ci)}">标记</button>
      <div class="dots">
        <button v-for="(q,i) in questions" :key="q.question_id" @click="ci=i" :class="{active:i===ci,answered:answers[i]}">{{ i+1 }}</button>
      </div>
      <button class="submit" @click="handleSubmit">提交试卷</button>
    </div>
  </div>
  <div v-else class="loading">加载中...</div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api'
import QuestionRenderer from '../../components/QuestionRenderer.vue'
import Timer from '../../components/Timer.vue'

const route = useRoute(), router = useRouter()
const sessionId = parseInt(route.params.id)
const questions = ref([]), answers = ref({}), ci = ref(0), marked = ref(new Set()), duration = ref(60)
let saveInterval = null

async function load(){
  const { data } = await api.get(`/exams/${sessionId}/questions`)
  questions.value = data
  const saved = localStorage.getItem('ea_'+sessionId)
  if (saved) answers.value = JSON.parse(saved)
}

watch(answers, (v) => localStorage.setItem('ea_'+sessionId, JSON.stringify(v)), { deep: true })

async function saveCurrent(){
  const q = questions.value[ci.value]
  if (!q || !answers.value[ci.value]) return
  try { await api.put(`/exams/${sessionId}/answer`, { question_id: q.question_id, answer: answers.value[ci.value] }) } catch(e) {}
}

onMounted(()=>{ load(); saveInterval=setInterval(saveCurrent, 10000) })
onUnmounted(()=>{ if(saveInterval) clearInterval(saveInterval) })

function prev(){ if(ci.value>0) ci.value-- }
function next(){ if(ci.value<questions.value.length-1) ci.value++ }
function toggleMark(){ if(marked.value.has(ci.value)) marked.value.delete(ci.value); else marked.value.add(ci.value); marked.value=new Set(marked.value) }

async function handleSubmit(){
  if(!confirm('确认提交？')) return
  for(const idx in answers.value){
    if(answers.value[idx]){ const q=questions.value[parseInt(idx)]; if(q) await api.put(`/exams/${sessionId}/answer`,{question_id:q.question_id,answer:answers.value[idx]}) }
  }
  await api.post(`/exams/${sessionId}/submit`)
  localStorage.removeItem('ea_'+sessionId)
  router.push('/student/results')
}
</script>

<style scoped>
.exam { min-height:100vh; display:flex; flex-direction:column; }
.header { display:flex; justify-content:space-between; align-items:center; padding:0.75rem 1.5rem; background:#3525cd; color:#fff; }
.header button { background:rgba(255,255,255,0.15); color:#fff; border:1px solid rgba(255,255,255,0.3); border-radius:0.5rem; min-height:44px; padding:0.5rem 1rem; }
.header button:hover { background:rgba(255,255,255,0.25); }
.header button:disabled { opacity:0.4; cursor:not-allowed; }
.body { padding:2rem; flex:1; }
.footer { display:flex; justify-content:space-between; align-items:center; padding:0.75rem 1.5rem; background:#f0ecf9; border-top:1px solid #e4e1ee; gap:1rem; flex-wrap:wrap; }
.footer button { padding:0.5rem 1rem; border:1px solid #c7c4d8; border-radius:0.5rem; background:#fff; cursor:pointer; min-height:44px; color:#464555; transition:all 0.15s; }
.footer button:hover:not(:disabled) { border-color:#3525cd; color:#3525cd; }
.footer button:disabled { opacity:0.4; cursor:not-allowed; }
.footer .submit { background:#ba1a1a; color:#fff; border:none; }
.footer .submit:hover { background:#dc2626; }
.footer .marked { background:#f59e0b; color:#fff; border-color:#f59e0b; }
.dots { display:flex; gap:0.375rem; flex-wrap:wrap; }
.dots button { width:36px; height:36px; border:1px solid #c7c4d8; background:#fff; border-radius:0.5rem; cursor:pointer; font-size:14px; font-weight:500; transition:all 0.15s; }
.dots button.active { background:#3525cd; color:#fff; border-color:#3525cd; }
.dots button.answered { border-color:#10b981; background:rgba(16,185,129,0.1); }
.loading { text-align:center; padding:3rem; color:#464555; }
</style>
