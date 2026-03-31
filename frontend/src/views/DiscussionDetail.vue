<template>
  <div class="page">
    <div class="page-header">
      <div>
        <el-button link type="primary" @click="$router.push('/discussions')">← 返回讨论区</el-button>
        <h1 class="page-title">{{ post?.title || '帖子详情' }}</h1>
        <p class="page-subtitle">{{ post?.author_name }} · {{ formatTime(post?.created_at) }}</p>
      </div>
      <div class="page-actions">
        <el-button @click="likePost">点赞 {{ post?.likes || 0 }}</el-button>
      </div>
    </div>

    <el-card v-if="post" class="detail-card">
      <div class="detail-meta">
        <el-tag size="small">{{ post.category }}</el-tag>
        <el-tag v-if="post.is_pinned" size="small" type="danger">置顶</el-tag>
      </div>
      <div class="content">{{ post.content }}</div>
    </el-card>

    <el-card class="comment-card">
      <template #header>评论</template>
      <el-input v-model="newComment" type="textarea" rows="3" placeholder="写下你的想法..." />
      <div class="comment-actions">
        <el-button type="primary" :loading="commenting" @click="sendComment">发布评论</el-button>
      </div>
      <div class="comment-list">
        <div v-for="c in comments" :key="c.id" class="comment-item">
          <div class="comment-head">
            <strong>{{ c.author_name }}</strong>
            <span>{{ formatTime(c.created_at) }}</span>
          </div>
          <p>{{ c.content }}</p>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../stores/auth'

const route = useRoute()
const id = computed(() => route.params.id)
const post = ref(null)
const comments = ref([])
const newComment = ref('')
const commenting = ref(false)

const formatTime = (t) => (t ? new Date(t).toLocaleString() : '')

const load = async () => {
  try {
    const { data } = await api.get(`/api/discussions/${id.value}`)
    post.value = data
    comments.value = data.comments || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载失败')
  }
}

const likePost = async () => {
  try {
    const { data } = await api.post(`/api/discussions/${id.value}/like`)
    if (post.value) post.value.likes = data.likes
  } catch {
    ElMessage.error('操作失败')
  }
}

const sendComment = async () => {
  if (!newComment.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }
  commenting.value = true
  try {
    await api.post(`/api/discussions/${id.value}/comments`, {
      content: newComment.value.trim(),
    })
    newComment.value = ''
    ElMessage.success('已发布')
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '发布失败')
  } finally {
    commenting.value = false
  }
}

load()
</script>

<style scoped>
.detail-card {
  margin-bottom: 12px;
}
.detail-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}
.content {
  white-space: pre-wrap;
  line-height: 1.8;
}
.comment-actions {
  margin-top: 10px;
  text-align: right;
}
.comment-list {
  margin-top: 14px;
  display: grid;
  gap: 8px;
}
.comment-item {
  padding: 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
}
.comment-head {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #a5b4fc;
}
</style>
