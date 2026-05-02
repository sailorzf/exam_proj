<template>
  <div>
    <h2>个人设置</h2>
    <div class="card">
      <div class="form-row">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="profile.username" disabled />
        </div>
        <div class="form-group">
          <label>角色</label>
          <input :value="roleLabel" disabled />
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>姓名</label>
          <input v-model="profile.name" placeholder="如：张三" />
        </div>
        <div class="form-group">
          <label>性别</label>
          <select v-model="profile.gender">
            <option value="">未设置</option>
            <option value="男">男</option>
            <option value="女">女</option>
          </select>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>手机号</label>
          <input v-model="profile.phone" placeholder="如：13800000000" />
        </div>
        <div class="form-group" v-if="profile.role === 'student'">
          <label>班级</label>
          <input v-model="profile.class_name" placeholder="如：一班" />
        </div>
      </div>
      <div class="form-actions">
        <button @click="saveProfile" :disabled="saving">{{ saving ? '保存中...' : '保存信息' }}</button>
      </div>
    </div>

    <div class="card password-section">
      <h3 @click="showPassword = !showPassword" class="toggle-header">
        <span class="chevron" :class="{ open: showPassword }">▶</span>
        修改密码
      </h3>
      <div v-if="showPassword">
        <div class="form-group">
          <label>旧密码</label>
          <input v-model="pw.old" type="password" placeholder="请输入当前密码" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>新密码</label>
            <input v-model="pw.new" type="password" placeholder="请输入新密码" />
          </div>
          <div class="form-group">
            <label>确认新密码</label>
            <input v-model="pw.confirm" type="password" placeholder="请再次输入新密码" />
          </div>
        </div>
        <div class="form-actions">
          <button @click="changePassword" :disabled="saving">{{ saving ? '修改中...' : '修改密码' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'
import { clearAuth, getRole } from '../../auth'

const router = useRouter()
const profile = ref({ username: '', role: '', name: '', gender: '', phone: '', class_name: '' })
const pw = ref({ old: '', new: '', confirm: '' })
const showPassword = ref(false)
const saving = ref(false)
const roleLabel = computed(() => profile.value.role === 'teacher' ? '教师' : profile.value.role === 'student' ? '学生' : profile.value.role)

async function load() {
  const { data } = await api.get('/users/profile')
  profile.value = data
}

async function saveProfile() {
  saving.value = true
  try {
    await api.put('/users/profile', {
      name: profile.value.name || null,
      gender: profile.value.gender || null,
      phone: profile.value.phone || null,
      class_name: profile.value.class_name || null,
    })
    alert('保存成功')
  } catch (e) {
    alert(e.response?.data?.detail || '保存失败')
  } finally { saving.value = false }
}

async function changePassword() {
  if (!pw.value.old) { alert('请输入旧密码'); return }
  if (!pw.value.new) { alert('请输入新密码'); return }
  if (pw.value.new !== pw.value.confirm) { alert('两次输入的新密码不一致'); return }
  saving.value = true
  try {
    await api.put('/users/profile', { old_password: pw.value.old, password: pw.value.new })
    alert('密码修改成功，请重新登录')
    clearAuth()
    router.push('/login')
  } catch (e) {
    alert(e.response?.data?.detail || '修改失败')
  } finally { saving.value = false }
}

onMounted(load)
</script>

<style scoped>
.card { background:#fff; border:1px solid #e4e1ee; border-radius:0.75rem; box-shadow:0 1px 3px rgba(30,41,59,0.08); padding:1.5rem; margin-bottom:1.5rem; }
.password-section { margin-top:1rem; }
.toggle-header { margin:0; cursor:pointer; display:flex; align-items:center; gap:0.5rem; user-select:none; }
.toggle-header:hover { color:#3525cd; }
.chevron { transition:transform 0.2s; font-size:12px; }
.chevron.open { transform:rotate(90deg); }
.form-group { margin-bottom:1rem; }
.form-group label { display:block; margin-bottom:0.375rem; font-weight:500; font-size:14px; color:#464555; }
.form-group input, .form-group select { width:100%; padding:0.75rem; border:1px solid rgba(119,117,135,0.3); border-radius:0.5rem; box-sizing:border-box; min-height:44px; }
.form-group input:disabled { background:#f0ecf9; color:#464555; }
.form-row { display:flex; gap:1rem; }
.form-row .form-group { flex:1; }
.form-actions { display:flex; gap:0.75rem; margin-top:0.5rem; }
.form-actions button { min-height:44px; padding:0.5rem 1.5rem; border-radius:0.5rem; background:#3525cd; color:#fff; border:none; cursor:pointer; font-weight:500; }
.form-actions button:hover:not(:disabled) { background:#4f46e5; }
.form-actions button:disabled { opacity:0.6; cursor:not-allowed; }
</style>
