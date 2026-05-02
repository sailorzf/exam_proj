<template>
  <div>
    <div class="header">
      <h2>用户管理</h2>
      <div class="actions">
        <select v-model="roleFilter" @change="load">
          <option value="">全部角色</option>
          <option value="teacher">教师</option>
          <option value="student">学生</option>
        </select>
        <button @click="showAdd">新增用户</button>
        <button @click="downloadTemplate">下载模板</button>
        <button @click="showImport">导入用户</button>
      </div>
    </div>
    <table v-if="users.length">
      <thead><tr><th>用户名</th><th>姓名</th><th>性别</th><th>手机号</th><th>班级</th><th>角色</th><th>创建时间</th><th>操作</th></tr></thead>
      <tbody><tr v-for="u in users" :key="u.id"><td>{{ u.username }}</td><td>{{ u.name || '-' }}</td>
        <td>{{ u.gender || '-' }}</td><td>{{ u.phone || '-' }}</td><td>{{ u.class_name || '-' }}</td>
        <td><span class="role-chip" :class="'role-'+u.role">{{ u.role === 'teacher' ? '教师' : '学生' }}</span></td><td>{{ fmt(u.created_at) }}</td>
        <td><button @click="openEdit(u)">编辑</button> <button class="danger" @click="doDelete(u)">删除</button></td></tr></tbody>
    </table>
    <p v-else>暂无用户</p>

    <!-- Add/Edit Modal -->
    <div v-if="showForm" class="modal" @click.self="closeForm">
      <div class="modal-content">
        <h3>{{ editingId ? '编辑用户' : '新增用户' }}</h3>
        <div class="form-group">
          <label>用户名</label>
          <input v-model="form.username" :disabled="!!editingId" placeholder="用户名" />
        </div>
        <div class="form-group">
          <label>密码{{ editingId ? '（留空不修改）' : '' }}</label>
          <input v-model="form.password" type="password" :placeholder="editingId ? '留空不修改' : '密码'" />
        </div>
        <div class="form-group">
          <label>角色</label>
          <select v-model="form.role">
            <option value="teacher">教师</option>
            <option value="student">学生</option>
          </select>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>姓名</label>
            <input v-model="form.name" placeholder="姓名（可选）" />
          </div>
          <div class="form-group">
            <label>性别</label>
            <select v-model="form.gender">
              <option value="">未选择</option>
              <option value="男">男</option>
              <option value="女">女</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>手机号</label>
            <input v-model="form.phone" placeholder="手机号（可选）" />
          </div>
          <div class="form-group">
            <label>班级</label>
            <input v-model="form.class_name" placeholder="班级（可选）" />
          </div>
        </div>
        <div class="modal-actions">
          <button @click="doSave" :disabled="saving">{{ saving ? '保存中...' : '保存' }}</button>
          <button @click="closeForm">取消</button>
        </div>
      </div>
    </div>

    <!-- Import Modal -->
    <div v-if="showImportModal" class="modal" @click.self="showImportModal = false">
      <div class="modal-content">
        <h3>导入用户</h3>
        <p class="hint">请上传 CSV 文件，格式：username,password,role</p>
        <input type="file" accept=".csv" @change="onFileChange" />
        <div class="modal-actions">
          <button @click="doImport" :disabled="!csvFile || importing">{{ importing ? '导入中...' : '导入' }}</button>
          <button @click="showImportModal = false">取消</button>
        </div>
        <div v-if="importResult" class="result">
          <p>成功导入 {{ importResult.imported }} 个用户</p>
          <ul v-if="importResult.errors.length">
            <li v-for="e in importResult.errors" :key="e">{{ e }}</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const users = ref([])
const roleFilter = ref('')
const showForm = ref(false)
const showImportModal = ref(false)
const editingId = ref(null)
const saving = ref(false)
const importing = ref(false)
const csvFile = ref(null)
const importResult = ref(null)
const form = ref({ username: '', password: '', role: 'student', name: '', gender: '', phone: '', class_name: '' })

function fmt(d) { return d ? new Date(d+'Z').toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }) : '-' }

async function load() {
  const params = roleFilter.value ? `?role=${roleFilter.value}` : ''
  const { data } = await api.get(`/users/${params}`)
  users.value = data
}

function showAdd() {
  editingId.value = null
  form.value = { username: '', password: '', role: 'student', name: '', gender: '', phone: '', class_name: '' }
  showForm.value = true
}

function openEdit(u) {
  editingId.value = u.id
  form.value = { username: u.username, password: '', role: u.role, name: u.name || '', gender: u.gender || '', phone: u.phone || '', class_name: u.class_name || '' }
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingId.value = null
}

