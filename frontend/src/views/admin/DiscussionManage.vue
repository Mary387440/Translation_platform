<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">讨论区管理</h1>
        <p class="page-subtitle">帖子审核、置顶、分类管理。</p>
      </div>
      <div class="page-actions">
        <el-button @click="load">刷新</el-button>
      </div>
    </div>

    <el-table :data="rows" size="small" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" label="标题" min-width="220" />
      <el-table-column prop="category" label="分类" width="110" />
      <el-table-column prop="author_name" label="作者" width="120" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column label="置顶" width="80">
        <template #default="{ row }">
          <el-tag v-if="row.is_pinned" size="small" type="danger">是</el-tag>
          <span v-else>否</span>
        </template>
      </el-table-column>
      <el-table-column prop="likes" label="赞" width="80" />
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <div class="ops">
            <el-button size="small" @click="togglePin(row)">
              {{ row.is_pinned ? '取消置顶' : '置顶' }}
            </el-button>
            <el-button size="small" @click="toggleStatus(row)">
              {{ row.status === 'published' ? '隐藏' : '发布' }}
            </el-button>
            <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../../stores/auth'

const loading = ref(false)
const rows = ref([])

const load = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/api/discussions/admin/posts')
    rows.value = data.items || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

const togglePin = async (row) => {
  try {
    await api.put(`/api/discussions/admin/posts/${row.id}`, {
      is_pinned: !row.is_pinned,
    })
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  }
}

const toggleStatus = async (row) => {
  try {
    await api.put(`/api/discussions/admin/posts/${row.id}`, {
      status: row.status === 'published' ? 'hidden' : 'published',
    })
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  }
}

const remove = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除帖子「${row.title}」吗？`, '提示', {
      type: 'warning',
    })
    await api.delete(`/api/discussions/admin/posts/${row.id}`)
    ElMessage.success('已删除')
    await load()
  } catch {
    /* cancel */
  }
}

onMounted(load)
</script>

<style scoped>
.ops {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
</style>
