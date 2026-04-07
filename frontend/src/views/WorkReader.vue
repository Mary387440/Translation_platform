<template>
  <div class="page reader-page">
    <div class="page-header">
      <div>
        <el-button link type="primary" @click="goBack">← {{ isReader ? '返回书库' : '返回书稿' }}</el-button>
        <h1 class="page-title">{{ work?.title || '阅读' }}</h1>
        <p class="page-subtitle">{{ work?.author_name }} · {{ chapterTitle }}</p>
      </div>
      <div class="page-actions reader-tools">
        <el-select v-model="targetLang" placeholder="目标语种" style="width: 130px" @change="reloadSegments">
          <el-option label="English" value="en" />
          <el-option label="日本語" value="ja" />
          <el-option label="한국어" value="ko" />
          <el-option label="Español" value="es" />
          <el-option label="Français" value="fr" />
          <el-option label="Deutsch" value="de" />
          <el-option label="ไทย" value="th" />
        </el-select>
        <el-switch v-model="useRag" active-text="RAG" />
      </div>
    </div>

    <el-skeleton v-if="loading" rows="6" animated />
    <div v-else class="segment-list">
      <div v-for="row in segments" :key="row.id" class="segment-row">
        <el-card shadow="never" class="src-card">
          <div class="seg-label">原文</div>
          <p class="seg-text">{{ row.content }}</p>
        </el-card>
        <el-card shadow="never" class="tgt-card">
          <div class="seg-label">译文 · {{ targetLang }}</div>
          <p v-if="row.translation" class="seg-text translated">{{ row.translation.text }}</p>
          <p v-else class="placeholder">点击右侧按钮生成 AI 译文</p>
          <div class="seg-actions">
            <el-button size="small" type="primary" :loading="row._loading" @click="doTranslate(row)">
              AI 翻译
            </el-button>
            <el-button
              v-if="row.translation && !isReader"
              size="small"
              @click="openPolish(row)"
            >
              人工润色
            </el-button>
            <el-button
              v-if="row.translation"
              size="small"
              link
              @click="openFeedback(row)"
            >
              反馈
            </el-button>
          </div>
          <div v-if="row.translation" class="meta">
            引擎 {{ row.translation.engine }} ·
            {{ row.translation.status === 'human_polished' ? '已润色' : 'AI 草稿' }}
          </div>

          <el-collapse
            v-if="row.translation && row.translation.rag && (row.translation.rag.glossary_block || row.translation.rag.parallel_block)"
            class="rag-collapse"
          >
            <el-collapse-item name="rag">
              <template #title>
                翻译依据（术语/平行句）
              </template>
              <div class="rag-box">
                <div v-if="row.translation.rag.glossary_block" class="rag-section">
                  <div class="rag-title">术语命中</div>
                  <pre class="rag-pre">{{ row.translation.rag.glossary_block }}</pre>
                </div>
                <div v-if="row.translation.rag.parallel_block" class="rag-section">
                  <div class="rag-title">平行句参考</div>
                  <pre class="rag-pre">{{ row.translation.rag.parallel_block }}</pre>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </div>
    </div>

    <el-dialog v-model="polishVisible" title="人工润色" width="560px">
      <el-input v-model="polishText" type="textarea" rows="8" />
      <template #footer>
        <el-button @click="polishVisible = false">取消</el-button>
        <el-button type="primary" @click="savePolish">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="fbVisible" title="翻译反馈" width="400px">
      <el-rate v-model="fbRating" />
      <el-input v-model="fbComment" type="textarea" rows="3" placeholder="选填意见" style="margin-top: 12px" />
      <template #footer>
        <el-button @click="fbVisible = false">取消</el-button>
        <el-button type="primary" @click="sendFeedback">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const workId = computed(() => route.params.workId)
const chapterId = computed(() => route.params.chapterId)
const isReader = computed(() => route.meta.mode === 'reader')
const apiBase = computed(() => (isReader.value ? '/api/catalog' : '/api/works'))

const goBack = () => {
  router.push(isReader.value ? '/books' : '/admin/works')
}

const work = ref(null)
const chapterTitle = ref('')
const segments = ref([])
const loading = ref(true)
const targetLang = ref('en')
const useRag = ref(true)

const polishVisible = ref(false)
const polishText = ref('')
const polishTarget = ref(null)

