<template>
  <div class="customer-page">
    <div class="header">
      <el-button :icon="ArrowLeft" size="small" @click="goBack">返回客户面状态</el-button>
    </div>
    <el-card shadow="never" class="page-card">
      <CustomerDetailPanel :customer-id="Number(route.params.id)" />
    </el-card>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import CustomerDetailPanel from '../components/CustomerDetailPanel.vue'

const route = useRoute()
const router = useRouter()

function goBack() {
  router.push('/customer-status')
}
</script>

<style scoped>
.customer-page {
  /* 与正常 tab 页占用相同的宽度，由外层 el-main 给的内边距控制 */
}
.header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
.page-card {
  padding: 4px 8px 8px;
}
</style>
