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

    <div class="shelf-head">
      <h2>《鬼吹灯》书架</h2>
      <p>翻译演示：节选对照 + 泰文成品译文，可继续体验 AI 翻译。</p>
    </div>
    <div class="work-grid shelf-grid">
      <el-card class="work-card shelf-card" shadow="hover">
        <div class="card-body">
          <div class="cover" :style="coverStyle({ genre: '悬疑' })">
            <img
              v-if="!brokenCovers.guichuideng"
              class="cover-img"
              src="/covers/classics/guichuideng.jpg"
              alt="《鬼吹灯》"
              @error="onCoverError('guichuideng')"
            />
            <div v-else class="cover-inner">
              <div class="cover-title">鬼吹灯</div>
              <div class="cover-sub">翻译演示</div>
            </div>
          </div>
          <div class="card-info">
            <div class="card-head">
              <span class="title">《鬼吹灯》翻译演示（节选）</span>
              <el-tag size="small" class="tag">悬疑</el-tag>
            </div>
            <p class="meta">天下霸唱（节选） · zh</p>
            <p class="summary">已内置泰文译文（th），可直接进入阅读器查看对照与翻译依据。</p>
            <div class="card-actions">
              <el-button v-if="guichuidengReady" type="primary" link @click="goReadGuichuideng(guichuidengWork)"
                >进入演示</el-button
              >
              <el-button v-else type="primary" link :loading="seedingGuichuideng" @click="seedGuichuideng"
                >一键初始化</el-button
              >
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <div class="shelf-head">
      <h2>经典文学书架</h2>
    </div>
    <div class="shelf-toolbar">
      <el-input v-model="classicFilters.q" placeholder="搜经典书名/作者" clearable @keyup.enter="noop" />
    </div>
    <el-tabs v-model="classicFilters.l1" class="classic-tabs" @tab-change="onL1Change">
      <el-tab-pane v-for="c in classicLevel1" :key="c" :label="c" :name="c" />
    </el-tabs>
    <div class="shelf-toolbar">
      <el-select v-model="classicFilters.l2" placeholder="二级分类" clearable style="width: 260px">
        <el-option label="全部二级分类" value="" />
        <el-option v-for="c in classicLevel2" :key="c" :label="c" :value="c" />
      </el-select>
    </div>
    <div class="work-grid shelf-grid">
      <el-card v-for="b in filteredClassicBooks" :key="b.key" class="work-card shelf-card" shadow="hover">
        <div class="card-body">
          <div class="cover" :style="coverStyle(b)">
            <img
              v-if="b.cover && !brokenCovers[b.key]"
              class="cover-img"
              :src="b.cover"
              :alt="b.title"
              @error="onCoverError(b.key)"
            />
            <div v-else class="cover-inner">
              <div class="cover-title">{{ coverTitle(b.title) }}</div>
              <div class="cover-sub">{{ b.genre }}</div>
            </div>
          </div>
          <div class="card-info">
            <div class="card-head">
              <span class="title" :title="b.title">{{ b.title }}</span>
              <el-tag size="small" class="tag">{{ b.genre }}</el-tag>
            </div>
            <p class="meta">{{ b.author_name || '佚名' }} · {{ b.src_lang }}</p>
            <p class="summary">{{ b.summary || '经典文学书目，等待正文导入。' }}</p>
            <div class="card-actions">
              <el-button link @click="showcaseTip">查看详情</el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <div class="shelf-head">
      <h2>已上架可阅读作品</h2>
      <p>以下作品已发布并可直接进入章节阅读。</p>
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
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../../stores/auth'
import { CLASSIC_BOOKS, CLASSIC_LEVEL1, CLASSIC_LEVEL2_BY_L1 } from '../../data/classic_catalog'

const router = useRouter()
const items = ref([])
const loading = ref(false)
const seedingGuichuideng = ref(false)
const guichuidengWork = ref(null)
const filters = reactive({ q: '', genre: '' })
const brokenCovers = ref({})
const classicFilters = reactive({ q: '', l1: '全部', l2: '' })
const classicLevel1 = CLASSIC_LEVEL1

const classicLevel2 = computed(() => CLASSIC_LEVEL2_BY_L1[classicFilters.l1] || [])

const noop = () => {}

const showcaseBooks = CLASSIC_BOOKS.map((b) => ({
  ...b,
  src_lang: 'zh',
  genre: b.l1 === '小说类' ? '小说' : b.l1 === '近现代文学' ? '近现代' : '经典',
  cover: `/covers/classics/${b.key}.jpg`,
}))

