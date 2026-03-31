<template>
  <el-container style="height: 100vh">
    <el-aside width="200px">
      <div class="brand reader-brand">SailoAI</div>
      <el-menu router :default-active="activePath">
        <el-menu-item index="/books">
          <span>书库</span>
        </el-menu-item>
        <el-menu-item index="/favorites">
          <span>收藏</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <span>我的设置</span>
        </el-menu-item>
        <el-menu-item index="/discussions">
          <span>讨论区</span>
        </el-menu-item>
      </el-menu>
      <div class="aside-foot">
        <el-button v-if="isAdmin" link type="primary" @click="$router.push('/admin')">
          进入管理后台
        </el-button>
      </div>
    </el-aside>
    <el-container>
      <el-header height="56px">
        <div class="app-title">
          <span>文学阅读</span>
          <span class="app-subtitle">多语种对照</span>
        </div>
        <div class="app-header-right">
          <el-tag v-if="user?.nickname" size="small" type="info">{{ user.nickname }}</el-tag>
          <el-button size="small" @click="logout">退出</el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const user = computed(() => auth.user)
const isAdmin = computed(() => auth.user?.role === 'admin')
const activePath = computed(() => {
  const p = route.path
  if (p.startsWith('/books')) return '/books'
  if (p.startsWith('/favorites')) return '/favorites'
  if (p.startsWith('/settings')) return '/settings'
  if (p.startsWith('/discussions')) return '/discussions'
  return '/books'
})

const logout = () => {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.reader-brand {
  padding: 16px;
  font-weight: 700;
  color: #e5e7eb;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.aside-foot {
  padding: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}
</style>
