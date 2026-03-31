<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">讨论区</h1>
        <p class="page-subtitle">文学翻译交流、作品讨论、问题互助。</p>
      </div>
      <div class="page-actions">
        <el-button type="primary" @click="openCreate">发布新帖</el-button>
      </div>
    </div>

    <div class="toolbar">
      <el-input
        v-model="filters.q"
        placeholder="搜索帖子标题或内容"
        clearable
        @clear="load"
        @keyup.enter="load"
      />
      <el-select v-model="filters.category" placeholder="分类" clearable @change="load">
        <el-option label="全部分类" value="" />
        <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
      </el-select>
      <el-button @click="load">查询</el-button>
    </div>

    <div class="post-list">
      <el-card v-for="p in posts" :key="p.id" class="post-card" shadow="hover" @click="goDetail(p.id)">
        <div class="post-head">
          <h3 class="post-title">{{ p.title }}</h3>
          <div class="post-tags">
            <el-tag v-if="p.is_pinned" type="danger" size="small">置顶</el-tag>
            <el-tag size="small">{{ p.category }}</el-tag>
          </div>
        </div>
        <p class="post-summary">{{ p.summary }}</p>
        <div class="post-meta">
          <span>{{ p.author_name }}</span>
          <span>{{ formatTime(p.created_at) }}</span>
          <span>点赞 {{ p.likes || 0 }}</span>
          <span>评论 {{ p.comment_count || 0 }}</span>
        </div>
      </el-card>
      <el-empty v-if="!loading && posts.length === 0" description="暂无帖子" />
    </div>

    <el-dialog v-model="createVisible" title="发布新帖" width="620px">
      <el-form label-position="top">
        <el-form-item label="分类">
          <el-select v-model="createForm.category" style="width: 100%">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="createForm.title" />
        </el-form-item>
        <el-form-item label="正文">
          <el-input v-model="createForm.content" type="textarea" rows="7" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="submitCreate">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../stores/auth'

const router = useRouter()
const loading = ref(false)
const posts = ref([])
const creating = ref(false)
const createVisible = ref(false)
const categories = ['翻译交流', '作品讨论', '技术问题', '公告']

const filters = reactive({
  q: '',
  category: '',
})

const createForm = reactive({
  category: '翻译交流',
  title: '',
  content: '',
})

const load = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/api/discussions', {
      params: {
        q: filters.q || undefined,
        category: filters.category || undefined,
      },
    })
    posts.value = data.items || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

const formatTime = (t) => (t ? new Date(t).toLocaleString() : '')

const goDetail = (id) => {
  router.push(`/discussions/${id}`)
}

const openCreate = () => {
  createVisible.value = true
}

const submitCreate = async () => {
  if (!createForm.title.trim() || !createForm.content.trim()) {
    ElMessage.warning('请填写标题和正文')
    return
  }
  creating.value = true
  try {
    const { data } = await api.post('/api/discussions', {
      category: createForm.category,
      title: createForm.title.trim(),
      content: createForm.content.trim(),
    })
    createVisible.value = false
    createForm.title = ''
    createForm.content = ''
    ElMessage.success('发布成功')
    router.push(`/discussions/${data.id}`)
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '发布失败')
  } finally {
    creating.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: grid;
  grid-template-columns: 1fr 180px 100px;
  gap: 10px;
  margin-bottom: 14px;
}
.post-list {
  display: grid;
  gap: 12px;
}
.post-card {
  cursor: pointer;
}
.post-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}
.post-title {
  margin: 0;
  font-size: 18px;
}
.post-tags {
  display: flex;
  gap: 8px;
}
.post-summary {
  margin: 8px 0;
  color: #cbd5e1;
}
.post-meta {
  display: flex;
  gap: 14px;
  font-size: 12px;
  color: #a5b4fc;
}
@media (max-width: 900px) {
  .toolbar {
    grid-template-columns: 1fr;
  }
}
</style>
