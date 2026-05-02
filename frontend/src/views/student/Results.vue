<template>
  <div>
    <h2>我的成绩</h2>
    <div v-if="detail" class="detail">
      <div class="header">
        <div>
          <button @click="detail=null" class="back">← 返回列表</button>
          <h3>{{ paperTitle }} - 答卷详情</h3>
        </div>
        <div class="scores">
          <span class="score-item">客观题分: <strong>{{ session.auto_score ?? 0 }}</strong></span>
          <span class="score-item">主观题分: <strong>{{ session.manual_score ?? 0 }}</strong></span>
          <span class="score-item total">总分: <strong>{{ session.total_score ?? '评分中' }}</strong></span>
        </div>
      </div>
      <div class="filter-bar">
        <button :class="{active: filterType===''}" @click="filterType=''">全部 ({{ allQuestions.length }})</button>
        <button :class="{active: filterType==='wrong'}" @click="filterType='wrong'" class="wrong-btn">仅错题 ({{ wrongCount }})</button>
      </div>
      <div v-for="(a, idx) in paginatedQuestions" :key="a.id" class="question-card">
        <div class="q-header">
          <span class="q-number">第 {{ a._globalIndex + 1 }} 题</span>
          <span class="q-type" :class="typeClass(a.question_type)">{{ typeLabel(a.question_type) }}</span>
          <span class="q-points">满分: {{ a.points }}</span>
          <span class="q-score" :class="scoreClass(a)">得分: {{ a.score ?? '未评分' }} / {{ a.points }}</span>
        </div>
        <div class="q-body">
          <div class="q-text">{{ a.question_text }}</div>
          <div v-if="a.question_type.startsWith('choice') && a.options" class="q-options">
            <div v-for="(opt, oi) in a.options" :key="oi" class="q-option" :class="{selected: isOptSelected(opt, a), correct: isOptCorrect(opt, a)}">
              <span class="opt-label">{{ String.fromCharCode(65 + oi) }}.</span> {{ opt }}
              <span v-if="isOptSelected(opt, a)" class="opt-mark my">我的</span>
              <span v-if="isOptCorrect(opt, a)" class="opt-mark ans">正确</span>
            </div>
          </div>
          <div class="q-answer">
            <span class="label">我的答案：</span>{{ a.student_answer || '(未作答)' }}
          </div>
          <div v-if="a.question_type !== 'essay'" class="q-answer correct">
            <span class="label">正确答案：</span>{{ a.correct_answer }}
          </div>
          <div v-if="a.is_correct !== null" class="q-result">
            <span :class="a.is_correct ? 'correct-tag' : 'wrong-tag'">
              {{ a.is_correct ? '✓ 正确' : '✗ 错误' }}
            </span>
          </div>
          <div v-if="a.teacher_comment" class="q-comment">
            <span class="label">教师评语：</span>{{ a.teacher_comment }}
          </div>
        </div>
      </div>
      <div v-if="paginatedQuestions.length === 0" class="empty">
        {{ filterType === 'wrong' ? '暂无错题，全部正确！' : '暂无题目' }}
      </div>
      <div v-if="totalPages > 1" class="pagination">
        <button :disabled="currentPage===1" @click="currentPage--">上一页</button>
        <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页 (共 {{ filteredQuestions.length }} 题)</span>
        <button :disabled="currentPage===totalPages" @click="currentPage++">下一页</button>
      </div>
    </div>
    <table v-else>
      <thead><tr><th>试卷</th><th>客观分</th><th>主观分</th><th>总分</th><th>状态</th><th>操作</th></tr></thead>
      <tbody><tr v-for="r in results" :key="r.session_id"><td>{{ r.paper_title }}</td>
        <td>{{ r.auto_score ?? '-' }}</td>
        <td>{{ r.manual_score ?? '-' }}</td>
        <td><strong>{{ r.total_score ?? '评分中' }}</strong></td>
        <td>{{ r.status === 'published' ? '成绩已公布' : r.status }}</td>
        <td><button @click="view(r.session_id)">查看答卷</button></td>
      </tr></tbody>
    </table>
    <p v-if="!results.length">暂无成绩</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '../../api'

const results = ref([])
const detail = ref(null)
const filterType = ref('')
const currentPage = ref(1)
const pageSize = 5

const paperTitle = computed(() => detail.value?.session?.paper_title || '未知试卷')
const session = computed(() => detail.value?.session || {})

const typeMap = {
  choice_single: '单选题',
  choice_multi: '多选题',
  fill_blank: '填空题',
  essay: '简答题'
}

function typeLabel(t) { return typeMap[t] || t }
function typeClass(t) { return 'type-' + t }
function scoreClass(a) {
  if (a.score === null) return ''
  return a.score >= a.points * 0.6 ? 'score-good' : 'score-bad'
}

function isOptSelected(opt, a) {
  const answers = (a.student_answer || '').replace(/\s/g, '').split(',')
  return answers.includes(opt)
}

function isOptCorrect(opt, a) {
  const correct = (a.correct_answer || '').replace(/\s/g, '').split(',')
  return correct.includes(opt)
}

const allQuestions = computed(() => {
  if (!detail.value) return []
  return (detail.value.answers || []).map((a, i) => ({ ...a, _globalIndex: i }))
})

const wrongCount = computed(() => allQuestions.value.filter(a => a.is_correct === false).length)

