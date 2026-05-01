<template>
  <div>
    <h2>成绩列表</h2>
    <table><thead><tr><th>学生</th><th>自动分</th><th>手动分</th><th>总分</th><th>状态</th><th>提交时间</th></tr></thead>
      <tbody><tr v-for="s in subs" :key="s.session_id"><td>{{ s.student_username }}</td><td>{{ s.auto_score??'-' }}</td><td>{{ s.manual_score??'-' }}</td>
        <td><strong>{{ s.total_score??'-' }}</strong></td><td>{{ s.status }}</td><td>{{ s.submit_time?new Date(s.submit_time).toLocaleString():'-' }}</td></tr></tbody>
    </table>
    <p v-if="!subs.length">暂无答卷</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
const subs = ref([])
async function load(){ const { data }=await api.get('/submissions'); subs.value=data }
onMounted(load)
</script>

<style scoped>
table{width:100%;border-collapse:collapse;} th,td{padding:0.5rem;text-align:left;border-bottom:1px solid #e2e8f0;}
</style>
