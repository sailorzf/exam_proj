<template>
  <div>
    <h2>错题集</h2>
    <div v-if="!wrongAnswers.length" class="empty">
      <p>恭喜！全部答对，没有错题。</p>
      <button @click="goResults">查看成绩</button>
    </div>
    <div v-else>
      <div class="summary">
        <span>共 {{ wrongAnswers.length }} 道错题</span>
        <button @click="goResults">查看成绩</button>
      </div>
      <div v-for="(item, idx) in wrongAnswers" :key="item.question_id" class="card">
        <div class="q-header">
          <span class="q-num">错题 {{ idx + 1 }}</span>
          <span class="q-type">{{ typeLabel(item.question_type) }}</span>
          <span class="q-points">{{ item.points }} 分</span>
          <span class="q-score">得分：{{ item.score ?? 0 }}</span>
        </div>
        <div class="q-text">{{ item.question_text }}</div>
        <div v-if="item.options" class="q-options">
          <div v-for="(opt, oi) in item.options" :key="oi" class="option"
               :class="{correct: isCorrectOption(opt, item.correct_answer), wrong: isWrongOption(opt, item.student_answer, item.question_type)}">
            <span class="opt-label">{{ String.fromCharCode(65 + oi) }}.</span>
            <span class="opt-text">{{ opt }}</span>
            <span v-if="isCorrectOption(opt, item.correct_answer)" class="badge correct-badge">正确答案</span>
            <span v-if="isWrongOption(opt, item.student_answer, item.question_type)" class="badge wrong-badge">你的选择</span>
          </div>
        </div>
        <div class="q-answer-compare">
          <div class="answer-row"><span class="label">你的答案：</span><span class="wrong-text">{{ item.student_answer || '(未作答)' }}</span></div>
          <div class="answer-row"><span class="label">正确答案：</span><span class="correct-text">{{ item.correct_answer }}</span></div>
        </div>
        <div v-if="item.question_type === 'essay'" class="q-answer-compare">
          <div class="answer-row"><span class="label">你的答案：</span><span>{{ item.student_answer }}</span></div>
          <div class="answer-row"><span class="label">参考答案：</span><span class="correct-text">{{ item.correct_answer }}</span></div>
          <div v-if="item.teacher_comment" class="answer-row"><span class="label">教师评语：</span><span>{{ item.teacher_comment }}</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute(), router = useRouter()
const wrongAnswers = ref([])
const typeLabel = t => ({ choice_single: '单选题', choice_multi: '多选题', fill_blank: '填空题', essay: '简答题' }[t] || t)

function isCorrectOption(opt, correctAnswer) {
  return correctAnswer.split(/[,,]/).map(s => s.trim()).includes(opt.trim())
}
function isWrongOption(opt, studentAnswer, type) {
  if (type !== 'choice_single' && type !== 'choice_multi') return false
  return studentAnswer.split(/[,,]/).map(s => s.trim()).includes(opt.trim())
}

function goResults() { router.push('/student/results') }

onMounted(() => {
  const data = history.state.wrongAnswers
  if (data) wrongAnswers.value = data
})
</script>

<style scoped>
.summary { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; padding: 0.75rem 1rem; background: #f0ecf9; border-radius: 0.5rem; }
.summary span { font-weight: 600; color: #464555; }
.summary button { padding: 0.5rem 1rem; background: #3525cd; color: #fff; border: none; border-radius: 0.5rem; cursor: pointer; min-height: 44px; }
.summary button:hover { background: #4f46e5; }
.empty { text-align: center; padding: 3rem; color: #464555; }
.empty button { margin-top: 1rem; padding: 0.75rem 2rem; background: #3525cd; color: #fff; border: none; border-radius: 0.5rem; cursor: pointer; min-height: 44px; }
.card { background: #fff; border: 1px solid #e4e1ee; border-radius: 0.75rem; box-shadow: 0 1px 3px rgba(30,41,59,0.08); padding: 1.5rem; margin-bottom: 1rem; }
.q-header { display: flex; gap: 0.75rem; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap; }
.q-num { font-weight: 700; color: #ba1a1a; }
.q-type { background: #f0ecf9; color: #464555; padding: 0.25rem 0.5rem; border-radius: 0.375rem; font-size: 12px; }
.q-points { font-size: 13px; color: #777587; }
.q-score { font-weight: 600; color: #ba1a1a; margin-left: auto; }
.q-text { font-size: 15px; line-height: 1.6; margin-bottom: 1rem; color: #1e293b; }
.q-options { display: flex; flex-direction: column; gap: 0.5rem; }
.option { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; border-radius: 0.5rem; border: 1px solid transparent; }
.option.correct { background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.3); }
.option.wrong { background: rgba(186,26,26,0.08); border-color: rgba(186,26,26,0.3); }
.opt-label { font-weight: 600; min-width: 1.5rem; }
.opt-text { flex: 1; }
.badge { font-size: 11px; padding: 0.125rem 0.375rem; border-radius: 9999px; font-weight: 500; }
.correct-badge { background: #10b981; color: #fff; }
.wrong-badge { background: #ba1a1a; color: #fff; }
.q-answer-compare { display: flex; flex-direction: column; gap: 0.5rem; }
.answer-row { display: flex; gap: 0.5rem; font-size: 14px; }
.answer-row .label { font-weight: 600; min-width: 5rem; color: #464555; }
.wrong-text { color: #ba1a1a; }
.correct-text { color: #059669; }
</style>
