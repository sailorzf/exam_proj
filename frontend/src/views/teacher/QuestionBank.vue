<template>
  <div>
    <div class="header">
      <h2>题库管理</h2>
    </div>
    <div class="tabs">
      <button :class="{active: activeTab==='questions'}" @click="activeTab='questions'">题库管理</button>
      <button :class="{active: activeTab==='categories'}" @click="activeTab='categories'">科目管理</button>
    </div>

    <!-- 科目管理 -->
    <div v-if="activeTab==='categories'" class="section">
      <div class="section-header">
        <h3>科目列表</h3>
        <button @click="showCatAdd=true">新增科目</button>
      </div>
      <table v-if="categoryList.length">
        <thead><tr><th>科目名称</th><th>题目数量</th><th>创建时间</th><th>操作</th></tr></thead>
        <tbody><tr v-for="c in categoryList" :key="c.id"><td>{{ c.name }}</td><td>{{ c.count }}</td>
          <td>{{ fmtDate(c.created_at) }}</td>
          <td><button @click="openCatEdit(c)">编辑</button> <button class="danger" @click="doDeleteCategory(c.name)">删除</button></td></tr></tbody>
      </table>
      <p v-else>暂无科目</p>
      <div v-if="showCatAdd" class="modal"><div class="modal-content modal-sm">
        <h3>{{ editingCat ? '编辑科目' : '新增科目' }}</h3>
        <input v-model="catName" placeholder="科目名称，如：物理" />
        <div class="modal-actions">
          <button @click="doSaveCategory" :disabled="saving">{{ saving?'保存中...':'保存' }}</button>
          <button @click="cancelCatEdit">取消</button>
        </div>
      </div></div>
    </div>

    <!-- 题库管理 -->
    <div v-if="activeTab==='questions'" class="section">
      <div class="actions">
        <select v-model="categoryFilter" @change="load">
          <option value="">全部分类</option>
          <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
        </select>
        <button @click="showImport=true">导入</button>
        <button @click="showAdd=true">新增</button>
      </div>
    <div v-if="showImport" class="modal"><div class="modal-content">
      <h3>导入题目</h3>
      <div class="form-group">
        <label>科目分类</label>
        <input v-model="importCategory" placeholder="如：物理、数学" list="cat-suggestions-import" />
        <datalist id="cat-suggestions-import"><option v-for="c in categories" :key="c" :value="c"></option></datalist>
      </div>
      <textarea v-model="importText" rows="12" placeholder="粘贴题目文本..."></textarea>
      <div class="modal-actions">
        <button @click="doImport" :disabled="importing">{{ importing?'导入中...':'导入' }}</button>
        <button @click="showImport=false">取消</button>
      </div>
      <p v-if="importResult">{{ importResult.imported }} 题导入成功</p>
      <ul v-if="importResult?.errors?.length"><li v-for="e in importResult.errors" :key="e">{{ e }}</li></ul>
    </div></div>
    <div v-if="showAdd" class="modal"><div class="modal-content">
      <h3>{{ editingId ? '编辑题目' : '新增题目' }}</h3>
      <select v-model="nq.type">
        <option value="choice_single">单选题</option><option value="choice_multi">多选题</option>
        <option value="fill_blank">填空题</option><option value="essay">简答题</option>
      </select>
      <div class="form-row">
        <div class="form-group">
          <label>科目分类</label>
          <input v-model="nq.category" placeholder="如：物理" list="cat-suggestions" />
          <datalist id="cat-suggestions"><option v-for="c in categories" :key="c" :value="c"></option></datalist>
        </div>
        <div class="form-group">
          <label>分值</label>
          <input v-model.number="nq.points" type="number" min="1" />
        </div>
      </div>
      <input v-model="nq.question_text" placeholder="题目内容" />
      <textarea v-if="nq.type.startsWith('choice')" v-model="nq.options_raw" placeholder="每行一个选项" rows="4"></textarea>
      <input v-model="nq.answer_text" placeholder="答案" />
      <div class="modal-actions">
        <button @click="doSave" :disabled="saving">{{ saving?'保存中...':'保存' }}</button>
        <button @click="cancelEdit">取消</button>
      </div>
    </div></div>
    <table v-if="questions.length">
      <thead><tr><th>分类</th><th>类型</th><th>题目</th><th>答案</th><th>分值</th><th>操作</th></tr></thead>
      <tbody><tr v-for="q in questions" :key="q.id"><td>{{ q.category || '-' }}</td><td>{{ typeLabel(q.type) }}</td>
        <td>{{ trunc(q.question_text,50) }}</td><td>{{ trunc(q.answer_text,30) }}</td><td>{{ q.points }}</td>
        <td><button @click="openEdit(q)">编辑</button> <button class="danger" @click="doDelete(q.id)">删除</button></td></tr></tbody>
    </table>
    <p v-else>暂无题目</p>
    <div v-if="totalPages > 1" class="pagination">
      <button :disabled="page===1" @click="page=1">首页</button>
      <button :disabled="page===1" @click="page--">上一页</button>
      <span class="page-info">第 {{ page }} / {{ totalPages }} 页 (共 {{ total }} 题)</span>
      <button :disabled="page===totalPages" @click="page++">下一页</button>
      <button :disabled="page===totalPages" @click="page=totalPages">末页</button>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '../../api'
