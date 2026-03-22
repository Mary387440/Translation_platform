<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">设置</h1>
        <p class="page-subtitle">默认翻译语种将用于阅读器体验（与计划书「用户偏好」一致）。</p>
      </div>
    </div>
    <el-card style="max-width: 480px">
      <el-form label-position="top" @submit.prevent="save">
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" />
        </el-form-item>
        <el-form-item label="默认源语言">
          <el-input v-model="form.preferred_src_lang" placeholder="如 zh" />
        </el-form-item>
        <el-form-item label="默认目标语言">
          <el-input v-model="form.preferred_tgt_lang" placeholder="如 en" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../stores/auth'

const form = reactive({
  nickname: '',
  preferred_src_lang: '',
  preferred_tgt_lang: '',
})
const saving = ref(false)

const load = async () => {
  try {
    const { data } = await api.get('/api/auth/me')
    form.nickname = data.nickname || ''
    form.preferred_src_lang = data.preferred_src_lang || ''
    form.preferred_tgt_lang = data.preferred_tgt_lang || ''
  } catch {
    ElMessage.warning('请先登录')
  }
}

onMounted(load)

const save = async () => {
  saving.value = true
  try {
    await api.put('/api/auth/profile', { ...form })
    ElMessage.success('已保存')
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>
