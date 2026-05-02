<template>
  <div>
    <h2>当前考试</h2>
    <div v-if="exams.length" class="grid">
      <div v-for="exam in exams" :key="exam.id" class="card">
        <h3>{{ exam.title }}</h3>
        <p>{{ exam.description }}</p>
        <p>题目: {{ exam.question_count }} | 时长: {{ exam.duration_minutes }} 分钟</p>
        <p>开放至: {{ fmt(exam.window_end) }}</p>
        <button @click="start(exam.id)">开始考试</button>
      </div>
    </div>
    <p v-else>暂无可用考试</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'
const router = useRouter()
const exams = ref([])
function fmt(d){ return d?new Date(d+'Z').toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}):'-' }
async function load(){ const { data }=await api.get('/exams/available'); exams.value=data }
async function start(pid){ const { data }=await api.post('/exams/start',{paper_id:pid}); router.push(`/student/exam/${data.id}`) }
onMounted(load)
</script>

<style scoped>
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:1.5rem; }
.card { padding:1.5rem; background:#fff; border:1px solid #e4e1ee; border-radius:0.75rem; box-shadow:0 1px 3px rgba(30,41,59,0.08); transition:box-shadow 0.15s; }
.card:hover { box-shadow:0 4px 12px rgba(30,41,59,0.12); }
.card h3 { margin-bottom:0.5rem; }
.card p { margin:0.375rem 0; color:#464555; }
.card button { margin-top:1rem; padding:0.5rem 1.5rem; background:#3525cd; color:#fff; border:none; border-radius:0.5rem; cursor:pointer; min-height:44px; width:100%; }
.card button:hover { background:#4f46e5; }
</style>
