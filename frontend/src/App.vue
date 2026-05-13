<template>
  <router-view v-if="route.meta.layout === 'blank'" />

  <el-container v-else class="app-root">
    <el-aside width="220px" class="app-aside">
      <div class="app-logo">AI 项目管理</div>
      <el-menu
        :default-active="route.path"
        router
        background-color="#1f2d3d"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item v-for="r in menuRoutes" :key="r.path" :index="r.path">
          <el-icon><component :is="r.meta.icon" /></el-icon>
          <span>{{ r.meta.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <span class="page-title">{{ currentTitle }}</span>
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
                <el-dropdown-item command="logout">
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
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { auth } from './store/auth'

const route = useRoute()
const router = useRouter()

const menuRoutes = computed(() =>
  router.options.routes.filter((r) => {
    if (!r.meta?.title) return false
    if (r.meta.requireAdmin && !auth.isAdmin.value) return false
    return true
  })
)
const currentTitle = computed(() => route.meta?.title || '')

function onCommand(cmd) {
  if (cmd === 'logout') {
    auth.clear()
    router.replace('/login')
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
}
.app-logo {
  color: #fff;
  height: 56px;
  line-height: 56px;
  text-align: center;
  font-size: 18px;
  font-weight: 600;
  border-bottom: 1px solid #2d3e53;
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
