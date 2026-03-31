<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">书稿与章节</h1>
        <p class="page-subtitle">创建作品、导入章节；发布后对读者可见。翻译润色在预览中完成。</p>
      </div>
      <div class="page-actions">
        <el-button type="primary" @click="openCreate">新建作品</el-button>
        <el-button @click="runDemo">一键示例</el-button>
        <el-button @click="runClassics">一键经典</el-button>
      </div>
    </div>

    <div class="toolbar">
      <el-input v-model="filters.q" placeholder="搜索标题" clearable style="max-width: 220px" @clear="load" @keyup.enter="load" />
      <el-select v-model="filters.genre" placeholder="题材" clearable style="width: 120px" @change="load">
        <el-option label="全部题材" value="" />
        <el-option label="玄幻" value="玄幻" />
        <el-option label="仙侠" value="仙侠" />
        <el-option label="都市" value="都市" />
        <el-option label="科幻" value="科幻" />
        <el-option label="言情" value="言情" />
        <el-option label="历史" value="历史" />
        <el-option label="其他" value="其他" />
      </el-select>
      <el-select v-model="filters.status" style="width: 120px" @change="load">
        <el-option label="全部状态" value="all" />
        <el-option label="已发布" value="published" />
        <el-option label="草稿" value="draft" />
      </el-select>
    </div>

    <div class="work-grid">
      <el-card v-for="w in items" :key="w.id" class="work-card" shadow="hover">
        <template #header>
          <div class="card-head">
            <span class="title">{{ w.title }}</span>
            <el-tag size="small">{{ w.genre }}</el-tag>
          </div>
        </template>
        <p class="meta">{{ w.author_name || '佚名' }} · {{ w.src_lang }} · {{ w.status }}</p>
        <p class="summary">{{ w.summary || '暂无简介' }}</p>
        <div class="card-actions">
          <el-button type="primary" link @click="goRead(w)">预览 / 润色</el-button>
        </div>
      </el-card>
    </div>
    <el-empty v-if="!loading && items.length === 0" description="暂无作品，请新建或导入示例" />

    <el-dialog v-model="createVisible" title="新建作品" width="480px">
      <el-form label-position="top">
        <el-form-item label="标题" required>
          <el-input v-model="createForm.title" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="createForm.author_name" />
        </el-form-item>
        <el-form-item label="题材">
          <el-select v-model="createForm.genre" style="width: 100%">
            <el-option v-for="g in genres" :key="g" :label="g" :value="g" />
          </el-select>
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="createForm.summary" type="textarea" rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>
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
const filters = reactive({ q: '', genre: '', status: 'all' })
const createVisible = ref(false)
const createLoading = ref(false)
const createForm = reactive({
  title: '',
  author_name: '',
  genre: '其他',
  summary: '',
})
const genres = ['玄幻', '仙侠', '都市', '科幻', '言情', '历史', '其他']

const load = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/api/works', {
      params: {
        q: filters.q || undefined,
        genre: filters.genre || undefined,
        status: filters.status,
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

const openCreate = () => {
  Object.assign(createForm, { title: '', author_name: '', genre: '其他', summary: '' })
  createVisible.value = true
}

const submitCreate = async () => {
  if (!createForm.title?.trim()) {
    ElMessage.warning('请填写标题')
    return
  }
  createLoading.value = true
  try {
    const { data } = await api.post('/api/works', {
      title: createForm.title.trim(),
      author_name: createForm.author_name || undefined,
      genre: createForm.genre,
      summary: createForm.summary || undefined,
      status: 'published',
    })
    createVisible.value = false
    ElMessage.success('已创建并写入示例章节')
    await api.post(`/api/works/${data.id}/seed-demo`)
    await load()
    const { data: ch } = await api.get(`/api/works/${data.id}/chapters`)
    const first = ch.items?.[0]
    if (first) {
      router.push({
        name: 'AdminWorkReader',
        params: { workId: String(data.id), chapterId: String(first.id) },
      })
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '创建失败')
  } finally {
    createLoading.value = false
  }
}

const runDemo = async () => {
  try {
    const { data: w } = await api.post('/api/works', {
      title: '示例：风起之夜',
      author_name: 'SailoAI',
      genre: '都市',
      summary: '体验 DeepSeek + 术语/平行句 RAG 的对照阅读流程。',
      status: 'published',
    })
    await api.post(`/api/works/${w.id}/seed-demo`)
    ElMessage.success('已生成示例章节')
    await load()
    const { data: ch } = await api.get(`/api/works/${w.id}/chapters`)
    const first = ch.items?.[0]
    if (first) {
      router.push({
        name: 'AdminWorkReader',
        params: { workId: String(w.id), chapterId: String(first.id) },
      })
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '失败')
  }
}

const runClassics = async () => {
  try {
    const { data } = await api.post('/api/works/seed-classics', { count: 4 })
    const first = data?.created?.[0]
    ElMessage.success('已生成经典作品')
    await load()
    if (!first?.work_id) return
    const { data: ch } = await api.get(`/api/works/${first.work_id}/chapters`)
    const firstCh = ch.items?.[0]
    if (firstCh) {
      router.push({
        name: 'AdminWorkReader',
        params: { workId: String(first.work_id), chapterId: String(firstCh.id) },
      })
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '失败')
  }
}

const goRead = async (w) => {
  try {
    const { data } = await api.get(`/api/works/${w.id}/chapters`)
    const first = data.items?.[0]
    if (!first) {
      ElMessage.info('请先添加章节')
      return
    }
    router.push({
      name: 'AdminWorkReader',
      params: { workId: String(w.id), chapterId: String(first.id) },
    })
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '无法进入')
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
.work-card .card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.work-card .title {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.meta {
  font-size: 13px;
  color: #6b7280;
  margin: 0 0 8px;
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
}
</style>
