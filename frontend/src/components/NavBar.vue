<template>
  <div>
    <nav class="navbar">
      <span class="brand">考试系统</span>
      <div class="nav-links" v-if="isTeacher">
        <router-link to="/teacher/questions">题库</router-link>
        <router-link to="/teacher/papers">试卷</router-link>
        <router-link to="/teacher/exams">发布</router-link>
        <router-link to="/teacher/submissions">阅卷</router-link>
        <router-link to="/teacher/grades">成绩</router-link>
        <router-link v-if="isAdmin" to="/teacher/admin">管理</router-link>
      </div>
      <div class="nav-links" v-else-if="isStudent">
        <router-link to="/student/exams">考试</router-link>
        <router-link to="/student/results">成绩</router-link>
      </div>
      <div class="nav-right">
        <router-link :to="`/${role}/profile`" class="user">{{ username }}</router-link>
        <button @click="handleLogout">退出</button>
      </div>
    </nav>
    <div class="content"><router-view /></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { getUsername, getRole, clearAuth } from '../auth'

const router = useRouter()
const username = computed(getUsername)
const role = computed(getRole)
const isTeacher = computed(() => role.value === 'teacher')
const isStudent = computed(() => role.value === 'student')
const isAdmin = computed(() => {
  try { return JSON.parse(localStorage.getItem('exam_is_admin') || 'false') } catch { return false }
})
function handleLogout() { clearAuth(); router.push('/login') }
</script>

<style scoped>
.navbar { display:flex; align-items:center; gap:1rem; padding:0.75rem 1.5rem; background:#3525cd; color:#fff; box-shadow:0 2px 8px rgba(53,37,205,0.2); }
.brand { font-weight:700; font-size:18px; margin-right:1rem; letter-spacing:-0.01em; }
.nav-links { display:flex; gap:0.25rem; }
.nav-links a { color:rgba(255,255,255,0.8); text-decoration:none; padding:0.5rem 0.75rem; border-radius:0.5rem; font-size:14px; font-weight:500; transition:all 0.15s; min-height:44px; display:flex; align-items:center; }
.nav-links a:hover { color:#fff; background:rgba(255,255,255,0.1); }
.nav-links a.router-link-active { color:#fff; background:rgba(255,255,255,0.15); }
.nav-right { margin-left:auto; display:flex; align-items:center; gap:1rem; }
.nav-right .user { font-size:14px; color:rgba(255,255,255,0.9); text-decoration:none; cursor:pointer; transition:color 0.15s; }
.nav-right .user:hover { color:#fff; text-decoration:underline; }
.nav-right button { padding:0.5rem 1rem; background:rgba(255,255,255,0.15); color:#fff; border:1px solid rgba(255,255,255,0.3); border-radius:0.5rem; cursor:pointer; font-size:14px; font-weight:500; min-height:44px; transition:all 0.15s; }
.nav-right button:hover { background:rgba(255,255,255,0.25); }
.content { padding:1.5rem; max-width:1280px; margin:0 auto; }
</style>