const filteredClassicBooks = computed(() => {
  const q = (classicFilters.q || '').trim()
  const l1 = (classicFilters.l1 || '').trim()
  const l2 = (classicFilters.l2 || '').trim()
  const hit = (x) => {
    if (!q) return true
    const s = `${x.title || ''} ${x.author_name || ''} ${x.tags || ''}`
    return s.includes(q)
  }
  const priority = (x) => {
    // 小说类优先，其次近现代文学，其余按原顺序
    if (x.l1 === '小说类' && x.l2 === '近现代小说') return 0
    if (x.l1 === '小说类') return 1
    if (x.l1 === '近现代文学') return 2
    return 3
  }
  return showcaseBooks
    .filter((x) => (!l1 || l1 === '全部' || x.l1 === l1) && (!l2 || x.l2 === l2) && hit(x))
    .sort((a, b) => priority(a) - priority(b))
})

const onL1Change = () => {
  classicFilters.l2 = ''
}

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
    // 自动探测是否已存在“鬼吹灯演示”
    const hit = (items.value || []).find((x) => String(x?.title || '').includes('鬼吹灯') && x.chapter_count > 0)
    guichuidengWork.value = hit || null
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)

const onCoverError = (key) => {
  brokenCovers.value[key] = true
}

const showcaseTip = () => {
  ElMessage.info('该书目已入库：可先上传封面，后续再导入正文')
}

const guichuidengReady = computed(() => !!guichuidengWork.value?.id)

const seedGuichuideng = async () => {
  seedingGuichuideng.value = true
  try {
    const { data } = await api.post('/api/catalog/seed-demo-guichuideng')
    ElMessage.success(data?.message || '已初始化')
    await load()
    if (guichuidengWork.value) {
      await goRead(guichuidengWork.value)
    }
  } catch (e) {
    const status = e?.response?.status
    const msg = e?.response?.data?.message || e?.message
    if (status === 401) {
      ElMessage.error('登录已失效，请重新登录后再初始化')
      router.push('/login')
      return
    }
    ElMessage.error(status ? `初始化失败（${status}）：${msg || '请求失败'}` : `初始化失败：${msg || '请求失败'}`)
  } finally {
    seedingGuichuideng.value = false
  }
}

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

const goReadGuichuideng = async (w) => {
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
      query: { target_lang: 'th' },
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
.shelf-head {
  margin: 10px 0 10px;
}
.shelf-head h2 {
  margin: 0;
  font-size: 18px;
}
.shelf-head p {
  margin: 4px 0 0;
  font-size: 12px;
  opacity: 0.85;
}
.classic-tabs {
  margin: 8px 0 6px;
}
:deep(.classic-tabs .el-tabs__header) {
  margin: 0 0 8px;
}
:deep(.classic-tabs .el-tabs__nav-wrap::after) {
  display: none;
}
:deep(.classic-tabs .el-tabs__active-bar) {
  display: none;
}
:deep(.classic-tabs .el-tabs__nav) {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
:deep(.classic-tabs .el-tabs__item) {
  height: 34px;
  line-height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  border-radius: 999px;
  padding: 0 16px !important;
  border: 1px solid rgba(236, 170, 255, 0.28);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.9) !important;
  transition: all 0.2s ease;
}
:deep(.classic-tabs .el-tabs__item:first-child),
:deep(.classic-tabs .el-tabs__item:last-child) {
  padding: 0 16px !important;
}
:deep(.classic-tabs .el-tabs__item:hover) {
  color: #fff !important;
  transform: translateY(-1px);
  background: rgba(255, 94, 212, 0.16);
  box-shadow: 0 8px 22px rgba(255, 94, 212, 0.24);
}
:deep(.classic-tabs .el-tabs__item.is-active) {
  color: #fff !important;
  font-weight: 700;
  border-color: transparent;
  background: linear-gradient(135deg, rgba(255, 79, 216, 0.95), rgba(122, 88, 255, 0.9));
  box-shadow: 0 10px 24px rgba(255, 94, 212, 0.32);
}
.shelf-grid {
  margin-bottom: 18px;
}
.shelf-card {
  opacity: 0.98;
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
.cover-img {
  width: 100%;
  height: 100%;
  min-height: 120px;
  object-fit: cover;
  display: block;
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