const questions = ref([])
const categories = ref([])
const categoryFilter = ref('')
const page = ref(1)
const limit = 20
const total = ref(0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / limit)))
const showImport = ref(false), showAdd = ref(false)
const importText = ref(''), importCategory = ref(''), importResult = ref(null), importing = ref(false), saving = ref(false)
const editingId = ref(null)
const nq = ref({ type:'choice_single', category:'', question_text:'', options_raw:'', answer_text:'', points:5 })
const typeLabels = { choice_single:'单选', choice_multi:'多选', fill_blank:'填空', essay:'简答' }
function typeLabel(t) { return typeLabels[t]||t }
function trunc(s,n) { return s&&s.length>n ? s.slice(0,n)+'...' : s }
function fmtDate(d) { if (!d) return '-'; return new Date(d+'Z').toLocaleString('zh-CN', {timeZone:'Asia/Shanghai', year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit'}) }

// Tab management
const activeTab = ref('questions')

// Category management
const categoryList = ref([])
const showCatAdd = ref(false)
const editingCat = ref(null)
const catName = ref('')

async function loadCategories(){
  const { data } = await api.get('/questions/categories')
  categoryList.value = data
  // Also update the simple name list for datalist suggestions
  categories.value = data.map(c => c.name)
}

function openCatEdit(c) {
  editingCat.value = c.name
  catName.value = c.name
  showCatAdd.value = true
}

function cancelCatEdit() {
  editingCat.value = null
  showCatAdd.value = false
  catName.value = ''
}

async function doSaveCategory() {
  if (!catName.value.trim()) { alert('请输入科目名称'); return }
  // Check duplicate
  if (categoryList.value.some(c => c.name === catName.value.trim() && c.name !== editingCat.value)) {
    alert('该科目已存在'); return
  }
  saving.value = true
  try {
    if (editingCat.value) {
      // Update: rename category for all questions
      await api.put(`/questions/category/${encodeURIComponent(editingCat.value)}`, { name: catName.value.trim() })
    } else {
      await api.post('/questions/category', { name: catName.value.trim() })
    }
    cancelCatEdit()
    await loadCategories()
  } catch (e) {
    alert(e.response?.data?.detail || '操作失败')
  } finally { saving.value = false }
}

async function doDeleteCategory(name) {
  // Check if category has questions
  const cat = categoryList.value.find(c => c.name === name)
  if (cat && cat.count > 0) {
    if (!confirm(`科目"${name}"下有${cat.count}道题目，删除科目将同时删除所有题目，确认？`)) return
  } else {
    if (!confirm(`确认删除科目"${name}"？`)) return
  }
  try {
    await api.delete(`/questions/category/${encodeURIComponent(name)}`)
    await loadCategories()
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || '删除失败')
  }
}
async function load(){
  if (activeTab.value !== 'questions') return
  const params = `?page=${page.value}&limit=${limit}${categoryFilter.value?'&category='+encodeURIComponent(categoryFilter.value):''}`
  const { data } = await api.get(`/questions/${params}`)
  questions.value = data.items
  total.value = data.total
}
async function doImport(){
  importing.value=true; importResult.value=null
  try {
    const { data } = await api.post('/questions/import', { file_text: importText.value, category: importCategory.value || null })
    importResult.value = data
    await load()
    if (data.imported > 0 && importCategory.value) await loadCategories()
  } finally { importing.value = false }
}
function parseOpts(raw) { return raw.split('\n').map(l=>l.replace(/^[A-Z][\.\)]\s*/,'').trim()).filter(Boolean) }
function parseOptsFromQuestion(q) { if (q.options && Array.isArray(q.options)) return q.options.join('\n'); return '' }
function openEdit(q) {
  editingId.value = q.id
  nq.value = { type: q.type, category: q.category || '', question_text: q.question_text, options_raw: parseOptsFromQuestion(q), answer_text: q.answer_text, points: q.points }
  showAdd.value = true
}
function cancelEdit() {
  editingId.value = null
  showAdd.value = false
  nq.value = { type:'choice_single', category:'', question_text:'', options_raw:'', answer_text:'', points:5 }
}
async function doSave() {
  if (!nq.value.category) { alert('请指定科目分类'); return }
  saving.value = true
  try {
    const body = { type: nq.value.type, category: nq.value.category, question_text: nq.value.question_text, answer_text: nq.value.answer_text, points: nq.value.points }
    if (nq.value.type.startsWith('choice')) body.options = parseOpts(nq.value.options_raw)
    if (editingId.value) {
      await api.put(`/questions/${editingId.value}`, body)
    } else {
      await api.post('/questions/', body)
    }
    cancelEdit()
    await load()
    await loadCategories()
  } catch (e) {
    alert(e.response?.data?.detail || '操作失败')
  } finally { saving.value = false }
}
async function doDelete(id) {
  if (!confirm('确认删除？')) return
  try { await api.delete(`/questions/${id}`); await load(); await loadCategories() }
  catch (e) { alert(e.response?.data?.detail || '删除失败') }
}
watch(activeTab, (tab) => {
  if (tab === 'questions') load()
  if (tab === 'categories') loadCategories()
})
watch(page, load)
onMounted(() => { load(); loadCategories() })
</script>

<style scoped>
.header { display:flex; justify-content:space-between; align-items:center; margin-bottom: 1rem; }
.header h2 { margin:0; }
.tabs { display:flex; gap:0; border-bottom:2px solid #e4e1ee; margin-bottom:1.5rem; }
.tabs button { padding:0.75rem 1.5rem; border:none; background:none; cursor:pointer; font-size:14px; font-weight:500; color:#464555; border-bottom:2px solid transparent; margin-bottom:-2px; transition:all 0.15s; border-radius:0.5rem 0.5rem 0 0; min-height:44px; }
.tabs button.active { color:#3525cd; border-bottom-color:#3525cd; font-weight:600; background:#f0ecf9; }
.tabs button:hover:not(.active) { color:#1b1b24; background:#f5f2ff; }
.section { min-height:200px; }
.section-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; }
.section-header h3 { margin:0; }
.actions { display:flex; gap:0.75rem; align-items:center; flex-wrap:wrap; }
.actions select { padding:0.5rem 0.75rem; border:1px solid rgba(119,117,135,0.3); border-radius:0.5rem; background:#fff; min-height:44px; }
.actions button { background:#3525cd; color:#fff; border:none; padding:0.5rem 1.25rem; border-radius:0.5rem; min-height:44px; }
.actions button:hover { background:#4f46e5; }
.card { background:#ffffff; border:1px solid #e4e1ee; border-radius:0.75rem; box-shadow:0 1px 3px rgba(30,41,59,0.08); }
table { width:100%; border-collapse:collapse; }
th { position:sticky; top:0; background:#f0ecf9; z-index:1; font-weight:600; font-size:14px; color:#464555; padding:0.75rem 1rem; text-align:left; border-bottom:1px solid #e4e1ee; }
td { padding:0.75rem 1rem; text-align:left; border-bottom:1px solid #e4e1ee; font-size:14px; }
tbody tr:hover { background:#f5f2ff; }
.modal { position:fixed; top:0;left:0;right:0;bottom:0; background:rgba(0,0,0,0.4); display:flex; justify-content:center; align-items:center; z-index:100; backdrop-filter:blur(2px); }
.modal-content { background:#ffffff; padding:1.5rem; border-radius:0.75rem; width:600px; max-height:80vh; overflow-y:auto; box-shadow:0 20px 60px rgba(30,41,59,0.15); }
.modal-sm { width:400px; }
.modal-content h3 { margin-top:0; margin-bottom:1rem; }
.modal-content input,.modal-content textarea,.modal-content select { width:100%; padding:0.75rem; margin-bottom:0.75rem; border:1px solid rgba(119,117,135,0.3); border-radius:0.5rem; box-sizing:border-box; background:#fff; }
.modal-content input:focus,.modal-content textarea:focus,.modal-content select:focus { border-color:#3525cd; box-shadow:0 0 0 3px rgba(53,37,205,0.1); outline:none; }
.modal-actions { display:flex; gap:0.75rem; margin-top:0.5rem; }
.modal-actions button { min-height:44px; padding:0.5rem 1.5rem; border-radius:0.5rem; }
.modal-actions button:first-child { background:#3525cd; color:#fff; border:none; }
.modal-actions button:first-child:hover { background:#4f46e5; }
.modal-actions button:first-child:disabled { opacity:0.6; cursor:not-allowed; }
.modal-actions button:last-child { background:transparent; color:#464555; border:1px solid #c7c4d8; }
.danger { background:#ba1a1a; color:#fff; border:none; border-radius:0.5rem; padding:0.5rem 1rem; cursor:pointer; min-height:44px; }
.danger:hover { background:#dc2626; }
.form-group { margin-bottom:1rem; }
.form-group label { display:block; margin-bottom:0.375rem; font-size:14px; font-weight:500; color:#464555; }
.form-row { display:flex; gap:0.75rem; }
.form-row .form-group { flex:1; }
.pagination { display:flex; justify-content:center; align-items:center; gap:0.5rem; margin-top:1.5rem; padding:1rem 0; }
.pagination button { padding:0.5rem 1rem; border:1px solid #c7c4d8; border-radius:0.5rem; background:#fff; cursor:pointer; min-height:44px; color:#464555; transition:all 0.15s; }
.pagination button:hover:not(:disabled) { border-color:#3525cd; color:#3525cd; }
.pagination button:disabled { opacity:0.4; cursor:not-allowed; }
.page-info { font-size:14px; color:#464555; }
.chip { display:inline-block; padding:0.25rem 0.75rem; border-radius:9999px; font-size:12px; font-weight:500; }
.chip-primary { background:rgba(53,37,205,0.1); color:#3525cd; }
.chip-success { background:rgba(16,185,129,0.1); color:#059669; }
</style>
