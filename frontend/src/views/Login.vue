<template>
  <div class="login-bg">
    <el-card class="login-card" shadow="always">
      <div class="brand">
        <h2>{{ appName }}</h2>
        <p>登录后访问业务模块</p>
      </div>
      <el-tabs v-model="tab">
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" label-width="0" @submit.prevent="onLogin">
            <el-form-item>
              <el-input v-model="loginForm.username" placeholder="用户名" :prefix-icon="User" />
            </el-form-item>
            <el-form-item>
              <el-input
                v-model="loginForm.password"
                type="password"
                show-password
                placeholder="密码"
                :prefix-icon="Lock"
                @keyup.enter="onLogin"
              />
            </el-form-item>
            <el-button type="primary" :loading="loading" style="width: 100%" @click="onLogin">
              登录
            </el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form :model="registerForm" label-width="0" @submit.prevent="onRegister">
            <el-form-item>
              <el-input v-model="registerForm.username" placeholder="用户名" :prefix-icon="User" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="registerForm.full_name" placeholder="姓名（可选）" />
            </el-form-item>
            <el-form-item>
              <el-input
                v-model="registerForm.password"
                type="password"
                show-password
                placeholder="密码"
                :prefix-icon="Lock"
              />
            </el-form-item>
            <el-button type="primary" :loading="loading" style="width: 100%" @click="onRegister">
              注册
            </el-button>
          </el-form>
          <p class="hint">注册的账号默认为普通用户角色。</p>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { authApi, configApi } from '../api'
import { auth } from '../store/auth'

const appName = ref('AI 项目管理系统')

onMounted(async () => {
  try {
    const { data } = await configApi.get()
    const firstLine = (data.about_content || '').split('\n')[0].trim()
    if (firstLine) appName.value = firstLine
  } catch { /* 非阻塞，保留默认标题 */ }
})

const router = useRouter()
const route = useRoute()
const tab = ref('login')
const loading = ref(false)

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', password: '', full_name: '' })

async function onLogin() {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const { data } = await authApi.login(loginForm)
    auth.setSession(data.access_token, data.user)
    ElMessage.success(`欢迎，${data.user.full_name || data.user.username}`)
    const target = route.query.redirect || '/intro'
    router.replace(target)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

async function onRegister() {
  if (!registerForm.username || !registerForm.password) {
    ElMessage.warning('用户名和密码必填')
    return
  }
  loading.value = true
  try {
    await authApi.register(registerForm)
    ElMessage.success('注册成功，请登录')
    tab.value = 'login'
    loginForm.username = registerForm.username
    loginForm.password = ''
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-bg {
  height: 100vh;
  background: linear-gradient(135deg, #1f2d3d 0%, #2d4a6b 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-card {
  width: 400px;
  padding: 8px;
}
.brand {
  text-align: center;
  margin-bottom: 16px;
}
.brand h2 {
  margin: 0 0 4px 0;
}
.brand p {
  margin: 0;
  color: #909399;
  font-size: 13px;
}
.hint {
  font-size: 12px;
  color: #909399;
  text-align: center;
  margin: 12px 0 0 0;
}
</style>
