<template>
  <div>
    <h2>当前考试</h2>
    <div v-if="exams.length" class="grid">
      <div v-for="exam in exams" :key="exam.id" class="card">
        <h3>{{ exam.title }}</h3>
        <p>{{ exam.description }}</p>
        <p>题目: {{ exam.question_count }} | 时长: {{ exam.duration_minutes }} 分钟</p>
        <p>开放至: {{ new Date(exam.window_end).toLocaleString() }}</p>
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
async function load(){ const { data }=await api.get('/exams/available'); exams.value=data }
async function start(pid){ const { data }=await api.post('/exams/start',{paper_id:pid}); router.push(`/student/exam/${data.id}`) }
onMounted(load)
</script>

<style scoped>
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1rem;}
.card{padding:1rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;}
.card h3{margin-bottom:0.5rem;} .card p{margin:0.25rem 0;color:#64748b;}
.card button{margin-top:0.75rem;padding:0.5rem 1rem;background:#3b82f6;color:white;border:none;border-radius:4px;cursor:pointer;}
</style>
