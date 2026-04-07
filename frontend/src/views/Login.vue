<template>
  <div class="login-shell">
    <div class="page login-page">
      <el-card class="login-card">
        <template #header>
          <span>{{ isRegister ? '注册账号' : '登录小语种翻译阅读平台' }}</span>
        </template>

        <!-- 登录 -->
        <el-form v-if="!isRegister" @submit.prevent="onLogin" :model="form" label-position="top">
          <el-form-item label="邮箱">
            <el-input v-model="form.email" placeholder="请输入邮箱，例如 name@example.com" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" style="width: 100%" :loading="loading" @click="onLogin">
              登录
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 注册 -->
        <el-form v-else @submit.prevent="onRegister" :model="regForm" label-position="top">
          <el-form-item label="邮箱">
            <el-input v-model="regForm.email" placeholder="用于登录，需为有效邮箱格式" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="regForm.password" type="password" placeholder="至少 6 位建议" show-password />
          </el-form-item>
          <el-form-item label="昵称（选填）">
            <el-input v-model="regForm.nickname" placeholder="显示名称" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" style="width: 100%" :loading="loading" @click="onRegister">
              注册并登录
            </el-button>
          </el-form-item>
        </el-form>

        <div class="form-footer">
          <template v-if="!isRegister">
            还没有账号？
            <el-button link type="primary" @click="isRegister = true">立即注册</el-button>
          </template>
          <template v-else>
            已有账号？
            <el-button link type="primary" @click="isRegister = false">返回登录</el-button>
          </template>
        </div>

        <p class="hint">
          新用户默认为读者；需要管理员权限时，请在数据库执行：
          <code>UPDATE users SET role='admin' WHERE email='你的邮箱';</code>
        </p>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore, api } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const isRegister = ref(false)
const loading = ref(false)

const form = reactive({
  email: '',
  password: '',
})

const regForm = reactive({
  email: '',
  password: '',
  nickname: '',
})

const afterAuthRedirect = () => {
  const redirect = route.query.redirect
  // 防止错误 redirect 把用户再次留在登录页
  if (redirect && typeof redirect === 'string' && !redirect.startsWith('/login')) {
    router.replace(redirect)
    return
  }
  if (auth.user?.role === 'admin') {
    router.replace('/admin/dashboard')
    return
  }
  router.replace('/books')
}

const onLogin = async () => {
  if (!form.email?.trim() || !form.password) {
    ElMessage.error('请输入邮箱和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(form.email.trim(), form.password)
    ElMessage.success('登录成功')
    afterAuthRedirect()
  } catch (err) {
    ElMessage.error(err?.response?.data?.message || '登录失败，请检查邮箱与密码，或先注册')
  } finally {
    loading.value = false
  }
}

const onRegister = async () => {
  const email = regForm.email?.trim().toLowerCase()
  if (!email || !regForm.password) {
    ElMessage.error('请填写邮箱和密码')
    return
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    ElMessage.warning('请使用正确的邮箱格式（例如 user@qq.com）')
    return
  }
  loading.value = true
  try {
    await api.post('/api/auth/register', {
      email,
      password: regForm.password,
      nickname: regForm.nickname?.trim() || undefined,
    })
    ElMessage.success('注册成功')
    await auth.login(email, regForm.password)
    ElMessage.success('已自动登录')
    afterAuthRedirect()
  } catch (err) {
    ElMessage.error(err?.response?.data?.message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-shell {
  min-height: 100vh;
  background: linear-gradient(160deg, #f5f7fb 0%, #e0e7ff 100%);
}
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
}

.login-card {
  width: 400px;
  max-width: 100%;
}

.form-footer {
  text-align: center;
  font-size: 14px;
  color: #6b7280;
  margin-top: 8px;
}

.hint {
  margin: 16px 0 0;
  font-size: 12px;
  color: #9ca3af;
  line-height: 1.5;
}
.hint code {
  display: block;
  margin-top: 6px;
  font-size: 11px;
  word-break: break-all;
  background: #f3f4f6;
  padding: 8px;
  border-radius: 4px;
}
</style>
