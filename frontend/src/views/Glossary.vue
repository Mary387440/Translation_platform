<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">术语库</h1>
        <p class="page-subtitle">术语在句段翻译时作为 RAG 提示注入，与数据集导入的术语表一致。</p>
      </div>
      <el-input
        v-model="q"
        placeholder="搜索源词/译文"
        clearable
        style="max-width: 260px"
        @clear="load"
        @keyup.enter="load"
      />
    </div>

    <el-table v-loading="loading" :data="items" stripe>
      <el-table-column prop="src_lang" label="源" width="70" />
      <el-table-column prop="tgt_lang" label="目标" width="70" />
      <el-table-column prop="src_text" label="术语/原文" min-width="160" show-overflow-tooltip />
      <el-table-column prop="tgt_text" label="译文" min-width="160" show-overflow-tooltip />
      <el-table-column prop="note" label="备注" width="120" show-overflow-tooltip />
    </el-table>
    <el-pagination
      v-model:current-page="page"
      :page-size="perPage"
      :total="total"
      layout="total, prev, pager, next"
      style="margin-top: 16px; justify-content: center"
      @current-change="onPage"
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../stores/auth'

const items = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 20
const q = ref('')
const loading = ref(false)

const load = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/api/glossary/entries', {
      params: { q: q.value || undefined, page: page.value, per_page: perPage },
    })
    items.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

const onPage = () => {
  load()
}

onMounted(load)
</script>
