<template>
  <router-view v-if="route.meta.layout === 'blank'" />

  <el-container v-else class="app-root">
    <el-aside
      class="app-aside"
      :class="{ 'is-collapsed': sidebarCollapsed }"
      :style="{ '--el-aside-width': sidebarCollapsed ? '64px' : '220px' }"
    >
      <div class="app-logo" :class="{ collapsed: sidebarCollapsed }">
        {{ sidebarCollapsed ? '岳' : '岳麓山管理系统' }}
      </div>
      <el-menu
        :default-active="activeMenuPath"
        :collapse="sidebarCollapsed"
        :collapse-transition="false"
        router
        background-color="#1f2d3d"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <template v-for="r in menuRoutes" :key="r.path">
          <!-- 专项管理：动态二级菜单 -->
          <el-sub-menu
            v-if="r.meta.specialsParent && (auth.isAdmin.value || specials.list.length > 0)"
            :index="r.path"
          >
            <template #title>
              <el-icon><component :is="r.meta.icon" /></el-icon>
              <span>{{ r.meta.title }}</span>
            </template>
            <el-menu-item v-if="auth.isAdmin.value" :index="r.path">
              <el-icon><Setting /></el-icon>
              <template #title>专项配置</template>
            </el-menu-item>
            <el-menu-item
              v-for="s in specials.list"
              :key="s.id"
              :index="'/specials/' + s.id"
            >
              <el-icon><Aim /></el-icon>
              <template #title>
                <el-tag size="small" :type="s.kind === 'assault' ? 'danger' : 'info'" effect="plain" style="margin-right: 6px">
                  {{ s.kind === 'assault' ? '攻关' : '专项' }}
                </el-tag>
                {{ s.name }}
              </template>
            </el-menu-item>
          </el-sub-menu>

          <el-menu-item v-else-if="!r.meta.specialsParent" :index="r.path">
            <el-icon><component :is="r.meta.icon" /></el-icon>
            <template #title>{{ r.meta.title }}</template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <button
            type="button"
            class="collapse-btn"
            :title="sidebarCollapsed ? '展开侧栏' : '收起侧栏'"
            @click="toggleSidebar"
          >
            <el-icon :size="22">
              <Fold v-if="!sidebarCollapsed" />
              <Expand v-else />
            </el-icon>
          </button>
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
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Aim, Expand, Fold, Setting } from '@element-plus/icons-vue'
import { authApi } from './api'
import { auth, installCrossTabAuth } from './store/auth'
import { startIdleWatcher } from './store/idleWatcher'
import { specials, reloadSpecials, clearSpecials } from './store/specials'

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
const currentTitle = computed(() => {
  if (route.name === 'SpecialDetail') {
    const s = specials.list.find(x => String(x.id) === String(route.params.id))
    if (!s) return '详情'
    const label = s.kind === 'assault' ? '攻关' : '专项'
    return `${label}：${s.name}`
  }
  return route.meta?.title || ''
})

// 高亮当前菜单：详情页时高亮对应 submenu 项
const activeMenuPath = computed(() => {
  if (route.name === 'SpecialDetail') {
    return `/specials/${route.params.id}`
  }
  return route.path
})

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
    auth.signalLogout('password-changed')
    router.replace('/login')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '修改失败')
  } finally {
    pwdLoading.value = false
  }
}

async function onCommand(cmd) {
  if (cmd === 'logout') {
    try { await authApi.logout() } catch { /* 后端日志失败不阻塞登出 */ }
    auth.signalLogout('manual')
    router.replace('/login')
  } else if (cmd === 'changePassword') {
    openChangePassword()
  }
}

const IDLE_MS = 15 * 60 * 1000 // 15 分钟
let stopIdle = null

function gotoLogin(reason) {
  if (route.path === '/login') return
  if (reason === 'idle') ElMessage.warning('因长时间未操作，已自动退出登录')
  router.replace({ path: '/login', query: { redirect: route.fullPath } })
}

onMounted(() => {
  installCrossTabAuth((reason) => gotoLogin(reason))
  stopIdle = startIdleWatcher({
    idleMs: IDLE_MS,
    isActive: () => auth.isLoggedIn.value,
    onIdle: () => {
      auth.signalLogout('idle')
      gotoLogin('idle')
    },
  })
  if (auth.isLoggedIn.value) reloadSpecials()
})

// 登录状态变化时刷新 / 清空菜单数据
watch(() => auth.isLoggedIn.value, (v) => {
  if (v) reloadSpecials()
  else clearSpecials()
})

onBeforeUnmount(() => {
  if (stopIdle) stopIdle()
})
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
  transition: width 0.25s ease, --el-aside-width 0.25s ease;
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
  gap: 8px;
}
.collapse-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: #606266;
  border-radius: 4px;
  cursor: pointer;
  padding: 0;
  transition: all 0.15s;
}
.collapse-btn:hover {
  background: #ecf5ff;
  color: #409EFF;
}
.collapse-btn:active {
  background: #d9ecff;
}
/* 折叠态下 menu-item 居中显示图标 */
.app-aside .el-menu--collapse {
  width: 64px;
}
.app-aside .el-menu--collapse .el-menu-item {
  padding: 0 !important;
  text-align: center;
}
.app-aside .el-menu--collapse .el-menu-item .el-icon {
  margin-right: 0;
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
