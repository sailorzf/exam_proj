<template>
  <div v-if="detail">
    <div class="header">
      <div>
        <router-link to="/teacher/submissions" class="back">← 返回列表</router-link>
        <h3>阅卷: {{ paperTitle }} - {{ studentName }}</h3>
      </div>
      <div class="scores">
        <span>客观题分: {{ displayAuto }}</span>
        <span>主观题分: {{ displayManual }}</span>
        <span>总分: {{ displayTotal }}</span>
        <button @click="doPub">成绩发布</button>
      </div>
    </div>
    <div class="filter-bar">
      <label>题目筛选：</label>
      <select v-model="filterType">
        <option value="">全部</option>
        <option value="objective">客观题</option>
        <option value="essay">主观题</option>
      </select>
    </div>
    <div v-for="a in filteredAnswers" :key="a.id" class="card">
      <h4>{{ a.question_text }}</h4>
      <p>类型: {{ statusMap[a.question_type]||a.question_type }} | 满分: {{ a.points }}</p>
      <p>学生答案: <span class="answer">{{ a.student_answer||'(未作答)' }}</span></p>
      <p v-if="a.question_type!=='essay'">正确答案: {{ a.correct_answer }}</p>
      <p v-if="a.question_type!=='essay'">结果: {{ a.is_correct===null?'待评':(a.is_correct?'正确':'错误') }} | 得分: {{ a.score??0 }} / {{ a.points }}</p>
      <div v-if="a.question_type==='essay'" class="score-row">
        <label>得分:</label>
        <input v-model.number="a._score" type="number" :max="a.points" :min="0" step="0.5" />
        <span>/ {{ a.points }}</span>
        <button @click="doScore(a)" :disabled="a._score===''">提交</button>
        <input v-model="a._comment" placeholder="评语（可选）" />
        <span v-if="a.teacher_comment" class="comment">评语: {{ a.teacher_comment }}</span>
      </div>
      <p v-if="a.question_type==='essay'" class="current-score">当前得分: {{ a.score??'未评分' }} / {{ a.points }}</p>
    </div>
  </div>
  <div v-else class="loading">加载中...</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../api'

const route = useRoute()
const sessionId = parseInt(route.params.id)
const detail = ref(null)
const papers = ref([])
const filterType = ref('')
const statusMap = { choice_single:'单选', choice_multi:'多选', fill_blank:'填空', essay:'简答' }
const objectiveTypes = new Set(['choice_single', 'choice_multi', 'fill_blank'])

const paperTitle = computed(() => {
  if (!detail.value) return ''
  const p = papers.value.find(p => p.id === detail.value.session.paper_id)
  return p ? p.title : `试卷${detail.value.session.paper_id}`
})
const studentName = computed(() => detail.value?.answers?.[0]?.student_username || '未知学生')
const displayAuto = computed(() => detail.value?.session?.auto_score ?? 0)
const displayManual = computed(() => detail.value?.session?.manual_score ?? 0)
const displayTotal = computed(() => displayAuto.value + displayManual.value)

const filteredAnswers = computed(() => {
  if (!detail.value) return []
  const answers = detail.value.answers || []
  if (filterType.value === 'essay') return answers.filter(a => a.question_type === 'essay')
  if (filterType.value === 'objective') return answers.filter(a => objectiveTypes.has(a.question_type))
  return answers
})

async function load(){
  const { data } = await api.get(`/submissions/${sessionId}/detail`)
  detail.value = data
  detail.value.answers.forEach(a => {
    a._score = a.score ?? ''
    a._comment = a.teacher_comment || ''
  })
  // fetch student name from submissions list
  const { data: subs } = await api.get('/submissions')
  const sub = subs.find(s => s.session_id === sessionId)
  if (sub) detail.value.answers.forEach(a => { a.student_username = sub.student_username })
}

async function loadPapers(){ const { data }=await api.get('/papers/'); papers.value=data }

async function doScore(a){
  await api.post(`/answers/${a.id}/score`, { score: parseFloat(a._score), comment: a._comment })
  await load()
}

async function doPub(){
  try {
    await api.post(`/submissions/${sessionId}/publish`)
    alert('成绩发布成功')
    await load()
  } catch(e) {
    alert('发布失败: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(()=>{ load(); loadPapers() })
</script>

<style scoped>
.header{display:flex;justify-content:space-between;align-items:center;padding:0.75rem 1rem;background:#f8fafc;border-radius:8px;margin-bottom:1rem;}
.back{color:#3b82f6;text-decoration:none;margin-right:1rem;} .header h3{display:inline;margin:0;}
.scores{display:flex;gap:1rem;align-items:center;} .scores button{padding:0.5rem 1rem;background:#10b981;color:white;border:none;border-radius:4px;cursor:pointer;}
.filter-bar{margin-bottom:1rem;display:flex;align-items:center;gap:0.5rem;}
.filter-bar select{padding:0.25rem 0.5rem;border:1px solid #ddd;border-radius:4px;}
.card{padding:1rem;background:white;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:0.75rem;}
.card h4{margin:0 0 0.5rem;} .card p{margin:0.25rem 0;color:#475569;}
.answer{font-weight:500;}
.score-row{display:flex;gap:0.5rem;align-items:center;margin-top:0.5rem;}
.score-row input[type="number"]{width:60px;padding:0.25rem;border:1px solid #ddd;border-radius:4px;}
.score-row input[type="text"]{flex:1;padding:0.25rem;border:1px solid #ddd;border-radius:4px;}
.score-row button{padding:0.25rem 0.75rem;background:#3b82f6;color:white;border:none;border-radius:4px;cursor:pointer;}
.comment{color:#64748b;font-size:0.875rem;}
.current-score{font-weight:bold;color:#10b981;margin-top:0.25rem;}
.loading{text-align:center;padding:2rem;}
</style>
