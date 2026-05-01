<template>
  <div>
    <h2>答卷查看</h2>
    <table><thead><tr><th>学生</th><th>状态</th><th>自动分</th><th>手动分</th><th>总分</th><th>提交时间</th><th>操作</th></tr></thead>
      <tbody><tr v-for="s in subs" :key="s.session_id"><td>{{ s.student_username }}</td><td>{{ s.status }}</td>
        <td>{{ s.auto_score??'-' }}</td><td>{{ s.manual_score??'-' }}</td><td>{{ s.total_score??'-' }}</td>
        <td>{{ s.submit_time?new Date(s.submit_time).toLocaleString():'-' }}</td>
        <td><button @click="viewDetail(s.session_id)">查看</button><button @click="doPub(s.session_id)" v-if="s.status!=='published'">发布</button></td></tr></tbody>
    </table>
    <div v-if="detail" class="detail">
      <h3>答卷详情</h3>
      <div v-for="a in detail.answers" :key="a.id" class="card">
        <h4>{{ a.question_text }} ({{ a.question_type }})</h4>
        <p>学生答案: {{ a.student_answer }}</p>
        <p>正确答案: {{ a.correct_answer }}</p>
        <p>结果: {{ a.is_correct===null?'待评':(a.is_correct?'正确':'错误') }}</p>
        <p>得分: {{ a.score??'未评分' }} / {{ a.points }}</p>
        <div v-if="a.question_type==='essay'" class="eg">
          <input v-model="a._score" placeholder="评分" type="number" />
          <input v-model="a._comment" placeholder="评语" />
          <button @click="doScore(a)">提交评分</button>
        </div>
      </div>
      <button @click="detail=null">关闭</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
const subs = ref([]), detail = ref(null)
async function load(){ const { data }=await api.get('/submissions'); subs.value=data }
async function viewDetail(sid){ const { data }=await api.get(`/submissions/${sid}/detail`); detail.value=data; detail.value.answers.forEach(a=>{ a._score=a.score||''; a._comment=a.teacher_comment||'' }) }
async function doScore(a){ await api.post(`/answers/${a.id}/score`,{score:parseFloat(a._score),comment:a._comment}); await viewDetail(detail.value.session.id); await load() }
async function doPub(sid){ await api.post(`/submissions/${sid}/publish`); await load() }
onMounted(load)
</script>

<style scoped>
table{width:100%;border-collapse:collapse;} th,td{padding:0.5rem;text-align:left;border-bottom:1px solid #e2e8f0;}
.detail{margin-top:1rem;padding:1rem;background:#f8fafc;border-radius:8px;}
.card{padding:1rem;background:white;margin-bottom:0.5rem;border-radius:4px;}
.eg{display:flex;gap:0.5rem;margin-top:0.5rem;} .eg input{padding:0.25rem;border:1px solid #ddd;border-radius:4px;}
</style>
