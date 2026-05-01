<template>
  <div>
    <div class="header"><h2>题库管理</h2>
      <div class="actions"><button @click="showImport=true">导入文本</button><button @click="showAdd=true">新增题目</button></div>
    </div>
    <div v-if="showImport" class="modal"><div class="modal-content">
      <h3>导入题目</h3>
      <textarea v-model="importText" rows="15" placeholder="粘贴题目文本..."></textarea>
      <div class="modal-actions"><button @click="doImport" :disabled="importing">{{ importing?'导入中...':'导入' }}</button><button @click="showImport=false">取消</button></div>
      <p v-if="importResult">{{ importResult.imported }} 题导入成功</p>
      <ul v-if="importResult?.errors?.length"><li v-for="e in importResult.errors" :key="e">{{ e }}</li></ul>
    </div></div>
    <div v-if="showAdd" class="modal"><div class="modal-content">
      <h3>新增题目</h3>
      <select v-model="nq.type"><option value="choice_single">单选题</option><option value="choice_multi">多选题</option><option value="fill_blank">填空题</option><option value="essay">简答题</option></select>
      <input v-model="nq.question_text" placeholder="题目内容" />
      <textarea v-if="nq.type.startsWith('choice')" v-model="nq.options_raw" placeholder="每行一个选项" rows="4"></textarea>
      <input v-model="nq.answer_text" placeholder="答案" />
      <input v-model.number="nq.points" type="number" placeholder="分值" />
      <div class="modal-actions"><button @click="doAdd" :disabled="adding">{{ adding?'保存中...':'保存' }}</button><button @click="showAdd=false">取消</button></div>
    </div></div>
    <table v-if="questions.length">
      <thead><tr><th>ID</th><th>类型</th><th>题目</th><th>答案</th><th>分值</th><th>操作</th></tr></thead>
      <tbody><tr v-for="q in questions" :key="q.id"><td>{{ q.id }}</td><td>{{ typeLabel(q.type) }}</td><td>{{ trunc(q.question_text,50) }}</td><td>{{ trunc(q.answer_text,30) }}</td><td>{{ q.points }}</td><td><button class="danger" @click="doDelete(q.id)">删除</button></td></tr></tbody>
    </table>
    <p v-else>暂无题目</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
const questions = ref([])
const showImport = ref(false), showAdd = ref(false)
const importText = ref(''), importResult = ref(null), importing = ref(false), adding = ref(false)
const nq = ref({ type:'choice_single', question_text:'', options_raw:'', answer_text:'', points:5 })
const typeLabels = { choice_single:'单选', choice_multi:'多选', fill_blank:'填空', essay:'简答' }
function typeLabel(t) { return typeLabels[t]||t }
function trunc(s,n) { return s&&s.length>n ? s.slice(0,n)+'...' : s }
async function loadQuestions() { const { data } = await api.get('/questions/'); questions.value = data }
async function doImport() { importing.value=true; try { const { data } = await api.post('/questions/import',{file_text:importText.value}); importResult.value=data; await loadQuestions() } finally { importing.value=false } }
function parseOpts(raw) { return raw.split('\n').map(l=>l.replace(/^[A-Z][\.\)]\s*/,'').trim()).filter(Boolean) }
async function doAdd() { adding.value=true; try { const body={type:nq.value.type, question_text:nq.value.question_text, answer_text:nq.value.answer_text, points:nq.value.points}; if(nq.value.type.startsWith('choice')) body.options=parseOpts(nq.value.options_raw); await api.post('/questions/',body); showAdd.value=false; nq.value={type:'choice_single',question_text:'',options_raw:'',answer_text:'',points:5}; await loadQuestions() } finally { adding.value=false } }
async function doDelete(id) { if(confirm('确认删除？')){ await api.delete(`/questions/${id}`); await loadQuestions() } }
onMounted(loadQuestions)
</script>

<style scoped>
.header { display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; }
.actions { display:flex; gap:0.5rem; }
table { width:100%; border-collapse:collapse; }
th,td { padding:0.5rem; text-align:left; border-bottom:1px solid #e2e8f0; }
.modal { position:fixed; top:0;left:0;right:0;bottom:0; background:rgba(0,0,0,0.5); display:flex; justify-content:center; align-items:center; z-index:100; }
.modal-content { background:white; padding:1.5rem; border-radius:8px; width:600px; max-height:80vh; overflow-y:auto; }
.modal-content input,.modal-content textarea,.modal-content select { width:100%; padding:0.5rem; margin-bottom:0.5rem; border:1px solid #ddd; border-radius:4px; box-sizing:border-box; }
.modal-actions { display:flex; gap:0.5rem; }
.danger { background:#ef4444; color:white; }
</style>
