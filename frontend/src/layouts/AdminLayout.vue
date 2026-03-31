<template>
  <el-container style="height: 100vh">
    <el-aside width="220px">
      <div class="brand admin-brand">管理后台</div>
      <el-menu router :default-active="activePath">
        <el-menu-item index="/admin/dashboard">
          <span>控制台</span>
        </el-menu-item>
        <el-menu-item index="/admin/works">
          <span>书稿与章节</span>
        </el-menu-item>
        <el-menu-item index="/admin/datasets">
          <span>数据集</span>
        </el-menu-item>
        <el-menu-item index="/admin/glossary">
          <span>术语库</span>
        </el-menu-item>
        <el-menu-item index="/admin/docs">
          <span>文档库</span>
        </el-menu-item>
        <el-menu-item index="/admin/ocr">
          <span>场景 OCR</span>
        </el-menu-item>
        <el-menu-item index="/admin/evals">
          <span>评测中心</span>
        </el-menu-item>
        <el-menu-item index="/admin/discussions">
          <span>讨论区管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/settings">
          <span>账号设置</span>
        </el-menu-item>
      </el-menu>
      <div class="aside-foot">
        <el-button link type="primary" @click="$router.push('/books')">读者端书库</el-button>
      </div>
    </el-aside>
    <el-container>
      <el-header height="56px">
        <div class="app-title">
          <span>SailoAI 运营</span>
          <span class="app-subtitle">语料 · 术语 · 内容</span>
        </div>
        <div class="app-header-right">
          <el-tag size="small" type="warning">管理员</el-tag>
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
const activePath = computed(() => {
  const p = route.path
  if (p.startsWith('/admin/works')) return '/admin/works'
  if (p.startsWith('/admin/docs')) return '/admin/docs'
  if (p.startsWith('/admin/datasets')) return '/admin/datasets'
  if (p.startsWith('/admin/glossary')) return '/admin/glossary'
  if (p.startsWith('/admin/ocr')) return '/admin/ocr'
  if (p.startsWith('/admin/evals')) return '/admin/evals'
  if (p.startsWith('/admin/discussions')) return '/admin/discussions'
  if (p.startsWith('/admin/settings')) return '/admin/settings'
  if (p.startsWith('/admin/dashboard')) return '/admin/dashboard'
  return '/admin/dashboard'
})

const logout = () => {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-brand {
  padding: 16px;
  font-weight: 700;
  color: #fde68a;
  background: #1c1917;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.aside-foot {
  padding: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}
</style>
