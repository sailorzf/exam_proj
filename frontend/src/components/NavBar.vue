<template>
  <div>
    <nav class="navbar">
      <span class="brand">考试系统</span>
      <div class="nav-links" v-if="isTeacher">
        <router-link to="/teacher/questions">题库</router-link>
        <router-link to="/teacher/papers">试卷</router-link>
        <router-link to="/teacher/exams">发布</router-link>
        <router-link to="/teacher/submissions">答卷</router-link>
        <router-link to="/teacher/grades">成绩</router-link>
      </div>
      <div class="nav-links" v-else-if="isStudent">
        <router-link to="/student/exams">考试</router-link>
        <router-link to="/student/results">成绩</router-link>
      </div>
      <div class="nav-right">
        <span class="user">{{ username }}</span>
        <button @click="handleLogout">退出</button>
      </div>
    </nav>
    <div class="content"><router-view /></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { getUsername, isTeacher, isStudent, clearAuth } from '../auth'

const router = useRouter()
const username = computed(getUsername)
function handleLogout() { clearAuth(); router.push('/login') }
</script>

<style scoped>
.navbar { display:flex; align-items:center; gap:1rem; padding:0.75rem 1.5rem; background:#1e293b; color:white; }
.brand { font-weight:bold; margin-right:1rem; }
.nav-links { display:flex; gap:0.75rem; }
.nav-links a { color:#cbd5e1; text-decoration:none; padding:0.25rem 0.5rem; border-radius:4px; }
.nav-links a.router-link-active { color:white; background:#334155; }
.nav-right { margin-left:auto; display:flex; align-items:center; gap:0.75rem; }
.nav-right button { padding:0.25rem 0.75rem; background:transparent; color:#cbd5e1; border:1px solid #475569; border-radius:4px; cursor:pointer; }
.content { padding:1.5rem; }
</style>
