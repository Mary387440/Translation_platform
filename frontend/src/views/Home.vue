<template>
  <div class="home">
    <div class="hero">
      <div class="hero-deco">
        <div class="stars" />
        <div class="diamond d1" />
        <div class="diamond d2" />
        <div class="line l1" />
        <div class="line l2" />
      </div>

      <div class="hero-grid">
        <div class="hero-left">
          <div class="kicker">SailoAI · 文学翻译阅读</div>
          <h1 class="hero-title">
            欢迎来到 <span class="brand">SailoAI</span>！
          </h1>
          <p class="hero-subtitle">用 AI 赋能文学翻译，让经典跨越山海</p>

          <div class="hero-actions">
            <el-button type="primary" size="large" @click="$router.push('/books')">进入书库</el-button>
            <el-button size="large" class="ghost" @click="$router.push('/discussions')">进入讨论区</el-button>
          </div>

          <div class="stats">
            <div class="stat">
              <div class="num">50M+</div>
              <div class="label">累计翻译字数</div>
            </div>
            <div class="stat">
              <div class="num">350K+</div>
              <div class="label">服务用户</div>
            </div>
            <div class="stat">
              <div class="num">100+</div>
              <div class="label">支持语种</div>
            </div>
          </div>

          <div class="logos">
            <div class="logo-item" title="DeepSeek">DeepSeek</div>
            <div class="logo-item" title="Baidu">Baidu</div>
            <div class="logo-item" title="Ethereum">Ethereum</div>
            <div class="logo-item" title="Web3">Web3</div>
          </div>
        </div>

        <div class="hero-right" aria-hidden="true">
          <div class="illus-wrap" :style="{ transform: illusTransform }">
            <svg class="illus" viewBox="0 0 520 420" fill="none" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="g1" x1="0" y1="0" x2="520" y2="420" gradientUnits="userSpaceOnUse">
                  <stop stop-color="#FF4FD8" stop-opacity="0.9" />
                  <stop offset="0.5" stop-color="#7A58FF" stop-opacity="0.85" />
                  <stop offset="1" stop-color="#2DD4FF" stop-opacity="0.35" />
                </linearGradient>
                <filter id="blur" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="12" />
                </filter>
              </defs>
              <!-- glow bubble -->
              <circle cx="330" cy="170" r="120" fill="url(#g1)" filter="url(#blur)" opacity="0.65" />
              <!-- swallows (stylized) -->
              <path
                d="M160 260c38-8 62-36 92-70 18-20 44-45 80-54 36-9 68 3 98 28-30-10-58-8-84 8-26 16-44 40-62 62-28 35-58 71-124 86Z"
                fill="url(#g1)"
                opacity="0.85"
              />
              <path
                d="M170 266c-12 24-34 44-70 60 4-20 14-40 30-58 14-16 26-28 40-38 6 10 6 22 0 36Z"
                fill="url(#g1)"
                opacity="0.65"
              />
              <!-- oriental line -->
              <path
                d="M90 322c84-28 156-30 216-6 64 26 120 26 170 0"
                stroke="rgba(255,255,255,0.35)"
                stroke-width="2"
              />
              <path
                d="M94 326c84-28 156-30 216-6 64 26 120 26 170 0"
                stroke="rgba(255,79,216,0.38)"
                stroke-width="1"
              />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-head">
        <h2 class="section-title">核心能力</h2>
        <p class="section-sub">对照阅读、AI 翻译、社区讨论与收藏管理。</p>
      </div>
      <div class="feature-grid">
        <div class="feature-card" @click="$router.push('/books')">
          <div class="icon">📚</div>
          <div class="name">多语种对照阅读</div>
          <div class="desc">在书库中阅读章节，句段对照更清晰。</div>
        </div>
        <div class="feature-card" @click="$router.push('/books')">
          <div class="icon">✨</div>
          <div class="name">AI 智能翻译润色</div>
          <div class="desc">支持 RAG 依据展示，翻译更透明。</div>
        </div>
        <div class="feature-card" @click="$router.push('/discussions')">
          <div class="icon">💬</div>
          <div class="name">文学社区讨论</div>
          <div class="desc">交流译法、讨论作品、互助排错。</div>
        </div>
        <div class="feature-card" @click="$router.push('/favorites')">
          <div class="icon">⭐</div>
          <div class="name">个人收藏管理</div>
          <div class="desc">收集喜欢的段落与译文，持续迭代。</div>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-head">
        <h2 class="section-title">热门书籍推荐</h2>
        <p class="section-sub">从经典开始，快速体验对照阅读。</p>
      </div>
      <div class="recommend-grid">
        <el-card v-for="w in hotWorks" :key="w.id" class="recommend-card" shadow="hover">
          <div class="recommend-body">
            <div class="mini-cover" :style="coverStyle(w)">
              <div class="mini-title">{{ shortTitle(w.title) }}</div>
              <div class="mini-tag">{{ w.genre }}</div>
            </div>
            <div class="recommend-info">
              <div class="recommend-head">
                <div class="t" :title="w.title">{{ w.title }}</div>
                <el-tag size="small">{{ w.genre }}</el-tag>
              </div>
              <div class="m">
                {{ w.author_name || '佚名' }} · {{ w.src_lang }}
                <span v-if="w.chapter_count != null"> · {{ w.chapter_count }} 章</span>
              </div>
              <div class="s">{{ w.summary || '暂无简介' }}</div>
              <div class="a">
                <el-button type="primary" link @click="goRead(w)">立即阅读</el-button>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <div class="section">
      <div class="section-head">
        <h2 class="section-title">社区热门讨论</h2>
        <p class="section-sub">看看大家都在聊什么。</p>
      </div>
      <div class="hot-discussions">
        <el-card v-for="p in hotPosts" :key="p.id" class="hot-post" shadow="hover" @click="goPost(p.id)">
          <div class="hp-head">
            <div class="hp-title">{{ p.title }}</div>
            <el-tag size="small">{{ p.category }}</el-tag>
          </div>
          <div class="hp-summary">{{ p.summary }}</div>
          <div class="hp-meta">
            <span>{{ p.author_name }}</span>
            <span>赞 {{ p.likes || 0 }}</span>
            <span>评 {{ p.comment_count || 0 }}</span>
          </div>
        </el-card>
        <el-empty v-if="!loading && hotPosts.length === 0" description="暂无帖子" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../stores/auth'