const fbVisible = ref(false)
const fbRating = ref(5)
const fbComment = ref('')
const fbTarget = ref(null)

const loadWork = async () => {
  const { data } = await api.get(`${apiBase.value}/works/${workId.value}`)
  work.value = data
}

const reloadSegments = async () => {
  const { data } = await api.get(
    `${apiBase.value}/works/${workId.value}/chapters/${chapterId.value}/segments`,
    { params: { target_lang: targetLang.value } },
  )
  segments.value = (data.items || []).map((s) => ({ ...s, _loading: false }))
}

onMounted(async () => {
  try {
    try {
      const { data: me } = await api.get('/api/auth/me')
      if (me.preferred_tgt_lang) targetLang.value = me.preferred_tgt_lang
    } catch {
      /* 未登录等 */
    }
    // 路由 query 优先（用于演示：点开即对比）
    if (route.query?.target_lang) targetLang.value = String(route.query.target_lang)
    await loadWork()
    const { data: ch } = await api.get(`${apiBase.value}/works/${workId.value}/chapters`)
    const cur = ch.items?.find((c) => String(c.id) === String(chapterId.value))
    chapterTitle.value = cur?.title || ''
    await reloadSegments()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
  }
})

const doTranslate = async (row) => {
  row._loading = true
  try {
    // 读者模式：若当前是 AI 草稿，再点一次 AI 翻译则回退到初始译文
    if (isReader.value && row.translation && row.translation.status === 'ai_draft') {
      await api.delete(`${apiBase.value}/segments/${row.id}/my-translation`, {
        params: { target_lang: targetLang.value },
      })
      await reloadSegments()
      ElMessage.success('已恢复到之前译文')
      return
    }
    const { data } = await api.post(`${apiBase.value}/segments/${row.id}/translate`, {
      target_lang: targetLang.value,
      use_rag: useRag.value,
    })
    // 直接更新当前卡片，保证“翻译依据”不会因 reload 而丢失
    row.translation = {
      id: data.translation_id,
      text: data.translated_text,
      status: data.status,
      engine: data.engine,
      rag: data.rag || { glossary_block: '', parallel_block: '' },
    }
    ElMessage.success('已生成译文')
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '翻译失败')
  } finally {
    row._loading = false
  }
}

const openPolish = (row) => {
  polishTarget.value = row
  polishText.value = row.translation?.text || ''
  polishVisible.value = true
}

const savePolish = async () => {
  if (!polishTarget.value?.translation) return
  try {
    await api.put(`/api/works/translations/${polishTarget.value.translation.id}/polish`, {
      translated_text: polishText.value,
    })
    ElMessage.success('已保存')
    polishVisible.value = false
    await reloadSegments()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
  }
}

const openFeedback = (row) => {
  fbTarget.value = row
  fbRating.value = 5
  fbComment.value = ''
  fbVisible.value = true
}

const sendFeedback = async () => {
  if (!fbTarget.value?.translation) return
  try {
    await api.post(`${apiBase.value}/translations/${fbTarget.value.translation.id}/feedback`, {
      rating: fbRating.value,
      comment: fbComment.value,
    })
    ElMessage.success('感谢反馈')
    fbVisible.value = false
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '提交失败')
  }
}
</script>

<style scoped>
.reader-page .reader-tools {
  align-items: center;
}
.segment-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.segment-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
@media (max-width: 900px) {
  .segment-row {
    grid-template-columns: 1fr;
  }
}
.seg-label {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 8px;
}
.seg-text {
  margin: 0;
  line-height: 1.7;
  white-space: pre-wrap;
}
.seg-text.translated {
  color: #1d4ed8;
}
.placeholder {
  color: #9ca3af;
  font-size: 13px;
}
.seg-actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.meta {
  margin-top: 8px;
  font-size: 12px;
  color: #6b7280;
}
.src-card {
  border-left: 3px solid #101827;
}
.tgt-card {
  border-left: 3px solid #3b82f6;
}

.rag-collapse {
  margin-top: 10px;
}

.rag-box {
  padding: 0 8px 6px;
}

.rag-section + .rag-section {
  margin-top: 10px;
}

.rag-title {
  font-size: 12px;
  color: #6b7280;
  margin: 6px 0;
  font-weight: 600;
}

.rag-pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono',
    'Courier New', monospace;
  font-size: 12px;
  line-height: 1.55;
}
</style>
