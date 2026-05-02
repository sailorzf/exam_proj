<template>
  <div>
    <h2>答卷查看</h2>
    <div class="filter-bar">
      <label>考试筛选：</label>
      <select v-model="paperId" @change="load">
        <option value="">全部</option>
        <option v-for="p in papers" :key="p.id" :value="p.id">{{ p.title }}</option>
      </select>
    </div>
    <table><thead><tr><th>学生</th><th>状态</th><th>客观题分</th><th>主观题分</th><th>总分</th><th>提交时间</th><th>操作</th></tr></thead>
      <tbody><tr v-for="s in subs" :key="s.session_id"><td>{{ s.student_username }}</td><td>{{ statusLabel(s.status) }}</td>
        <td>{{ s.auto_score??'-' }}</td><td>{{ s.manual_score??'-' }}</td><td>{{ s.total_score??'-' }}</td>
        <td>{{ s.submit_time?new Date(s.submit_time).toLocaleString():'-' }}</td>
        <td><router-link :to="`/teacher/submissions/grade/${s.session_id}`" class="btn">阅卷</router-link>
            <button @click="doPub(s.session_id)" class="btn">成绩发布</button></td></tr></tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
const subs = ref([]), papers = ref([]), paperId = ref('')
const statusMap = { in_progress:'答题中', submitted:'已交卷', published:'成绩已公布' }
function statusLabel(s) { return statusMap[s]||s }
async function load(){
  const params = paperId.value ? `?paper_id=${paperId.value}` : ''
  const { data } = await api.get(`/submissions${params}`)
  subs.value = data
}
async function loadPapers(){ const { data }=await api.get('/papers/'); papers.value=data }
async function doPub(sid){ await api.post(`/submissions/${sid}/publish`); await load() }
onMounted(()=>{ load(); loadPapers() })
</script>

<style scoped>
table{width:100%;border-collapse:collapse;} th,td{padding:0.5rem;text-align:left;border-bottom:1px solid #e2e8f0;}
.filter-bar{margin-bottom:1rem;display:flex;align-items:center;gap:0.5rem;}
.filter-bar select{padding:0.25rem 0.5rem;border:1px solid #ddd;border-radius:4px;}
.btn{padding:0.25rem 0.75rem;border:1px solid #ddd;border-radius:4px;background:white;cursor:pointer;text-decoration:none;color:inherit;display:inline-block;font-size:0.875rem;}
.btn:hover{background:#f1f5f9;}
</style>