const router = useRouter()
const loading = ref(false)
const hotWorks = ref([])
const hotPosts = ref([])

const scrollY = ref(0)
const onScroll = () => {
  scrollY.value = window.scrollY || 0
}
const illusTransform = computed(() => {
  const y = Math.min(36, scrollY.value * 0.06)
  const x = Math.sin(scrollY.value / 240) * 6
  return `translate3d(${x}px, ${y}px, 0)`
})

const shortTitle = (t) => {
  const s = String(t || '').trim()
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
  return { background: `linear-gradient(135deg, ${a} 0%, ${b} 100%)` }
}

const goRead = async (w) => {
  try {
    const { data } = await api.get(`/api/catalog/works/${w.id}/chapters`)
    const first = data.items?.[0]
    if (!first) return ElMessage.info('本书暂无章节')
    router.push({ name: 'ReaderWorkReader', params: { workId: String(w.id), chapterId: String(first.id) } })
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '无法打开')
  }
}

const goPost = (id) => router.push(`/discussions/${id}`)

const load = async () => {
  loading.value = true
  try {
    const [worksRes, postsRes] = await Promise.all([
      api.get('/api/catalog/works'),
      api.get('/api/discussions', { params: { category: undefined } }),
    ])
    hotWorks.value = (worksRes.data.items || []).slice(0, 4)
    hotPosts.value = (postsRes.data.items || []).slice(0, 4)
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载首页数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
  load()
})
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<style scoped>
.home {
  padding: 0 4px 40px;
}

.hero {
  position: relative;
  border-radius: 22px;
  overflow: hidden;
  margin-bottom: 18px;
  border: 1px solid rgba(255, 196, 255, 0.18);
  background:
    radial-gradient(800px 500px at 20% 20%, rgba(255, 79, 216, 0.18), transparent 55%),
    radial-gradient(700px 520px at 80% 12%, rgba(122, 88, 255, 0.22), transparent 60%),
    linear-gradient(145deg, rgba(15, 8, 36, 0.65), rgba(32, 16, 74, 0.35));
}

.hero-deco {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.stars {
  position: absolute;
  inset: -20%;
  background-image:
    radial-gradient(circle at 12% 18%, rgba(255, 255, 255, 0.55) 0 1px, transparent 2px),
    radial-gradient(circle at 32% 68%, rgba(255, 255, 255, 0.35) 0 1px, transparent 2px),
    radial-gradient(circle at 72% 38%, rgba(255, 255, 255, 0.45) 0 1px, transparent 2px),
    radial-gradient(circle at 82% 78%, rgba(255, 255, 255, 0.25) 0 1px, transparent 2px);
  background-size: 220px 180px;
  opacity: 0.35;
  filter: blur(0.2px);
  animation: twinkle 10s ease-in-out infinite;
}

@keyframes twinkle {
  0% { opacity: 0.28; transform: translate3d(0,0,0); }
  50% { opacity: 0.42; transform: translate3d(8px, -6px, 0); }
  100% { opacity: 0.28; transform: translate3d(0,0,0); }
}

.diamond {
  position: absolute;
  width: 120px;
  height: 120px;
  transform: rotate(45deg);
  border: 1px solid rgba(255, 79, 216, 0.22);
  background: rgba(255, 255, 255, 0.03);
  box-shadow: 0 0 26px rgba(255, 79, 216, 0.12);
}
.d1 { top: 26px; right: 160px; }
.d2 { bottom: 26px; left: 110px; width: 90px; height: 90px; border-color: rgba(122,88,255,0.22); }

.line {
  position: absolute;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 79, 216, 0.35), transparent);
}
.l1 { top: 86px; left: 0; right: 0; }
.l2 { bottom: 86px; left: 0; right: 0; background: linear-gradient(90deg, transparent, rgba(122, 88, 255, 0.35), transparent); }

