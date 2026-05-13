<template>
  <div class="intro-page">
    <el-card shadow="never">
      <h1>AI 项目管理系统</h1>
      <p class="lead">
        本系统用于统一管理项目的客户面状态、版本发布与迭代规划，帮助项目组成员实时同步进度与关键问题。
      </p>

      <el-divider content-position="left">系统模块</el-divider>
      <el-row :gutter="20">
        <el-col :span="8" v-for="m in modules" :key="m.title">
          <el-card class="module-card" shadow="hover">
            <el-icon class="module-icon"><component :is="m.icon" /></el-icon>
            <h3>{{ m.title }}</h3>
            <p>{{ m.desc }}</p>
          </el-card>
        </el-col>
      </el-row>

      <el-divider content-position="left">关于</el-divider>
      <ul>
        <li>技术栈：Python (FastAPI) + Vue 3 + Element Plus + SQLite</li>
        <li>当前版本：v0.1.0（骨架版本）</li>
        <li>维护：项目管理组</li>
      </ul>
    </el-card>
  </div>
</template>

<script setup>
const modules = [
  { title: '客户面状态', desc: '汇总各机台的战场、阶段、客户满意度与关键问题。', icon: 'DataLine' },
  { title: '版本管理', desc: '记录软件版本发布信息，提供跳转链接。', icon: 'Files' },
  { title: '迭代管理', desc: '规划并跟踪迭代目标、负责人与时间节点。', icon: 'Calendar' },
]
</script>

<style scoped>
.intro-page h1 {
  margin: 0 0 8px 0;
}
.lead {
  color: #606266;
  font-size: 15px;
}
.module-card {
  text-align: center;
  height: 100%;
}
.module-icon {
  font-size: 36px;
  color: #409EFF;
}
</style>
