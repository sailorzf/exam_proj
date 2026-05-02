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
    <table><thead><tr><th>考试轮次</th><th>学生</th><th>状态</th><th>客观题分</th><th>主观题分</th><th>总分</th><th>提交时间</th><th>操作</th></tr></thead>
      <tbody><tr v-for="s in subs" :key="s.session_id"><td>{{ paperName(s) }}</td><td>{{ s.student_name || s.student_username }}</td><td><span class="status-chip" :class="'status-'+s.status">{{ statusLabel(s.status) }}</span></td>
        <td>{{ s.auto_score??'-' }}</td><td>{{ s.manual_score??'-' }}</td><td>{{ s.total_score??'-' }}</td>
        <td>{{ fmt(s.submit_time) }}</td>
        <td><router-link :to="`/teacher/submissions/grade/${s.session_id}`" class="btn">阅卷</router-link>
            <button @click="doPub(s.session_id)" class="btn">成绩发布</button></td></tr></tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api'
const subs = ref([]), papers = ref([]), paperId = ref('')
const statusMap = { in_progress:'答题中', submitted:'已交卷', published:'成绩已公布' }
function statusLabel(s) { return statusMap[s]||s }
function fmt(d){ return d?new Date(d+'Z').toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}):'-' }
const paperMap = computed(() => { const m = {}; papers.value.forEach(p => m[p.id] = p.title); return m })
function paperName(s) { return paperMap.value[s.paper_id] || '-' }
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
.filter-bar { margin-bottom:1.5rem; display:flex; align-items:center; gap:0.75rem; }
.filter-bar select { padding:0.5rem 0.75rem; border:1px solid rgba(119,117,135,0.3); border-radius:0.5rem; min-height:44px; }
.card { background:#fff; border:1px solid #e4e1ee; border-radius:0.75rem; box-shadow:0 1px 3px rgba(30,41,59,0.08); overflow:hidden; }
table { width:100%; border-collapse:collapse; }
th { position:sticky; top:0; background:#f0ecf9; z-index:1; font-weight:600; font-size:14px; color:#464555; padding:0.75rem 1rem; text-align:left; border-bottom:1px solid #e4e1ee; }
td { padding:0.75rem 1rem; text-align:left; border-bottom:1px solid #e4e1ee; font-size:14px; }
tbody tr:hover { background:#f5f2ff; }
.btn { padding:0.5rem 1rem; border:1px solid #c7c4d8; border-radius:0.5rem; background:#fff; cursor:pointer; text-decoration:none; color:#464555; display:inline-block; font-size:14px; font-weight:500; min-height:44px; transition:all 0.15s; }
.btn:hover { border-color:#3525cd; color:#3525cd; background:#f5f2ff; }
.status-chip { display:inline-block; padding:0.25rem 0.625rem; border-radius:9999px; font-size:12px; font-weight:500; }
.status-in_progress { background:rgba(245,158,11,0.1); color:#b45309; }
.status-submitted { background:rgba(53,37,205,0.1); color:#3525cd; }
.status-published { background:rgba(16,185,129,0.1); color:#059669; }
</style>
