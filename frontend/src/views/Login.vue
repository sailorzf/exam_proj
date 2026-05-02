<template>
  <div class="login-container">
    <div class="login-card">
      <h1>考试系统</h1>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="username" type="text" placeholder="请输入用户名" required />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="password" type="password" placeholder="请输入密码" required />
        </div>
        <button type="submit" :disabled="loading">{{ loading ? '登录中...' : '登录' }}</button>
        <p v-if="error" class="error">{{ error }}</p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { setAuth } from '../auth'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.post('/login', { username: username.value, password: password.value })
    setAuth(data.token, data.role, data.username, data.is_admin)
    router.push(data.role === 'teacher' ? '/teacher' : '/student')
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container { display:flex; justify-content:center; align-items:center; min-height:100vh; background:#fcf8ff; }
.login-card { background:#fff; padding:2.5rem; border-radius:0.75rem; box-shadow:0 4px 20px rgba(53,37,205,0.1); width:400px; border:1px solid #e4e1ee; }
.login-card h1 { text-align:center; margin-bottom:2rem; color:#3525cd; font-size:28px; }
.form-group { margin-bottom:1.25rem; }
.form-group label { display:block; margin-bottom:0.375rem; font-weight:500; font-size:14px; color:#464555; }
.form-group input { width:100%; padding:0.75rem; border:1px solid rgba(119,117,135,0.3); border-radius:0.5rem; box-sizing:border-box; min-height:44px; }
.form-group input:focus { border-color:#3525cd; box-shadow:0 0 0 3px rgba(53,37,205,0.1); outline:none; }
button { width:100%; padding:0.75rem; background:#3525cd; color:#fff; border:none; border-radius:0.5rem; cursor:pointer; font-size:16px; font-weight:500; min-height:44px; transition:background 0.15s; }
button:hover { background:#4f46e5; }
button:disabled { opacity:0.6; cursor:not-allowed; }
.error { color:#ba1a1a; font-size:14px; margin-top:0.75rem; text-align:center; }
</style>
