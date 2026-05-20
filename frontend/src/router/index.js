import { createRouter, createWebHistory } from 'vue-router'
import { auth } from '../store/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { public: true, layout: 'blank' },
  },
  { path: '/', redirect: '/intro' },
  {
    path: '/intro',
    name: 'ProjectIntro',
    component: () => import('../views/ProjectIntro.vue'),
    meta: { title: '项目简介', icon: 'InfoFilled' },
  },
  {
    path: '/customer-status',
    name: 'CustomerStatus',
    component: () => import('../views/CustomerStatus.vue'),
    meta: { title: '客户面状态', icon: 'DataLine' },
  },
  {
    path: '/versions',
    name: 'VersionManagement',
    component: () => import('../views/VersionManagement.vue'),
    meta: { title: '版本管理', icon: 'Files' },
  },
  {
    path: '/iterations',
    name: 'IterationManagement',
    component: () => import('../views/IterationManagement.vue'),
    meta: { title: '迭代管理', icon: 'Calendar' },
  },
  {
    path: '/iterations/:id',
    name: 'IterationDetail',
    component: () => import('../views/IterationDetail.vue'),
    meta: { title: '迭代详情', hidden: true },
  },
  {
    path: '/issues',
    name: 'IssueManagement',
    component: () => import('../views/IssueManagement.vue'),
    meta: { title: '问题单管理', icon: 'Warning' },
  },
  {
    path: '/stakeholders',
    name: 'StakeholderManagement',
    component: () => import('../views/StakeholderManagement.vue'),
    meta: { title: '干系人管理', icon: 'Avatar' },
  },
  {
    path: '/roadmaps',
    name: 'RoadmapManage',
    component: () => import('../views/RoadmapManage.vue'),
    meta: { title: '里程碑管理', icon: 'Guide', requireAdmin: true },
  },
  {
    path: '/handbook',
    name: 'ProjectHandbook',
    component: () => import('../views/ProjectHandbook.vue'),
    meta: { title: '项目一本通', icon: 'Notebook' },
  },
  {
    path: '/specials',
    name: 'SpecialList',
    // 路由本身不需要 requireAdmin（页面内自查），让左侧菜单的"专项管理"分组对普通用户也可见
    component: () => import('../views/SpecialList.vue'),
    meta: { title: '专项管理', icon: 'Briefcase', specialsParent: true },
  },
  {
    path: '/specials/:id(\\d+)',
    name: 'SpecialDetail',
    component: () => import('../views/SpecialDetail.vue'),
    meta: { title: '专项详情', hidden: true },
  },
  {
    path: '/users',
    name: 'UserManagement',
    component: () => import('../views/UserManagement.vue'),
    meta: { title: '用户管理', icon: 'User', requireAdmin: true },
  },
  {
    path: '/op-logs',
    name: 'OperationLogs',
    component: () => import('../views/OperationLogs.vue'),
    meta: { title: '操作日志', icon: 'Document', requireAdmin: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if (to.meta.public) return true
  if (!auth.isLoggedIn.value) return { path: '/login', query: { redirect: to.fullPath } }
  if (to.meta.requireAdmin && !auth.isAdmin.value) return { path: '/intro' }
  return true
})

export default router
