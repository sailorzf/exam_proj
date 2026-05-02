<template>
  <div>
    <h2>成绩列表</h2>
    <div class="filter-bar">
      <label>考试筛选：</label>
      <select v-model="paperId" @change="load">
        <option value="">全部</option>
        <option v-for="p in papers" :key="p.id" :value="p.id">{{ p.title }}</option>
      </select>
    </div>
    <table><thead><tr><th>考试轮次</th><th>学生姓名</th><th>客观分</th><th>主观分</th><th>总分</th></tr></thead>
      <tbody><tr v-for="s in sortedSubs" :key="s.session_id"><td>{{ paperName(s) }}</td><td>{{ s.student_name || s.student_username }}</td>
        <td>{{ s.auto_score??0 }}</td><td>{{ s.manual_score??0 }}</td>
        <td><strong>{{ (s.auto_score||0) + (s.manual_score||0) }}</strong></td></tr></tbody>
    </table>
    <p v-if="!sortedSubs.length">暂无答卷</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api'
const subs = ref([]), papers = ref([]), paperId = ref('')

const sortedSubs = computed(() => {
  return [...subs.value].sort((a, b) => ((b.auto_score||0) + (b.manual_score||0)) - ((a.auto_score||0) + (a.manual_score||0)))
})

const paperMap = computed(() => {
  const m = {}
  papers.value.forEach(p => m[p.id] = p.title)
  return m
})

function paperName(s) { return paperMap.value[s.paper_id] || '-' }

async function load(){
  const params = paperId.value ? `?paper_id=${paperId.value}` : ''
  const { data } = await api.get(`/submissions${params}`)
  subs.value = data
}
async function loadPapers(){ const { data }=await api.get('/papers/'); papers.value=data }
onMounted(()=>{ load(); loadPapers() })
</script>

<style scoped>
.card { background:#fff; border:1px solid #e4e1ee; border-radius:0.75rem; box-shadow:0 1px 3px rgba(30,41,59,0.08); overflow:hidden; }
.filter-bar { margin-bottom:1.5rem; display:flex; align-items:center; gap:0.75rem; }
.filter-bar select { padding:0.5rem 0.75rem; border:1px solid rgba(119,117,135,0.3); border-radius:0.5rem; min-height:44px; }
table { width:100%; border-collapse:collapse; }
th { position:sticky; top:0; background:#f0ecf9; z-index:1; font-weight:600; font-size:14px; color:#464555; padding:0.75rem 1rem; text-align:left; border-bottom:1px solid #e4e1ee; }
td { padding:0.75rem 1rem; text-align:left; border-bottom:1px solid #e4e1ee; font-size:14px; }
tbody tr:hover { background:#f5f2ff; }
</style>
