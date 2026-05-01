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
.exam{min-height:100vh;display:flex;flex-direction:column;}
.header{display:flex;justify-content:space-between;align-items:center;padding:0.75rem 1rem;background:#1e293b;color:white;}
.body{padding:1.5rem;flex:1;}
.footer{display:flex;justify-content:space-between;align-items:center;padding:0.75rem 1rem;background:#f8fafc;border-top:1px solid #e2e8f0;}
.dots{display:flex;gap:0.25rem;flex-wrap:wrap;}
.dots button{width:28px;height:28px;border:1px solid #e2e8f0;background:white;border-radius:4px;cursor:pointer;font-size:0.75rem;}
.dots button.active{background:#3b82f6;color:white;}
.dots button.answered{border-color:#10b981;}
.marked{background:#f59e0b;color:white!important;}
.submit{background:#ef4444;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer;}
.loading{text-align:center;padding:2rem;}
</style>
