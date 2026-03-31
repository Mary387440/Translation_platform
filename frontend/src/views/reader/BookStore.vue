<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">书库</h1>
        <p class="page-subtitle">浏览已上架作品，支持多语种对照阅读与 AI 翻译。</p>
      </div>
    </div>

    <div class="toolbar">
      <el-input
        v-model="filters.q"
        placeholder="搜索书名"
        clearable
        style="max-width: 220px"
        @clear="load"
        @keyup.enter="load"
      />
      <el-select v-model="filters.genre" placeholder="题材" clearable style="width: 120px" @change="load">
        <el-option label="全部" value="" />
        <el-option label="玄幻" value="玄幻" />
        <el-option label="仙侠" value="仙侠" />
        <el-option label="都市" value="都市" />
        <el-option label="科幻" value="科幻" />
        <el-option label="言情" value="言情" />
        <el-option label="历史" value="历史" />
        <el-option label="其他" value="其他" />
      </el-select>
    </div>

    <div class="work-grid">
      <el-card v-for="w in items" :key="w.id" class="work-card" shadow="hover">
        <div class="card-body">
          <div class="cover" :style="coverStyle(w)">
            <div class="cover-inner">
              <div class="cover-title">
                {{ coverTitle(w.title) }}
              </div>
              <div class="cover-sub">
                {{ w.genre }}
              </div>
            </div>
          </div>

          <div class="card-info">
            <div class="card-head">
              <span class="title" :title="w.title">{{ w.title }}</span>
              <el-tag size="small" class="tag">{{ w.genre }}</el-tag>
            </div>
            <p class="meta">
              {{ w.author_name || '佚名' }} · {{ w.src_lang }}
              <span v-if="w.chapter_count != null"> · {{ w.chapter_count }} 章</span>
            </p>
            <p class="summary">{{ w.summary || '暂无简介' }}</p>
            <div class="card-actions">
              <el-button type="primary" link @click="goRead(w)">开始阅读</el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>
    <el-empty v-if="!loading && items.length === 0" description="暂无已发布作品，请稍后再来或由管理员上架内容" />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../../stores/auth'

const router = useRouter()
const items = ref([])
const loading = ref(false)
const filters = reactive({ q: '', genre: '' })

const load = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/api/catalog/works', {
      params: {
        q: filters.q || undefined,
        genre: filters.genre || undefined,
      },
    })
    items.value = data.items || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)

const goRead = async (w) => {
  try {
    const { data } = await api.get(`/api/catalog/works/${w.id}/chapters`)
    const first = data.items?.[0]
    if (!first) {
      ElMessage.info('本书暂无章节')
      return
    }
    router.push({
      name: 'ReaderWorkReader',
      params: { workId: String(w.id), chapterId: String(first.id) },
    })
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '无法打开')
  }
}

const coverTitle = (t) => {
  if (!t) return ''
  // 封面展示尽量短
  const s = String(t).trim()
  return s.length > 10 ? s.slice(0, 10) + '…' : s
}

const coverStyle = (w) => {
  const genre = (w?.genre || '').trim()
  const map = {
    玄幻: ['#0ea5e9', '#2563eb'],
    仙侠: ['#a78bfa', '#7c3aed'],
    都市: ['#34d399', '#059669'],
    科幻: ['#60a5fa', '#1d4ed8'],
    言情: ['#fb7185', '#e11d48'],
    历史: ['#f59e0b', '#b45309'],
    其他: ['#94a3b8', '#475569'],
  }
  const [a, b] = map[genre] || map['其他']
  return {
    background: `linear-gradient(135deg, ${a} 0%, ${b} 100%)`,
  }
}
</script>

<style scoped>
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}
.work-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.work-card {
  border-radius: 14px;
}

.card-body {
  display: grid;
  grid-template-columns: 92px 1fr;
  gap: 12px;
  align-items: stretch;
}

.cover {
  border-radius: 12px;
  position: relative;
  overflow: hidden;
  min-height: 120px;
}

.cover::after {
  content: '';
  position: absolute;
  inset: -30% -30% auto -30%;
  height: 90px;
  background: radial-gradient(circle at 30% 40%, rgba(255, 255, 255, 0.55), rgba(255, 255, 255, 0) 60%);
  transform: rotate(-10deg);
}

.cover-inner {
  position: relative;
  height: 100%;
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.cover-title {
  color: rgba(255, 255, 255, 0.95);
  font-weight: 800;
  letter-spacing: 0.2px;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.25);
  line-height: 1.15;
  font-size: 14px;
  word-break: break-word;
}

.cover-sub {
  color: rgba(255, 255, 255, 0.9);
  font-size: 12px;
  font-weight: 600;
}

.card-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.title {
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag {
  flex-shrink: 0;
}

.meta {
  font-size: 13px;
  color: #6b7280;
  margin: 8px 0 8px;
}

.summary {
  font-size: 13px;
  color: #374151;
  margin: 0 0 12px;
  min-height: 40px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-actions {
  text-align: right;
  margin-top: auto;
}

@media (max-width: 560px) {
  .card-body {
    grid-template-columns: 80px 1fr;
  }
  .cover {
    min-height: 108px;
  }
}
</style>
