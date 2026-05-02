<template>
  <div>
    <h2>试卷管理</h2>
    <div v-if="!editingPaper">
      <button @click="showCreate=true">新建试卷</button>
      <table class="paper-table">
        <thead><tr><th>ID</th><th>名称</th><th>描述</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="p in papers" :key="p.id">
            <td>{{ p.id }}</td><td>{{ p.title }}</td><td>{{ trunc(p.description||'-',30) }}</td><td>{{ p.status }}</td>
            <td>
              <button @click="openPaper(p)" v-if="p.status==='draft'">编辑</button>
              <button class="danger" @click="doDelete(p.id)" v-if="p.status==='draft'">删除</button>
              <span v-else>-</span>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!papers.length">暂无试卷</p>
    </div>
    <div v-else class="editor">
      <div class="editor-header">
        <div>
          <button class="back" @click="closeEditor">← 返回列表</button>
          <h3>编辑: {{ editingPaper.title }}</h3>
        </div>
        <div class="editor-actions">
          <input v-model.number="randCount" type="number" placeholder="数量" style="width:70px" />
          <button @click="doRandom">随机选题</button>
          <button class="save-btn" @click="closeEditor">保存并返回</button>
        </div>
      </div>
      <div class="editor-body">
        <div class="selected-panel">
          <h4>已选题目 ({{ selectedQ.length }})</h4>
          <table v-if="selectedQ.length">
            <thead><tr><th class="col-no">#</th><th class="col-type">类型</th><th class="col-text">题目</th><th class="col-op">操作</th></tr></thead>
            <tbody>
              <tr v-for="(q,i) in selectedQ" :key="q.pq_id">
                <td class="col-no">{{ i+1 }}</td><td class="col-type">{{ typeLabel(q.type) }}</td>
                <td class="col-text">{{ trunc(q.question_text,80) }}</td>
                <td class="col-op"><button class="danger sm" @click="removeQ(q.pq_id)">移除</button></td>
              </tr>
            </tbody>
          </table>
          <p v-else>暂无题目</p>
        </div>
        <div class="available-panel">
          <h4>待选题目 ({{ filtered.length }})</h4>
          <div class="batch-bar">
            <button @click="batchAdd" :disabled="!selectedIds.size">批量添加 ({{ selectedIds.size }})</button>
            <button @click="selectedIds=new Set()">清空选择</button>
          </div>
          <input v-model="searchQ" placeholder="搜索题目..." />
          <table class="q-table">
            <thead><tr><th class="col-cb"><input type="checkbox" :checked="filtered.length>0 && selectedIds.size===filtered.length" @change="toggleAll" /></th><th>ID</th><th>类型</th><th>题目</th></tr></thead>
            <tbody>
              <tr v-for="q in filtered" :key="q.id" :class="{checked:selectedIds.has(q.id)}" @click="toggleSelect(q.id)">
                <td class="col-cb"><input type="checkbox" :checked="selectedIds.has(q.id)" /></td>
                <td>{{ q.id }}</td><td>{{ typeLabel(q.type) }}</td>
                <td>{{ trunc(q.question_text,80) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    <div v-if="showCreate" class="modal"><div class="modal-content">
      <h3>新建试卷</h3>
      <input v-model="newTitle" placeholder="试卷名称" />
      <textarea v-model="newDesc" placeholder="描述（可选）" rows="3"></textarea>
      <div class="modal-actions"><button @click="doCreate">创建</button><button @click="showCreate=false">取消</button></div>
    </div></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api'
const papers = ref([]), showCreate = ref(false), newTitle = ref(''), newDesc = ref('')
const editingPaper = ref(null), selectedQ = ref([]), allQ = ref([]), searchQ = ref(''), randCount = ref(5)
const selectedIds = ref(new Set())
const typeLabels = { choice_single:'单选', choice_multi:'多选', fill_blank:'填空', essay:'简答' }
function typeLabel(t) { return typeLabels[t]||t }
function trunc(s,n){ return s&&s.length>n?s.slice(0,n)+'...':s }

const filtered = computed(() => {
  const s = new Set(selectedQ.value.map(q=>q.question_id))
  const avail = allQ.value.filter(q=>!s.has(q.id))
  if(!searchQ.value) return avail
  const k=searchQ.value.toLowerCase()
  return avail.filter(q=>q.id.toString().includes(k)||q.question_text.toLowerCase().includes(k))
})

async function loadPapers(){ const { data }=await api.get('/papers/'); papers.value=data }
async function loadAllQ(){ const { data }=await api.get('/questions/'); allQ.value=data }

async function doCreate(){
  const { data } = await api.post('/papers/',{title:newTitle.value,description:newDesc.value})
  showCreate.value=false; newTitle.value=''; newDesc.value=''
  await loadPapers()
  openPaper(data)
}

async function openPaper(p){
  editingPaper.value=p
  const { data }=await api.get(`/papers/${p.id}/questions`)
  selectedQ.value=data
  selectedIds.value=new Set()
}

function closeEditor(){ editingPaper.value=null; selectedQ.value=[]; selectedIds.value=new Set() }

async function removeQ(pqId){
  await api.delete(`/papers/${editingPaper.value.id}/questions/${pqId}`)
  const { data }=await api.get(`/papers/${editingPaper.value.id}/questions`)
  selectedQ.value=data
}

async function batchAdd(){
  if(!selectedIds.value.size) return
  await api.post(`/papers/${editingPaper.value.id}/build`,{question_ids:[...selectedIds.value]})
  selectedIds.value=new Set()
  const { data }=await api.get(`/papers/${editingPaper.value.id}/questions`)
  selectedQ.value=data
}

async function doRandom(){
  await api.post(`/papers/${editingPaper.value.id}/build`,{strategy:'random',count:randCount.value})
  const { data }=await api.get(`/papers/${editingPaper.value.id}/questions`)
  selectedQ.value=data
}

async function doDelete(id){
  if(!confirm('确认删除该试卷？')) return
  try {
    await api.delete(`/papers/${id}`)
    await loadPapers()
  } catch(e) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

function toggleSelect(id){
  const s = new Set(selectedIds.value)
  if(s.has(id)) s.delete(id); else s.add(id)
  selectedIds.value = s
}

function toggleAll(){
  if(selectedIds.value.size===filtered.value.length){
    selectedIds.value=new Set()
  } else {
    selectedIds.value=new Set(filtered.value.map(q=>q.id))
  }
}

onMounted(()=>{ loadPapers(); loadAllQ() })
</script>

<style scoped>
.paper-table{width:100%;border-collapse:collapse;} .paper-table th,.paper-table td{padding:0.5rem;text-align:left;border-bottom:1px solid #e2e8f0;}
.modal{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;justify-content:center;align-items:center;z-index:100;}
.modal-content{background:white;padding:1.5rem;border-radius:8px;width:400px;} .modal-content input,.modal-content textarea{width:100%;padding:0.5rem;margin-bottom:0.5rem;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;}
.modal-actions{display:flex;gap:0.5rem;}
.danger{background:#ef4444;color:white;border:none;border-radius:4px;padding:0.25rem 0.75rem;cursor:pointer;} .danger:hover{background:#dc2626;}
.editor{margin-top:1rem;}
.editor-header{display:flex;justify-content:space-between;align-items:center;padding:0.75rem 1rem;background:#f8fafc;border-radius:8px;margin-bottom:1rem;}
.editor-header h3{margin:0.25rem 0 0;} .back{background:none;border:none;cursor:pointer;font-size:1rem;padding:0.25rem 0.5rem;}
.editor-actions{display:flex;gap:0.5rem;align-items:center;} .editor-actions input{padding:0.25rem;border:1px solid #ddd;border-radius:4px;}
.save-btn{background:#10b981;color:white;border:none;border-radius:4px;padding:0.5rem 1rem;cursor:pointer;}
.editor-body{display:flex;gap:1rem;align-items:flex-start;}
.selected-panel,.available-panel{flex:1;background:#f8fafc;padding:1rem;border-radius:8px;}
.selected-panel table,.q-table{width:100%;border-collapse:collapse;}
.selected-panel th,.selected-panel td,.q-table th,.q-table td{padding:0.35rem 0.75rem;text-align:left;border-bottom:1px solid #e2e8f0;font-size:0.875rem;}
.selected-panel td,.q-table td{vertical-align:middle;}
.col-no{width:40px;min-width:40px;} .col-type{width:80px;min-width:80px;} .col-cb{width:40px;min-width:40px;}
.col-op{width:80px;min-width:80px;} .col-text{text-align:left;}
.selected-panel p{margin-top:0.5rem;color:#94a3b8;}
.available-panel input[type="text"]{width:100%;padding:0.5rem;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;margin-bottom:0.5rem;}
.batch-bar{display:flex;gap:0.5rem;margin-bottom:0.5rem;} .batch-bar button{padding:0.25rem 0.75rem;border:1px solid #ddd;border-radius:4px;cursor:pointer;background:white;}
.q-table tbody tr{cursor:pointer;} .q-table tbody tr:hover{background:#eff6ff;} .q-table tbody tr.checked{background:#dbeafe;}
.q-table input[type="checkbox"]{margin:0;}
.sm{padding:0.15rem 0.5rem;font-size:0.75rem;}
</style>
