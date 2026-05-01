<template>
  <div>
    <h2>试卷管理</h2>
    <button @click="showCreate=true">新建试卷</button>
    <div v-if="showCreate" class="modal"><div class="modal-content">
      <h3>新建试卷</h3>
      <input v-model="newTitle" placeholder="试卷名称" />
      <textarea v-model="newDesc" placeholder="描述（可选）" rows="3"></textarea>
      <div class="modal-actions"><button @click="doCreate">创建</button><button @click="showCreate=false">取消</button></div>
    </div></div>
    <table><thead><tr><th>ID</th><th>名称</th><th>状态</th><th>操作</th></tr></thead>
      <tbody><tr v-for="p in papers" :key="p.id"><td>{{ p.id }}</td><td>{{ p.title }}</td><td>{{ p.status }}</td>
        <td><button @click="openPaper(p)" v-if="p.status==='draft'">编辑</button><span v-else>-</span></td></tr></tbody>
    </table>
    <div v-if="editingPaper" class="editor">
      <h3>编辑: {{ editingPaper.title }}</h3>
      <p>已选 {{ paperQuestions.length }} 道题</p>
      <div v-for="(pq,i) in paperQuestions" :key="pq.id" class="pq-item">{{ i+1 }}. {{ pq.question?.question_text || '题目'+pq.question_id }}</div>
      <h4>添加题目</h4>
      <input v-model="searchQ" placeholder="搜索题目..." />
      <div v-for="q in filtered" :key="q.id" class="q-item"><span>{{ q.id }}. {{ trunc(q.question_text,60) }}</span><button @click="addQ(q.id)">添加</button></div>
      <h4>随机选题</h4>
      <input v-model.number="randCount" type="number" placeholder="数量" style="width:80px" />
      <button @click="doRandom">随机选择</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api'
const papers = ref([]), showCreate = ref(false), newTitle = ref(''), newDesc = ref('')
const editingPaper = ref(null), paperQuestions = ref([]), allQ = ref([]), searchQ = ref(''), randCount = ref(5)
const filtered = computed(() => { if(!searchQ.value) return allQ.value; const s=searchQ.value.toLowerCase(); return allQ.value.filter(q=>q.id.toString().includes(s)||q.question_text.toLowerCase().includes(s)) })
function trunc(s,n){ return s&&s.length>n?s.slice(0,n)+'...':s }
async function loadPapers(){ const { data }=await api.get('/papers/'); papers.value=data }
async function loadAllQ(){ const { data }=await api.get('/questions/'); allQ.value=data }
async function doCreate(){ await api.post('/papers/',{title:newTitle.value,description:newDesc.value}); showCreate.value=false; newTitle.value=''; newDesc.value=''; await loadPapers() }
async function openPaper(p){ editingPaper.value=p; const { data }=await api.get(`/papers/${p.id}/questions`); paperQuestions.value=data }
async function addQ(id){ await api.post(`/papers/${editingPaper.value.id}/build`,{question_ids:[id]}); const { data }=await api.get(`/papers/${editingPaper.value.id}/questions`); paperQuestions.value=data }
async function doRandom(){ await api.post(`/papers/${editingPaper.value.id}/build`,{strategy:'random',count:randCount.value}); const { data }=await api.get(`/papers/${editingPaper.value.id}/questions`); paperQuestions.value=data }
onMounted(()=>{ loadPapers(); loadAllQ() })
</script>

<style scoped>
table{width:100%;border-collapse:collapse;} th,td{padding:0.5rem;text-align:left;border-bottom:1px solid #e2e8f0;}
.modal{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;justify-content:center;align-items:center;z-index:100;}
.modal-content{background:white;padding:1.5rem;border-radius:8px;width:400px;} .modal-content input,.modal-content textarea{width:100%;padding:0.5rem;margin-bottom:0.5rem;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;}
.modal-actions{display:flex;gap:0.5rem;}
.editor{margin-top:1.5rem;padding:1rem;background:#f8fafc;border-radius:8px;}
.q-item{display:flex;justify-content:space-between;padding:0.25rem 0;}
</style>