const filteredQuestions = computed(() => {
  if (filterType.value === 'wrong') {
    return allQuestions.value.filter(a => a.is_correct === false)
  }
  return allQuestions.value
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredQuestions.value.length / pageSize)))

const paginatedQuestions = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredQuestions.value.slice(start, start + pageSize)
})

watch(filterType, () => { currentPage.value = 1 })
watch(filteredQuestions, () => { if (currentPage.value > totalPages.value) currentPage.value = totalPages.value })

async function load() {
  const { data } = await api.get('/results')
  results.value = data
}

async function view(sid) {
  const { data } = await api.get(`/results/${sid}`)
  detail.value = data
  filterType.value = ''
  currentPage.value = 1
  const paper = results.value.find(r => r.session_id === sid)
  if (paper && data.session) {
    data.session.paper_title = paper.paper_title
  }
}

onMounted(load)
</script>

<style scoped>
table { width:100%; border-collapse:collapse; }
th { position:sticky; top:0; background:#f0ecf9; z-index:1; font-weight:600; font-size:14px; color:#464555; padding:0.75rem 1rem; text-align:left; border-bottom:1px solid #e4e1ee; }
td { padding:0.75rem 1rem; text-align:left; border-bottom:1px solid #e4e1ee; font-size:14px; }
tbody tr:hover { background:#f5f2ff; }
.back { padding:0.5rem 1rem; border:1px solid #c7c4d8; border-radius:0.5rem; background:#fff; cursor:pointer; color:#3525cd; font-weight:500; min-height:44px; transition:all 0.15s; }
.back:hover { border-color:#3525cd; background:#f5f2ff; }
.header { display:flex; justify-content:space-between; align-items:center; padding:1rem 1.5rem; background:#f0ecf9; border-radius:0.75rem; margin-bottom:1.5rem; }
.header h3 { margin:0; }
.scores { display:flex; gap:1.5rem; align-items:center; }
.score-item { font-size:14px; color:#464555; }
.score-item.total { font-size:16px; color:#1b1b24; font-weight:600; }
.filter-bar { display:flex; gap:0.5rem; margin-bottom:1.5rem; }
.filter-bar button { padding:0.5rem 1rem; border:1px solid #c7c4d8; border-radius:0.5rem; background:#fff; cursor:pointer; font-size:14px; min-height:44px; transition:all 0.15s; }
.filter-bar button.active { background:#3525cd; color:#fff; border-color:#3525cd; }
.wrong-btn.active { background:#ba1a1a !important; border-color:#ba1a1a !important; }
.question-card { border:1px solid #e4e1ee; border-radius:0.75rem; margin-bottom:1rem; overflow:hidden; background:#fff; box-shadow:0 1px 3px rgba(30,41,59,0.08); }
.q-header { display:flex; align-items:center; gap:0.5rem; padding:0.75rem 1rem; background:#f5f2ff; font-size:14px; }
.q-type { padding:0.125rem 0.5rem; border-radius:9999px; font-size:12px; font-weight:500; }
.type-choice_single,.type-choice_multi { background:rgba(53,37,205,0.1); color:#3525cd; }
.type-fill_blank { background:rgba(245,158,11,0.1); color:#b45309; }
.type-essay { background:rgba(119,117,135,0.1); color:#464555; }
.q-points { color:#464555; }
.q-score { margin-left:auto; font-weight:600; }
.q-body { padding:1rem 1.5rem; }
.q-text { font-weight:500; margin-bottom:0.5rem; line-height:1.7; }
.q-options { margin:0.5rem 0; }
.q-option { padding:0.375rem 0.75rem; margin:0.25rem 0; background:#f5f2ff; border-radius:0.5rem; border:1px solid transparent; }
.q-option.selected { border-color:#3525cd; background:rgba(53,37,205,0.05); }
.q-option.correct { border-color:#059669; background:rgba(16,185,129,0.05); }
.q-option.selected.correct { background:rgba(16,185,129,0.1); border-color:#059669; }
.opt-label { font-weight:600; margin-right:0.25rem; }
.opt-mark { float:right; font-size:12px; padding:0.125rem 0.375rem; border-radius:9999px; }
.opt-mark.my { color:#3525cd; background:rgba(53,37,205,0.1); }
.opt-mark.ans { color:#059669; background:rgba(16,185,129,0.1); margin-left:0.25rem; }
.q-answer { margin:0.375rem 0; }
.q-answer.correct { color:#059669; }
.q-answer .label,.q-comment .label { font-weight:600; color:#1b1b24; }
.q-comment { margin-top:0.5rem; padding:0.5rem 0.75rem; background:#f5f2ff; border-radius:0.5rem; font-size:14px; }
.q-result { margin-top:0.375rem; }
.correct-tag { color:#059669; font-weight:600; }
.wrong-tag { color:#ba1a1a; font-weight:600; }
.pagination { display:flex; justify-content:center; align-items:center; gap:0.75rem; padding:1.5rem 0; }
.pagination button { padding:0.5rem 1rem; border:1px solid #c7c4d8; border-radius:0.5rem; background:#fff; cursor:pointer; min-height:44px; transition:all 0.15s; }
.pagination button:hover:not(:disabled) { border-color:#3525cd; color:#3525cd; }
.pagination button:disabled { opacity:0.4; cursor:not-allowed; }
.page-info { font-size:14px; color:#464555; }
.empty { text-align:center; padding:3rem; color:#464555; }
.score-good { color:#059669; }
.score-bad { color:#ba1a1a; }
</style>