.hero-grid {
  position: relative;
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 10px;
  padding: 22px;
}

.kicker {
  color: rgba(255, 255, 255, 0.65);
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}
.hero-title {
  margin: 10px 0 0;
  font-size: 44px;
  line-height: 1.05;
  font-weight: 900;
}
.brand {
  background: linear-gradient(135deg, #ff4fd8, #a559ff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.hero-subtitle {
  margin: 12px 0 0;
  color: rgba(255, 255, 255, 0.78);
  font-size: 15px;
  line-height: 1.7;
}

.hero-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}
.ghost {
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid rgba(255, 201, 255, 0.28) !important;
}

.stats {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.stat {
  padding: 10px 12px;
  border: 1px solid rgba(255, 201, 255, 0.18);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
}
.num {
  font-weight: 900;
  font-size: 20px;
  color: #ff7be6;
}
.label {
  margin-top: 2px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
}

.logos {
  margin-top: 14px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.logo-item {
  padding: 8px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255, 201, 255, 0.18);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.logo-item:hover {
  transform: translateY(-1px) scale(1.03);
  box-shadow: 0 0 20px rgba(255, 93, 212, 0.2);
}

.hero-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  gap: 10px;
}
.illus-wrap {
  width: min(520px, 100%);
  padding: 12px 12px 6px;
  border-radius: 18px;
  border: 1px solid rgba(255, 201, 255, 0.18);
  background: rgba(255, 255, 255, 0.04);
  box-shadow: 0 18px 50px rgba(10, 6, 24, 0.35);
  transition: transform 0.2s ease;
  animation: floaty 6.5s ease-in-out infinite;
}
@keyframes floaty {
  0% { transform: translate3d(0, 0, 0); }
  50% { transform: translate3d(0, -10px, 0); }
  100% { transform: translate3d(0, 0, 0); }
}
.illus {
  width: 100%;
  height: auto;
  display: block;
}
.illus-caption {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
  text-align: right;
}
.pager {
  padding: 8px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255, 201, 255, 0.18);
  background: rgba(255, 255, 255, 0.04);
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
}

.section {
  margin-top: 18px;
}
.section-head {
  margin-bottom: 12px;
}
.section-title {
  margin: 0;
  font-size: 22px;
  font-weight: 900;
}
.section-sub {
  margin: 6px 0 0;
  color: rgba(255, 255, 255, 0.72);
  font-size: 13px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}
.feature-card {
  padding: 14px 14px 12px;
  border: 1px solid rgba(255, 201, 255, 0.18);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}
.feature-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 18px 50px rgba(10, 6, 24, 0.35);
  background: rgba(255, 255, 255, 0.06);
}
.icon {
  font-size: 18px;
}
.name {
  margin-top: 8px;
  font-weight: 900;
  color: #fff;
}
.desc {
  margin-top: 6px;
  color: rgba(255, 255, 255, 0.75);
  font-size: 13px;
  line-height: 1.6;
}

.recommend-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.recommend-body {
  display: grid;
  grid-template-columns: 90px 1fr;
  gap: 12px;
}
.mini-cover {
  border-radius: 14px;
  min-height: 118px;
  overflow: hidden;
  position: relative;
  padding: 10px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.25);
}
.mini-title {
  font-weight: 900;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.25);
}
.mini-tag {
  position: absolute;
  bottom: 10px;
  left: 10px;
  font-size: 12px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}
.recommend-info {
  min-width: 0;
}
.recommend-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}
.t {
  font-weight: 900;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.m {
  margin-top: 8px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
}
.s {
  margin-top: 6px;
  color: rgba(255, 255, 255, 0.78);
  font-size: 13px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 40px;
}
.a {
  margin-top: 8px;
  text-align: right;
}

.hot-discussions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.hot-post {
  cursor: pointer;
  transition: transform 0.2s ease;
}
.hot-post:hover {
  transform: translateY(-2px);
}
.hp-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}
.hp-title {
  font-weight: 900;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.hp-summary {
  margin-top: 8px;
  color: rgba(255, 255, 255, 0.76);
  font-size: 13px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 40px;
}
.hp-meta {
  margin-top: 8px;
  display: flex;
  gap: 12px;
  color: rgba(255, 255, 255, 0.65);
  font-size: 12px;
}

@media (max-width: 1100px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }
  .hero-right {
    align-items: stretch;
  }
}
@media (max-width: 900px) {
  .feature-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .recommend-grid,
  .hot-discussions {
    grid-template-columns: 1fr;
  }
  .hero-title {
    font-size: 36px;
  }
}
</style>
