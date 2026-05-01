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
    setAuth(data.token, data.role, data.username)
    router.push(data.role === 'teacher' ? '/teacher' : '/student')
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container { display:flex; justify-content:center; align-items:center; min-height:100vh; background:#f5f5f5; }
.login-card { background:white; padding:2rem; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.1); width:360px; }
.login-card h1 { text-align:center; margin-bottom:1.5rem; }
.form-group { margin-bottom:1rem; }
.form-group label { display:block; margin-bottom:0.25rem; font-weight:500; }
.form-group input { width:100%; padding:0.5rem; border:1px solid #ddd; border-radius:4px; box-sizing:border-box; }
button { width:100%; padding:0.5rem; background:#3b82f6; color:white; border:none; border-radius:4px; cursor:pointer; font-size:1rem; }
button:disabled { opacity:0.6; cursor:not-allowed; }
.error { color:red; font-size:0.875rem; margin-top:0.5rem; }
</style>
