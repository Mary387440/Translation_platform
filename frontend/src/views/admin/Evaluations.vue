<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">评测中心</h1>
        <p class="page-subtitle">管理员发起评测任务，选择指标并生成翻译分数。</p>
      </div>
    </div>

    <el-card class="form-card">
      <el-form label-position="top">
        <div class="form-grid">
          <el-form-item label="任务名称">
            <el-input v-model="form.name" placeholder="如 TED-ja-zh 基线评测" />
          </el-form-item>
          <el-form-item label="平行句数据集">
            <el-select v-model="form.dataset_id" placeholder="请选择" style="width: 100%">
              <el-option
                v-for="d in parallelDatasets"
                :key="d.id"
                :label="`${d.name} (#${d.id})`"
                :value="d.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="源语言">
            <el-input v-model="form.src_lang" placeholder="zh / ja / ko ..." />
          </el-form-item>
          <el-form-item label="目标语言">
            <el-input v-model="form.tgt_lang" placeholder="en / zh / ..." />
          </el-form-item>
          <el-form-item label="样本数（1-100）">
            <el-input-number v-model="form.sample_size" :min="1" :max="100" />
          </el-form-item>
          <el-form-item label="指标（多选）">
            <el-checkbox-group v-model="form.metrics">
              <el-checkbox label="BLEU" />
              <el-checkbox label="ROUGE" />
              <el-checkbox label="METEOR" />
            </el-checkbox-group>
          </el-form-item>
        </div>
        <el-button type="primary" :loading="creating" @click="createTask">发起评测</el-button>
      </el-form>
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>历史任务</template>
      <el-table :data="tasks" v-loading="loading" size="small">
        <el-table-column prop="name" label="任务名" min-width="160" />
        <el-table-column prop="dataset_id" label="数据集ID" width="90" />
        <el-table-column prop="src_lang" label="源" width="70" />
        <el-table-column prop="tgt_lang" label="目标" width="70" />
        <el-table-column prop="sample_size" label="样本" width="80" />
        <el-table-column label="分数" min-width="280">
          <template #default="{ row }">
            <span v-if="row.result?.scores">
              BLEU {{ row.result.scores.BLEU ?? '-' }} /
              ROUGE {{ row.result.scores.ROUGE ?? '-' }} /
              METEOR {{ row.result.scores.METEOR ?? '-' }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../../stores/auth'

const loading = ref(false)
const creating = ref(false)
const parallelDatasets = ref([])
const tasks = ref([])

const form = reactive({
  name: '翻译评测任务',
  dataset_id: null,
  src_lang: 'zh',
  tgt_lang: 'en',
  sample_size: 30,
  metrics: ['BLEU', 'ROUGE', 'METEOR'],
})

const loadDatasets = async () => {
  const { data } = await api.get('/api/datasets')
  parallelDatasets.value = (data.items || []).filter((d) => d.kind === 'parallel')
  if (!form.dataset_id && parallelDatasets.value.length) {
    form.dataset_id = parallelDatasets.value[0].id
  }
}

const loadTasks = async () => {
  const { data } = await api.get('/api/evals')
  tasks.value = data.items || []
}

const loadAll = async () => {
  loading.value = true
  try {
    await Promise.all([loadDatasets(), loadTasks()])
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载评测数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)

const createTask = async () => {
  if (!form.dataset_id) {
    ElMessage.warning('请先选择平行句数据集')
    return
  }
  if (!form.metrics.length) {
    ElMessage.warning('请至少选择一个指标')
    return
  }
  creating.value = true
  try {
    await api.post('/api/evals', {
      name: form.name,
      dataset_id: form.dataset_id,
      src_lang: form.src_lang,
      tgt_lang: form.tgt_lang,
      sample_size: form.sample_size,
      metrics: form.metrics,
      engine: 'mock',
    })
    ElMessage.success('评测完成')
    await loadTasks()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '评测失败')
  } finally {
    creating.value = false
  }
}
</script>

<style scoped>
.form-card {
  margin-bottom: 8px;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(220px, 1fr));
  gap: 0 12px;
}
@media (max-width: 900px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>

