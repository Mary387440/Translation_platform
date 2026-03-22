<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">场景文字 · OCR</h1>
        <p class="page-subtitle">
          对应计划书 PaddleOCR：上传街景/截图等图片，识别文字并翻译（当前为后端占位，可接入真实识别）。
        </p>
      </div>
      <el-select v-model="targetLang" style="width: 120px">
        <el-option label="English" value="en" />
        <el-option label="日本語" value="ja" />
        <el-option label="한국어" value="ko" />
      </el-select>
    </div>

    <el-card>
      <el-upload
        drag
        :auto-upload="false"
        :on-change="onFile"
        :show-file-list="false"
        accept="image/png,image/jpeg,image/webp"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽图片到此处，或 <em>点击选择</em></div>
      </el-upload>
      <div v-if="result" class="ocr-result">
        <h4>识别</h4>
        <p>{{ result.recognized_text }}</p>
        <h4>译文</h4>
        <p>{{ result.translated_text }}</p>
        <p class="hint">{{ result.hint }}</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { api } from '../stores/auth'

const targetLang = ref('en')
const result = ref(null)

const onFile = async (uploadFile) => {
  const raw = uploadFile.raw
  if (!raw) return
  const fd = new FormData()
  fd.append('file', raw)
  fd.append('target_lang', targetLang.value)
  try {
    const { data } = await api.post('/api/ocr/scan', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    result.value = data
    ElMessage.success('处理完成（占位）')
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '上传失败')
  }
}
</script>

<style scoped>
.ocr-result {
  margin-top: 20px;
}
.ocr-result h4 {
  margin: 12px 0 6px;
  font-size: 14px;
}
.ocr-result .hint {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 12px;
}
</style>
