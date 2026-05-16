<template>
  <div class="intro-page">
    <div class="hero">
      <div class="hero-inner">
        <div class="hero-tag">AI · Project Manager</div>
        <h1 class="hero-title">AI 项目管理系统</h1>
        <p class="hero-sub">
          统一管理客户面状态、版本发布与迭代规划，让团队成员实时同步进度、关键问题与变更。
        </p>
        <div class="hero-stack">
          <span class="badge badge-py">Python · FastAPI</span>
          <span class="badge badge-vue">Vue 3 · Element Plus</span>
          <span class="badge badge-db">SQLite · SQLAlchemy</span>
          <span class="badge badge-auth">JWT · bcrypt</span>
        </div>
        <div class="hero-stats">
          <div class="stat-item">
            <div class="stat-num">{{ stats.versions }}</div>
            <div class="stat-label">版本</div>
          </div>
          <div class="stat-divider" />
          <div class="stat-item">
            <div class="stat-num">{{ stats.iterations }}</div>
            <div class="stat-label">迭代</div>
          </div>
          <div class="stat-divider" />
          <div class="stat-item">
            <div class="stat-num">{{ stats.machines }}</div>
            <div class="stat-label">机台</div>
          </div>
        </div>
      </div>
    </div>

    <el-card shadow="never" class="modules-card">
      <template #header>
        <span class="card-title"><el-icon><Grid /></el-icon> 系统模块</span>
        <span class="card-hint">点击卡片快速进入对应模块</span>
      </template>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="8" v-for="m in modules" :key="m.path">
          <div class="module-card" :class="m.theme" @click="$router.push(m.path)" tabindex="0" @keyup.enter="$router.push(m.path)">
            <div class="module-icon"><el-icon><component :is="m.icon" /></el-icon></div>
            <div class="module-meta">
              <h3>{{ m.title }}</h3>
              <p>{{ m.desc }}</p>
              <span class="module-link">进入 <el-icon><Right /></el-icon></span>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never" class="about-card">
      <template #header>
        <span class="card-title"><el-icon><InfoFilled /></el-icon> 关于</span>
      </template>
      <ul class="about-list">
        <li><strong>技术栈：</strong>Python (FastAPI) + Vue 3 + Element Plus + SQLite</li>
        <li><strong>当前版本：</strong>v0.6.0</li>
        <li><strong>维护：</strong>项目管理组</li>
      </ul>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { auth } from '../store/auth'
import {
  annualIterationApi,
  customerStatusApi,
  versionApi,
} from '../api'

const isAdmin = auth.isAdmin

const modules = [
  {
    title: '客户面状态',
    desc: '机台分阶段进展、关注度、关键诉求、风险问题与问题单。',
    icon: 'DataLine',
    path: '/customer-status',
    theme: 't-blue',
  },
  {
    title: '版本管理',
    desc: '记录软件版本发布、说明与跳转链接，作为现场版本的来源。',
    icon: 'Files',
    path: '/versions',
    theme: 't-green',
  },
  {
    title: '迭代管理',
    desc: '年度 12 月迭代规划、需求清单、6 段交付进展跟踪与导出。',
    icon: 'Calendar',
    path: '/iterations',
    theme: 't-orange',
  },
  ...(isAdmin.value
    ? [{
        title: '用户管理',
        desc: '账号、角色、启停与重置密码（仅管理员）。',
        icon: 'User',
        path: '/users',
        theme: 't-purple',
      }]
    : []),
]

const stats = reactive({ versions: '-', iterations: '-', machines: '-' })

async function loadStats() {
  try {
    const [v, m] = await Promise.all([
      versionApi.list(),
      customerStatusApi.list(),
    ])
    stats.versions = v.data.length
    stats.machines = m.data.length
  } catch (e) { /* 不阻塞 */ }
  try {
    const year = new Date().getFullYear()
    const { data } = await annualIterationApi.list(year)
    stats.iterations = data.filter(it => it.name).length || data.length
  } catch (e) { /* 不阻塞 */ }
}

onMounted(loadStats)
</script>

<style scoped>
.intro-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background: linear-gradient(135deg, #1b3a6b 0%, #2c558c 35%, #4073ba 100%);
  color: #fff;
  padding: 32px 36px;
  box-shadow: 0 8px 24px -12px rgba(31, 45, 61, 0.45);
}
.hero::before, .hero::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
  pointer-events: none;
}
.hero::before { width: 240px; height: 240px; right: -60px; top: -80px; }
.hero::after  { width: 160px; height: 160px; right: 140px; bottom: -80px; background: rgba(255, 255, 255, 0.07); }

.hero-inner { position: relative; z-index: 1; }
.hero-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.16);
  font-size: 12px;
  letter-spacing: 1.5px;
  margin-bottom: 12px;
}
.hero-title {
  font-size: 30px;
  margin: 0 0 8px 0;
  letter-spacing: 1px;
}
.hero-sub {
  margin: 0 0 18px 0;
  color: rgba(255,255,255,0.85);
  max-width: 720px;
  line-height: 1.65;
}
.hero-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 18px;
}
.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.2);
}
.badge-py    { background: rgba(255, 209, 102, 0.18); border-color: rgba(255, 209, 102, 0.5); }
.badge-vue   { background: rgba(102, 217, 171, 0.18); border-color: rgba(102, 217, 171, 0.5); }
.badge-db    { background: rgba(110, 172, 255, 0.20); border-color: rgba(110, 172, 255, 0.55); }
.badge-auth  { background: rgba(245, 130, 130, 0.18); border-color: rgba(245, 130, 130, 0.5); }

.hero-stats {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-top: 4px;
}
.stat-item { display: flex; flex-direction: column; }
.stat-num { font-size: 26px; font-weight: 700; line-height: 1.1; }
.stat-label { font-size: 12px; color: rgba(255,255,255,0.7); }
.stat-divider { width: 1px; height: 28px; background: rgba(255,255,255,0.2); }

.modules-card :deep(.el-card__header),
.about-card   :deep(.el-card__header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-title { font-size: 16px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }
.card-hint  { color: #909399; font-size: 12px; }

.module-card {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #eaecef;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #fff;
  height: 100%;
}
.module-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px -16px rgba(31, 45, 61, 0.3);
  border-color: transparent;
}
.module-card:focus-visible {
  outline: 2px solid #409EFF;
  outline-offset: 2px;
}
.module-icon {
  width: 44px; height: 44px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
  border-radius: 8px;
  color: #fff;
  flex-shrink: 0;
}
.t-blue   .module-icon { background: linear-gradient(135deg, #4073ba, #2c558c); }
.t-green  .module-icon { background: linear-gradient(135deg, #67c23a, #449728); }
.t-orange .module-icon { background: linear-gradient(135deg, #e6a23c, #b87f1e); }
.t-purple .module-icon { background: linear-gradient(135deg, #8e7ad8, #6b5ab8); }

.module-meta { flex: 1; min-width: 0; }
.module-meta h3 { margin: 0 0 4px 0; font-size: 16px; color: #303133; }
.module-meta p  { margin: 0 0 8px 0; color: #606266; font-size: 13px; line-height: 1.55; }
.module-link {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 12px; color: #409EFF; font-weight: 500;
}

.about-list {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  line-height: 1.9;
}
</style>
