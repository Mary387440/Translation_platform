<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">控制台</h1>
        <p class="page-subtitle">
          SailoAI：中国文学多语种出海 · 对齐「AI 预译 + 人工润色 + 读者反馈」闭环。
        </p>
      </div>
      <div class="page-actions">
        <el-button type="primary" @click="$router.push('/works')">进入书库</el-button>
        <el-button @click="$router.push('/datasets')">数据集</el-button>
      </div>
    </div>

    <div class="card-grid">
      <el-card shadow="hover">
        <template #header>书库作品</template>
        <div class="stat-num">{{ summary.literary_works ?? '—' }}</div>
        <p class="stat-desc">已创建的网络文学书目</p>
      </el-card>
      <el-card shadow="hover">
        <template #header>上传文档</template>
        <div class="stat-num">{{ summary.documents ?? '—' }}</div>
        <p class="stat-desc">文档库中的文件数</p>
      </el-card>
      <el-card shadow="hover">
        <template #header>术语条目</template>
        <div class="stat-num">{{ summary.glossary_entries ?? '—' }}</div>
        <p class="stat-desc">用于 RAG 的术语规模</p>
      </el-card>
      <el-card shadow="hover">
        <template #header>近 7 日 AI 调用</template>
        <div class="stat-num">{{ summary.ai_calls_7d ?? '—' }}</div>
        <p class="stat-desc">翻译 / 模型请求次数（估算）</p>
      </el-card>
    </div>

    <el-alert
      :title="summary.tagline || 'SailoAI'"
      type="info"
      show-icon
      style="margin-top: 16px"
      description="配置 DEEPSEEK_API_KEY 后，阅读器内「AI 翻译」将调用真实大模型；未配置时使用模拟译文便于开发。"
    />
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../stores/auth'

const summary = reactive({
  literary_works: null,
  documents: null,
  glossary_entries: null,
  ai_calls_7d: null,
  tagline: '',
})

onMounted(async () => {
  try {
    const { data } = await api.get('/api/dashboard/summary')
    Object.assign(summary, data)
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载汇总失败，请先登录')
  }
})
</script>

<style scoped>
.stat-num {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
}
.stat-desc {
  margin: 8px 0 0;
  font-size: 13px;
  color: #6b7280;
}
</style>
