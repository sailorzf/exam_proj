<template>
  <div>
    <h2>发布管理</h2>
    <table><thead><tr><th>ID</th><th>试卷</th><th>状态</th><th>时间窗口</th><th>时长</th><th>操作</th></tr></thead>
      <tbody><tr v-for="p in papers" :key="p.id"><td>{{ p.id }}</td><td>{{ p.title }}</td><td>{{ p.status }}</td>
        <td>{{ fmt(p.window_start) }} ~ {{ fmt(p.window_end) }}</td><td>{{ p.duration_minutes?p.duration_minutes+' 分钟':'-' }}</td>
        <td><button v-if="p.status==='draft'" @click="showPub(p)">发布</button>
            <button v-if="p.status==='active'" class="danger" @click="doUnpub(p)">下线</button></td></tr></tbody>
    </table>
    <div v-if="pubPaper" class="modal"><div class="modal-content">
      <h3>发布: {{ pubPaper.title }}</h3>
      <label>开始时间</label><input v-model="wStart" type="datetime-local" />
      <label>结束时间</label><input v-model="wEnd" type="datetime-local" />
      <label>考试时长（分钟）</label><input v-model.number="dur" type="number" />
      <div class="modal-actions"><button @click="doPub">确认发布</button><button @click="pubPaper=null">取消</button></div>
    </div></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
const papers = ref([]), pubPaper = ref(null), wStart = ref(''), wEnd = ref(''), dur = ref(60)
function fmt(d){ return d?new Date(d).toLocaleString():'-' }
async function load(){ const { data }=await api.get('/papers/'); papers.value=data }
function showPub(p){ pubPaper.value=p; const now=new Date(); const later=new Date(now.getTime()+3600000); wStart.value=now.toISOString().slice(0,16); wEnd.value=later.toISOString().slice(0,16); dur.value=60 }
async function doPub(){ await api.post(`/papers/${pubPaper.value.id}/publish`,{window_start:wStart.value,window_end:wEnd.value,duration_minutes:dur.value}); pubPaper.value=null; await load() }
async function doUnpub(p){ await api.put(`/papers/${p.id}/unpublish`); await load() }
onMounted(load)
</script>

<style scoped>
table{width:100%;border-collapse:collapse;} th,td{padding:0.5rem;text-align:left;border-bottom:1px solid #e2e8f0;}
.modal{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;justify-content:center;align-items:center;z-index:100;}
.modal-content{background:white;padding:1.5rem;border-radius:8px;width:400px;} .modal-content input,.modal-content label{width:100%;display:block;margin-bottom:0.5rem;} .modal-content input{padding:0.5rem;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;}
.modal-actions{display:flex;gap:0.5rem;} .danger{background:#ef4444;color:white;}
</style>
