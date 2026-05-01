<template>
  <div class="question-renderer">
    <h3>{{ label }}. {{ question.question_text }}</h3>
    <div v-if="question.type === 'choice_single'" class="options">
      <label v-for="(opt, idx) in question.options" :key="idx" class="option">
        <input type="radio" :name="'q_'+question.question_id" :value="optionLetter(idx)"
          :checked="modelValue === optionLetter(idx)" @change="$emit('update:modelValue', optionLetter(idx))" />
        {{ optionLetter(idx) }}. {{ opt }}
      </label>
    </div>
    <div v-else-if="question.type === 'choice_multi'" class="options">
      <label v-for="(opt, idx) in question.options" :key="idx" class="option">
        <input type="checkbox" :value="optionLetter(idx)" :checked="selectedLetters.includes(optionLetter(idx))"
          @change="toggleOption(optionLetter(idx))" />
        {{ optionLetter(idx) }}. {{ opt }}
      </label>
    </div>
    <div v-else-if="question.type === 'fill_blank'" class="fill">
      <input type="text" :value="modelValue" @input="$emit('update:modelValue', $event.target.value)" placeholder="请输入答案" />
    </div>
    <div v-else-if="question.type === 'essay'" class="essay">
      <textarea :value="modelValue" @input="$emit('update:modelValue', $event.target.value)" rows="6" placeholder="请输入答案"></textarea>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ question: { type: Object, required: true }, modelValue: { type: String, default: '' }, label: { type: Number, default: 1 } })
const emit = defineEmits(['update:modelValue'])

function optionLetter(idx) { return String.fromCharCode(65 + idx) }
const selectedLetters = computed(() => props.modelValue ? props.modelValue.split(',') : [])

function toggleOption(letter) {
  const current = props.modelValue ? props.modelValue.split(',') : []
  const idx = current.indexOf(letter)
  if (idx >= 0) current.splice(idx, 1); else current.push(letter)
  emit('update:modelValue', current.sort().join(','))
}
</script>

<style scoped>
.question-renderer { padding:1rem 0; }
.question-renderer h3 { margin-bottom:1rem; }
.options { display:flex; flex-direction:column; gap:0.75rem; }
.option { display:flex; align-items:center; gap:0.5rem; padding:0.75rem; background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; cursor:pointer; }
.option:hover { background:#eff6ff; }
.fill input, .essay textarea { width:100%; padding:0.5rem; border:1px solid #ddd; border-radius:4px; font-size:1rem; box-sizing:border-box; }
</style>
