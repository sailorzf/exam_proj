<template>
  <div>
    <h2>发布管理</h2>
    <table><thead><tr><th>ID</th><th>试卷</th><th>状态</th><th>时间窗口</th><th>时长</th><th>操作</th></tr></thead>
      <tbody><tr v-for="p in papers" :key="p.id"><td>{{ p.id }}</td><td>{{ p.title }}</td><td><span class="status-chip" :class="'status-'+p.status">{{ p.status }}</span></td>
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
function fmt(d){ return d?new Date(d+'Z').toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}):'-' }
function toLocal(d){ const pad=n=>String(n).padStart(2,'0'); return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}` }
function toUTC(d){ const pad=n=>String(n).padStart(2,'0'); const utc=new Date(d.toISOString().replace('Z','')); return `${utc.getUTCFullYear()}-${pad(utc.getUTCMonth()+1)}-${pad(utc.getUTCDate())}T${pad(utc.getUTCHours())}:${pad(utc.getUTCMinutes())}` }
async function load(){ const { data }=await api.get('/papers/'); papers.value=data }
function showPub(p){ pubPaper.value=p; const now=new Date(); const later=new Date(now.getTime()+3600000); wStart.value=toUTC(now); wEnd.value=toUTC(later); dur.value=60 }
async function doPub(){ await api.post(`/papers/${pubPaper.value.id}/publish`,{window_start:wStart.value+'Z',window_end:wEnd.value+'Z',duration_minutes:dur.value}); pubPaper.value=null; await load() }
async function doUnpub(p){ await api.put(`/papers/${p.id}/unpublish`); await load() }
onMounted(load)
</script>

<style scoped>
.card { background:#fff; border:1px solid #e4e1ee; border-radius:0.75rem; box-shadow:0 1px 3px rgba(30,41,59,0.08); overflow:hidden; }
table { width:100%; border-collapse:collapse; }
th { position:sticky; top:0; background:#f0ecf9; z-index:1; font-weight:600; font-size:14px; color:#464555; padding:0.75rem 1rem; text-align:left; border-bottom:1px solid #e4e1ee; }
td { padding:0.75rem 1rem; text-align:left; border-bottom:1px solid #e4e1ee; font-size:14px; }
tbody tr:hover { background:#f5f2ff; }
.modal { position:fixed; top:0;left:0;right:0;bottom:0; background:rgba(0,0,0,0.4); display:flex; justify-content:center; align-items:center; z-index:100; backdrop-filter:blur(2px); }
.modal-content { background:#fff; padding:1.5rem; border-radius:0.75rem; width:400px; box-shadow:0 20px 60px rgba(30,41,59,0.15); }
.modal-content input,.modal-content label { width:100%; display:block; margin-bottom:0.75rem; }
.modal-content input { padding:0.75rem; border:1px solid rgba(119,117,135,0.3); border-radius:0.5rem; box-sizing:border-box; }
.modal-content label { font-size:14px; font-weight:500; color:#464555; }
.modal-actions { display:flex; gap:0.75rem; }
.modal-actions button { min-height:44px; padding:0.5rem 1.5rem; border-radius:0.5rem; }
.modal-actions button:first-child { background:#3525cd; color:#fff; border:none; }
.modal-actions button:first-child:hover { background:#4f46e5; }
.modal-actions button:last-child { background:transparent; color:#464555; border:1px solid #c7c4d8; }
.danger { background:#ba1a1a; color:#fff; border:none; border-radius:0.5rem; padding:0.5rem 1rem; cursor:pointer; min-height:44px; }
.danger:hover { background:#dc2626; }
.status-chip { display:inline-block; padding:0.25rem 0.625rem; border-radius:9999px; font-size:12px; font-weight:500; }
.status-draft { background:rgba(119,117,135,0.1); color:#464555; }
.status-active { background:rgba(16,185,129,0.1); color:#059669; }
.status-offline { background:rgba(186,26,26,0.1); color:#ba1a1a; }
</style>
