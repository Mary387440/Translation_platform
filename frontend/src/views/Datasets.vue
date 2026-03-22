<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">数据集</h1>
        <p class="page-subtitle">
          术语库（CSV/TSV）、平行句（CSV/TSV/JSONL）、文档库（ZIP，内含 txt/md/docx/pdf）。
        </p>
      </div>
      <el-button type="primary" @click="openCreate">新建数据集</el-button>
    </div>

    <el-tabs v-model="activeKind" class="dataset-tabs">
      <el-tab-pane label="术语库" name="terminology" />
      <el-tab-pane label="平行句" name="parallel" />
      <el-tab-pane label="文档库" name="document" />
    </el-tabs>

    <el-table :data="filteredItems" stripe style="width: 100%">
      <el-table-column prop="name" label="名称" min-width="160" />
      <el-table-column prop="source_note" label="来源说明" min-width="140" show-overflow-tooltip />
      <el-table-column prop="languages" label="语种" width="120" show-overflow-tooltip />
      <el-table-column label="统计" min-width="200">
        <template #default="{ row }">
          <span class="stats-text">{{ formatStats(row.stats) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <div class="row-actions">
            <el-upload
              :show-file-list="false"
              :http-request="(opt) => onImport(opt, row)"
              :accept="acceptFor(row)"
            >
              <el-button size="small" type="primary">导入</el-button>
            </el-upload>
            <el-button
              v-if="row.kind === 'parallel'"
              size="small"
              link
              type="primary"
              @click="previewParallel(row)"
            >
              预览句对
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="createVisible" title="新建数据集" width="480px" destroy-on-close>
      <el-form :model="createForm" label-position="top">
        <el-form-item label="类型（当前页签）">
          <el-tag>{{ kindLabel(activeKind) }}</el-tag>
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="createForm.name" placeholder="如：TED 日中小句对" />
        </el-form-item>
        <el-form-item label="简介（可选）">
          <el-input v-model="createForm.description" type="textarea" rows="3" />
        </el-form-item>
        <el-form-item label="来源说明（可选，如论文中的「数据集介绍」）">
          <el-input v-model="createForm.source_note" placeholder="如：多语言 TED 平行语料" />
        </el-form-item>
        <el-form-item label="语种（可选）">
          <el-input v-model="createForm.languages" placeholder='如 ja,zh 或 ["ja","zh"]' />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="previewVisible" title="平行句预览（前 20 条）" width="720px">
      <el-table v-loading="previewLoading" :data="previewRows" size="small" max-height="400">
        <el-table-column prop="src_lang" label="源" width="70" />
        <el-table-column prop="tgt_lang" label="目标" width="70" />
        <el-table-column prop="src_text" label="原文" min-width="160" show-overflow-tooltip />
        <el-table-column prop="tgt_text" label="译文" min-width="160" show-overflow-tooltip />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../stores/auth'

const activeKind = ref('terminology')
const items = ref([])
const createVisible = ref(false)
const createLoading = ref(false)
const createForm = ref({
  name: '',
  description: '',
  source_note: '',
  languages: '',
})

const previewVisible = ref(false)
const previewLoading = ref(false)
const previewRows = ref([])

const filteredItems = computed(() =>
  items.value.filter((i) => i.kind === activeKind.value),
)

const kindLabel = (k) => {
  const m = { terminology: '术语库', parallel: '平行句', document: '文档库' }
  return m[k] || k
}

const formatStats = (stats) => {
  if (!stats || typeof stats !== 'object') return '—'
  const parts = []
  if (stats.terminology_total_entries != null) {
    parts.push(`术语 ${stats.terminology_total_entries} 条`)
  }
  if (stats.parallel_total_pairs != null) {
    parts.push(`句对 ${stats.parallel_total_pairs}`)
  }
  if (stats.document_total_docs != null) {
    parts.push(`文档 ${stats.document_total_docs}`)
  }
  return parts.length ? parts.join(' · ') : '暂无导入'
}

const load = async () => {
  try {
    const { data } = await api.get('/api/datasets')
    items.value = data.items || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载数据集失败，请先登录')
  }
}

onMounted(load)

const openCreate = () => {
  createForm.value = {
    name: '',
    description: '',
    source_note: '',
    languages: '',
  }
  createVisible.value = true
}

const submitCreate = async () => {
  if (!createForm.value.name?.trim()) {
    ElMessage.warning('请填写名称')
    return
  }
  createLoading.value = true
  try {
    await api.post('/api/datasets', {
      name: createForm.value.name.trim(),
      kind: activeKind.value,
      description: createForm.value.description || undefined,
      source_note: createForm.value.source_note || undefined,
      languages: createForm.value.languages || undefined,
    })
    ElMessage.success('创建成功')
    createVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '创建失败')
  } finally {
    createLoading.value = false
  }
}

const importUrl = (row) => {
  if (row.kind === 'terminology') return `/api/datasets/${row.id}/import/terminology`
  if (row.kind === 'parallel') return `/api/datasets/${row.id}/import/parallel`
  return `/api/datasets/${row.id}/import/documents`
}

const acceptFor = (row) => {
  if (row.kind === 'terminology') return '.csv,.tsv,text/csv,text/tab-separated-values'
  if (row.kind === 'parallel') return '.csv,.tsv,.jsonl'
  return '.zip,application/zip'
}

const onImport = async ({ file }, row) => {
  if (row.kind === 'document' && !file.name.toLowerCase().endsWith('.zip')) {
    ElMessage.warning('文档库请上传 .zip')
    return
  }
  const fd = new FormData()
  fd.append('file', file)
  try {
    const { data } = await api.post(importUrl(row), fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    ElMessage.success(data.message || '导入成功')
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '导入失败')
  }
}

const previewParallel = async (row) => {
  previewVisible.value = true
  previewLoading.value = true
  previewRows.value = []
  try {
    const { data } = await api.get(`/api/datasets/${row.id}/parallel-pairs`, {
      params: { limit: 20 },
    })
    previewRows.value = data.items || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载预览失败')
    previewVisible.value = false
  } finally {
    previewLoading.value = false
  }
}
</script>

<style scoped>
.dataset-tabs {
  margin-bottom: 12px;
}
.row-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.stats-text {
  font-size: 13px;
  color: #6b7280;
}
</style>