async function doSave() {
  if (!editingId.value && (!form.value.username || !form.value.password)) {
    alert('请填写用户名和密码')
    return
  }
  saving.value = true
  try {
    const body = { role: form.value.role }
    if (form.value.password) body.password = form.value.password
    if (form.value.name) body.name = form.value.name
    if (form.value.gender) body.gender = form.value.gender
    if (form.value.phone) body.phone = form.value.phone
    if (form.value.class_name) body.class_name = form.value.class_name
    if (!editingId.value) {
      body.username = form.value.username
      await api.post('/users/', body)
    } else {
      await api.put(`/users/${editingId.value}`, body)
    }
    closeForm()
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}

async function doDelete(u) {
  if (!confirm(`确认删除用户 "${u.username}"？`)) return
  try {
    await api.delete(`/users/${u.id}`)
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

function downloadTemplate() {
  window.open('/api/users/template', '_blank')
}

function showImport() {
  showImportModal.value = true
  csvFile.value = null
  importResult.value = null
}

function onFileChange(e) {
  csvFile.value = e.target.files[0]
}

async function doImport() {
  if (!csvFile.value) return
  importing.value = true
  try {
    const fd = new FormData()
    fd.append('file', csvFile.value)
    const { data } = await api.post('/users/import', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    importResult.value = data
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.header { display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem; flex-wrap:wrap; gap:0.75rem; }
.actions { display:flex; gap:0.75rem; align-items:center; flex-wrap:wrap; }
.actions select { padding:0.5rem 0.75rem; border:1px solid rgba(119,117,135,0.3); border-radius:0.5rem; background:#fff; min-height:44px; }
.actions button { background:#3525cd; color:#fff; border:none; padding:0.5rem 1.25rem; border-radius:0.5rem; min-height:44px; }
.actions button:hover { background:#4f46e5; }
.card { background:#fff; border:1px solid #e4e1ee; border-radius:0.75rem; box-shadow:0 1px 3px rgba(30,41,59,0.08); overflow:hidden; }
table { width:100%; border-collapse:collapse; }
th { position:sticky; top:0; background:#f0ecf9; z-index:1; font-weight:600; font-size:14px; color:#464555; padding:0.75rem 1rem; text-align:left; border-bottom:1px solid #e4e1ee; }
td { padding:0.75rem 1rem; text-align:left; border-bottom:1px solid #e4e1ee; font-size:14px; }
tbody tr:hover { background:#f5f2ff; }
.modal { position:fixed; top:0;left:0;right:0;bottom:0; background:rgba(0,0,0,0.4); display:flex; justify-content:center; align-items:center; z-index:100; backdrop-filter:blur(2px); }
.modal-content { background:#fff; padding:1.5rem; border-radius:0.75rem; width:500px; box-shadow:0 20px 60px rgba(30,41,59,0.15); max-height:80vh; overflow-y:auto; }
.modal-content h3 { margin-top:0; margin-bottom:1rem; }
.form-group { margin-bottom:1rem; }
.form-group label { display:block; margin-bottom:0.375rem; font-weight:500; font-size:14px; color:#464555; }
.form-group input,.form-group select { width:100%; padding:0.75rem; border:1px solid rgba(119,117,135,0.3); border-radius:0.5rem; box-sizing:border-box; min-height:44px; }
.form-group input:disabled { background:#f0ecf9; }
.form-row { display:flex; gap:0.75rem; }
.form-row .form-group { flex:1; }
.modal-actions { display:flex; gap:0.75rem; margin-top:0.5rem; }
.modal-actions button { min-height:44px; padding:0.5rem 1.5rem; border-radius:0.5rem; }
.modal-actions button:first-child { background:#3525cd; color:#fff; border:none; }
.modal-actions button:first-child:hover { background:#4f46e5; }
.modal-actions button:first-child:disabled { opacity:0.6; cursor:not-allowed; }
.modal-actions button:last-child { background:transparent; color:#464555; border:1px solid #c7c4d8; }
.danger { background:#ba1a1a; color:#fff; border:none; border-radius:0.5rem; padding:0.5rem 1rem; cursor:pointer; min-height:44px; }
.danger:hover { background:#dc2626; }
.hint { font-size:14px; color:#464555; margin:0.75rem 0; }
.result { margin-top:1rem; padding:1rem; background:#f5f2ff; border-radius:0.5rem; }
.result ul { margin:0.5rem 0 0; padding-left:1.25rem; }
.result li { color:#ba1a1a; font-size:14px; }
.role-chip { display:inline-block; padding:0.25rem 0.625rem; border-radius:9999px; font-size:12px; font-weight:500; }
.role-teacher { background:rgba(53,37,205,0.1); color:#3525cd; }
.role-student { background:rgba(16,185,129,0.1); color:#059669; }
</style>
