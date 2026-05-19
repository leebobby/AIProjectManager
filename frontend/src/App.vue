<template>
  <router-view v-if="route.meta.layout === 'blank'" />

  <el-container v-else class="app-root">
    <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="app-aside">
      <div class="app-logo" :class="{ collapsed: sidebarCollapsed }">
        {{ sidebarCollapsed ? '岳' : '岳麓山管理系统' }}
      </div>
      <el-menu
        :default-active="route.path"
        :collapse="sidebarCollapsed"
        :collapse-transition="false"
        router
        background-color="#1f2d3d"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item v-for="r in menuRoutes" :key="r.path" :index="r.path">
          <el-icon><component :is="r.meta.icon" /></el-icon>
          <template #title>{{ r.meta.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <el-button text class="collapse-btn" :title="sidebarCollapsed ? '展开侧栏' : '收起侧栏'" @click="toggleSidebar">
            <el-icon><component :is="sidebarCollapsed ? Expand : Fold" /></el-icon>
          </el-button>
          <span class="page-title">{{ currentTitle }}</span>
        </div>
        <div class="header-right">
          <el-dropdown @command="onCommand">
            <span class="user-trigger">
              <el-icon><Avatar /></el-icon>
              <span>{{ auth.state.user?.full_name || auth.state.user?.username }}</span>
              <el-tag v-if="auth.isAdmin.value" size="small" type="danger" effect="dark">admin</el-tag>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="changePassword">
                  <el-icon><Lock /></el-icon> 修改密码
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>

  <el-dialog v-model="pwdVisible" title="修改密码" width="420px" :close-on-click-modal="false">
    <el-form :model="pwdForm" label-width="100px" @keyup.enter="onSubmitPwd">
      <el-form-item label="原密码">
        <el-input v-model="pwdForm.old_password" type="password" show-password autocomplete="current-password" />
      </el-form-item>
      <el-form-item label="新密码">
        <el-input v-model="pwdForm.new_password" type="password" show-password autocomplete="new-password" placeholder="至少 6 位" />
      </el-form-item>
      <el-form-item label="确认新密码">
        <el-input v-model="pwdForm.confirm" type="password" show-password autocomplete="new-password" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="pwdVisible = false">取消</el-button>
      <el-button type="primary" :loading="pwdLoading" @click="onSubmitPwd">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Expand, Fold } from '@element-plus/icons-vue'
import { authApi } from './api'
import { auth } from './store/auth'

const sidebarCollapsed = ref(localStorage.getItem('sidebarCollapsed') === '1')
function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('sidebarCollapsed', sidebarCollapsed.value ? '1' : '0')
}

const route = useRoute()
const router = useRouter()

const menuRoutes = computed(() =>
  router.options.routes.filter((r) => {
    if (!r.meta?.title) return false
    if (r.meta.hidden) return false
    if (r.meta.requireAdmin && !auth.isAdmin.value) return false
    return true
  })
)
const currentTitle = computed(() => route.meta?.title || '')

const pwdVisible = ref(false)
const pwdLoading = ref(false)
const pwdForm = reactive({ old_password: '', new_password: '', confirm: '' })

function openChangePassword() {
  pwdForm.old_password = ''
  pwdForm.new_password = ''
  pwdForm.confirm = ''
  pwdVisible.value = true
}

async function onSubmitPwd() {
  if (!pwdForm.old_password || !pwdForm.new_password) {
    ElMessage.warning('请填写完整')
    return
  }
  if (pwdForm.new_password.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  if (pwdForm.new_password !== pwdForm.confirm) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  pwdLoading.value = true
  try {
    await authApi.changePassword({
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
    })
    ElMessage.success('密码已修改，请重新登录')
    pwdVisible.value = false
    auth.clear()
    router.replace('/login')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '修改失败')
  } finally {
    pwdLoading.value = false
  }
}

function onCommand(cmd) {
  if (cmd === 'logout') {
    auth.clear()
    router.replace('/login')
  } else if (cmd === 'changePassword') {
    openChangePassword()
  }
}
</script>

<style>
html, body, #app {
  height: 100%;
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
.app-root {
  height: 100vh;
}
.app-aside {
  background-color: #1f2d3d;
  transition: width 0.2s ease;
  overflow: hidden;
}
.app-logo {
  color: #fff;
  height: 56px;
  line-height: 56px;
  text-align: center;
  font-size: 18px;
  font-weight: 600;
  border-bottom: 1px solid #2d3e53;
  white-space: nowrap;
  overflow: hidden;
}
.app-logo.collapsed { font-size: 22px; letter-spacing: 0; }
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.collapse-btn {
  padding: 6px 8px;
  font-size: 18px;
  color: #606266;
}
.collapse-btn:hover { color: #409EFF; background: #ecf5ff; }
/* 折叠态下确保 menu-item 居中 */
.app-aside .el-menu--collapse .el-menu-item {
  padding: 0 !important;
  text-align: center;
}
.app-aside .el-menu {
  border-right: none;
}
.app-header {
  background-color: #fff;
  border-bottom: 1px solid #eaecef;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.page-title {
  font-size: 18px;
  font-weight: 500;
}
.header-right .user-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #303133;
}
.editable-cell {
  min-height: 22px;
  padding: 2px 6px;
  border-radius: 4px;
  cursor: text;
}
.editable-cell:hover {
  background: #f0f7ff;
  outline: 1px dashed #c6e2ff;
}
</style>
