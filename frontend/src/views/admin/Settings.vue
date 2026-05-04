<template>
  <div>
    <h2>系统设置</h2>
    <div class="card">
      <div class="form-group">
        <label>背景图片</label>
        <div class="upload-area">
          <input type="file" accept="image/jpeg,image/png,image/webp" @change="onFileChange" />
          <p class="hint">支持 JPG/PNG/WebP 格式，建议 1920×1080 (16:9)，不超过 5MB</p>
          <button class="upload-btn" @click="showCropper = true" :disabled="!selectedFile">
            裁剪并上传
          </button>
        </div>
        <div v-if="form.background_image && !showCropper" class="preview-box">
          <img :src="form.background_image" alt="预览" />
          <button class="remove-btn" @click="form.background_image = ''">移除</button>
        </div>
      </div>
      <div class="form-group">
        <label>Copyright 文本</label>
        <input v-model="form.copyright_text" placeholder="© 2026 智慧考试系统 版权所有" />
      </div>
      <div class="actions">
        <button @click="save" :disabled="saving">{{ saving ? '保存中...' : '保存' }}</button>
        <button class="secondary" @click="load" :disabled="saving">重置</button>
      </div>
    </div>

    <!-- Cropper Modal -->
    <div v-if="showCropper" class="modal" @click.self="closeCropper">
      <div class="cropper-content">
        <h3>裁剪背景图片</h3>
        <p class="cropper-hint">推荐比例 16:9，裁剪后自动上传并设置为背景</p>
        <Cropper
          ref="cropperRef"
          :src="cropperSrc"
          :stencil-props="{ aspectRatio: 16/9 }"
          class="cropper"
        />
        <div class="cropper-actions">
          <button @click="cropAndUpload" :disabled="cropping">
            {{ cropping ? '处理中...' : '确认裁剪并上传' }}
          </button>
          <button class="secondary" @click="closeCropper">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Cropper } from 'vue-advanced-cropper'
import 'vue-advanced-cropper/dist/style.css'
import api from '../../api'

const form = ref({ background_image: '', copyright_text: '' })
const selectedFile = ref(null)
const cropperSrc = ref('')
const showCropper = ref(false)
const cropping = ref(false)
const uploading = ref(false)
const saving = ref(false)
const cropperRef = ref(null)

async function load() {
  try {
    const { data } = await api.get('/settings/')
    form.value = data
  } catch {
    // use defaults
  }
}

function onFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) {
    alert('文件大小不能超过 5MB')
    e.target.value = ''
    return
  }
  selectedFile.value = file
  cropperSrc.value = URL.createObjectURL(file)
}

function closeCropper() {
  showCropper.value = false
  selectedFile.value = null
  cropperSrc.value = ''
}

async function cropAndUpload() {
  if (!cropperRef.value) return
  cropping.value = true
  try {
    const { canvas } = cropperRef.value.getResult()
    canvas.toBlob(async (blob) => {
      try {
        cropping.value = false
        const fd = new FormData()
        fd.append('file', blob, 'background.jpg')
        const { data } = await api.post('/settings/upload-image', fd)
        form.value.background_image = data.url
        closeCropper()
      } catch (e) {
        alert(e.response?.data?.detail || '上传失败')
        cropping.value = false
      }
    }, 'image/jpeg', 0.92)
  } catch (e) {
    alert('裁剪处理失败')
    cropping.value = false
  }
}

async function save() {
  saving.value = true
  try {
    await api.put('/settings/', form.value)
    alert('设置已保存')
  } catch (e) {
    alert(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
h2 { margin-bottom: 1.5rem; }
.card {
  background: #fff;
  border: 1px solid #e4e1ee;
  border-radius: 0.75rem;
  padding: 1.5rem;
  max-width: 640px;
}
.form-group { margin-bottom: 1.25rem; }
.form-group label {
  display: block;
  margin-bottom: 0.375rem;
  font-weight: 500;
  font-size: 14px;
  color: #464555;
}
.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid rgba(119,117,135,0.3);
  border-radius: 0.5rem;
  box-sizing: border-box;
  min-height: 44px;
}
.upload-area {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}
.upload-area input[type="file"] {
  flex: 1;
  min-width: 0;
}
.hint {
  font-size: 12px;
  color: #777587;
  margin: 0;
  width: 100%;
}
.upload-btn {
  background: #3525cd;
  color: #fff;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  min-height: 44px;
  white-space: nowrap;
}
.upload-btn:hover { background: #4f46e5; }
.upload-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.preview-box {
  margin-top: 0.75rem;
  border-radius: 0.5rem;
  overflow: hidden;
  max-height: 200px;
  border: 1px solid #e4e1ee;
  position: relative;
}
.preview-box img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.remove-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: rgba(0,0,0,0.6);
  color: #fff;
  border: none;
  padding: 0.25rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 12px;
  cursor: pointer;
  min-height: auto;
}
.remove-btn:hover { background: rgba(0,0,0,0.8); }
.actions { display: flex; gap: 0.75rem; }
.actions button {
  background: #3525cd;
  color: #fff;
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: 0.5rem;
  min-height: 44px;
}
.actions button:hover { background: #4f46e5; }
.actions button:disabled { opacity: 0.6; cursor: not-allowed; }
.actions button.secondary {
  background: transparent;
  color: #464555;
  border: 1px solid #c7c4d8;
}
.actions button.secondary:hover { background: #f0ecf9; }

/* Cropper Modal */
.modal {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}
.cropper-content {
  background: #fff;
  padding: 1.5rem;
  border-radius: 0.75rem;
  width: 800px;
  max-width: 95vw;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.cropper-content h3 {
  margin: 0 0 0.5rem;
  font-size: 18px;
}
.cropper-hint {
  font-size: 13px;
  color: #777587;
  margin: 0 0 1rem;
}
.cropper {
  height: 450px;
  background: #1b1b24;
  border-radius: 0.5rem;
  overflow: hidden;
}
.cropper-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}
.cropper-actions button {
  background: #3525cd;
  color: #fff;
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: 0.5rem;
  min-height: 44px;
}
.cropper-actions button:hover { background: #4f46e5; }
.cropper-actions button:disabled { opacity: 0.6; cursor: not-allowed; }
.cropper-actions button.secondary {
  background: transparent;
  color: #464555;
  border: 1px solid #c7c4d8;
}
.cropper-actions button.secondary:hover { background: #f0ecf9; }
</style>
