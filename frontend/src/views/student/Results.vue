<template>
  <div>
    <h2>我的成绩</h2>
    <div v-if="detail" class="detail">
      <h3>考试成绩</h3>
      <p>总分: <strong>{{ detail.session?.total_score }}</strong></p>
      <div v-for="a in detail.answers" :key="a.id" class="card">
        <h4>{{ a.question_text }}</h4>
        <p>你的答案: {{ a.student_answer }}</p>
        <p>正确答案: {{ a.correct_answer }}</p>
        <p>结果: {{ a.is_correct===null?'已评分':(a.is_correct?'正确':'错误') }}</p>
        <p>得分: {{ a.score }} / {{ a.points }}</p>
        <p v-if="a.teacher_comment">评语: {{ a.teacher_comment }}</p>
      </div>
      <button @click="detail=null">返回</button>
    </div>
    <table v-else><thead><tr><th>试卷</th><th>总分</th><th>状态</th><th>操作</th></tr></thead>
      <tbody><tr v-for="r in results" :key="r.session_id"><td>{{ r.paper_title }}</td><td>{{ r.total_score??'评分中' }}</td>
        <td>{{ r.status }}</td><td><button @click="view(r.session_id)">查看</button></td></tr></tbody>
    </table>
    <p v-if="!results.length">暂无成绩</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
const results = ref([]), detail = ref(null)
async function load(){ const { data }=await api.get('/results'); results.value=data }
async function view(sid){ const { data }=await api.get(`/results/${sid}`); detail.value=data }
onMounted(load)
</script>

<style scoped>
table{width:100%;border-collapse:collapse;} th,td{padding:0.5rem;text-align:left;border-bottom:1px solid #e2e8f0;}
.detail{padding:1rem;} .card{padding:1rem;background:#f8fafc;margin-bottom:0.5rem;border-radius:4px;}
</style>
