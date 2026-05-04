<template>
  <div class="login-container" :style="containerStyle">
    <div class="login-card">
      <h1>考试系统</h1>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="username" type="text" placeholder="请输入用户名" required />
        </div>
        <div class="form-group">
          <label>密码</label>
          <div class="password-wrapper">
            <input v-model="password" :type="showPassword ? 'text' : 'password'" placeholder="请输入密码" required />
            <span class="toggle-password" @click="showPassword = !showPassword">
              <svg v-if="!showPassword" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
            </span>
          </div>
        </div>
        <button type="submit" :disabled="loading">{{ loading ? '登录中...' : '登录' }}</button>
        <p v-if="error" class="error">{{ error }}</p>
      </form>
    </div>
    <div class="copyright">{{ copyrightText }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { setAuth } from '../auth'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)
const backgroundImage = ref('')
const copyrightText = ref('')

const containerStyle = computed(() => {
  if (backgroundImage.value) {
    return {
      backgroundImage: `url('${backgroundImage.value}')`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
    }
  }
  return {}
})

onMounted(async () => {
  try {
    const { data } = await api.get('/settings/')
    if (data.background_image) backgroundImage.value = data.background_image
    if (data.copyright_text) copyrightText.value = data.copyright_text
  } catch {
    // use defaults
  }
})

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
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #fcf8ff;
  position: relative;
  flex-direction: column;
}
.login-container::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  z-index: 0;
}
.login-card {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  padding: 2.5rem;
  border-radius: 0.75rem;
  box-shadow: 0 4px 20px rgba(53, 37, 205, 0.1);
  width: 400px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}
.login-card h1 { text-align: center; margin-bottom: 2rem; color: #3525cd; font-size: 28px; }
.form-group { margin-bottom: 1.25rem; }
.form-group label { display: block; margin-bottom: 0.375rem; font-weight: 500; font-size: 14px; color: #464555; }
.form-group input { width: 100%; padding: 0.75rem; border: 1px solid rgba(119,117,135,0.3); border-radius: 0.5rem; box-sizing: border-box; min-height: 44px; }
.password-wrapper { position: relative; display: flex; align-items: center; }
.password-wrapper input { padding-right: 2.75rem; }
.toggle-password { position: absolute; right: 0.75rem; cursor: pointer; color: #777587; display: flex; align-items: center; transition: color 0.15s; }
.toggle-password:hover { color: #3525cd; }
.form-group input:focus { border-color: #3525cd; box-shadow: 0 0 0 3px rgba(53, 37, 205, 0.1); outline: none; }
button { width: 100%; padding: 0.75rem; background: #3525cd; color: #fff; border: none; border-radius: 0.5rem; cursor: pointer; font-size: 16px; font-weight: 500; min-height: 44px; transition: background 0.15s; }
button:hover { background: #4f46e5; }
button:disabled { opacity: 0.6; cursor: not-allowed; }
.error { color: #ba1a1a; font-size: 14px; margin-top: 0.75rem; text-align: center; }
.copyright {
  position: relative;
  z-index: 1;
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  margin-top: 1.5rem;
  text-align: center;
}
</style>
