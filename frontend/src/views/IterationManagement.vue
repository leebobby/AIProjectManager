<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <el-button type="primary" :icon="Plus" @click="openCreate">新增迭代</el-button>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </div>

      <el-table :data="list" v-loading="loading" border stripe style="width: 100%">
        <el-table-column prop="name" label="迭代名称" min-width="160" />
        <el-table-column prop="goal" label="迭代目标" min-width="240" show-overflow-tooltip />
        <el-table-column prop="owner" label="负责人" width="120" />
        <el-table-column label="开始时间" width="170">
          <template #default="{ row }">{{ formatDate(row.start_date) }}</template>
        </el-table-column>
        <el-table-column label="结束时间" width="170">
          <template #default="{ row }">{{ formatDate(row.end_date) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑迭代' : '新增迭代'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="迭代名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="迭代目标">
          <el-input v-model="form.goal" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="form.owner" />
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker v-model="form.start_date" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker v-model="form.end_date" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option label="规划中" value="planning" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="done" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { iterationApi } from '../api'

const list = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const form = reactive(defaultForm())

function defaultForm() {
  return {
    name: '',
    goal: '',
    owner: '',
    start_date: null,
    end_date: null,
    status: 'planning',
  }
}

async function load() {
  loading.value = true
  try {
    const { data } = await iterationApi.list()
    list.value = data
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  Object.assign(form, defaultForm())
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = row
  Object.assign(form, row)
  dialogVisible.value = true
}

async function onSubmit() {
  try {
    if (editing.value) {
      await iterationApi.update(editing.value.id, form)
      ElMessage.success('已更新')
    } else {
      await iterationApi.create(form)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确认删除迭代 ${row.name} 吗？`, '提示', { type: 'warning' })
  await iterationApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString()
}

const STATUS_LABEL = { planning: '规划中', in_progress: '进行中', done: '已完成' }
const STATUS_TAG = { planning: 'info', in_progress: 'warning', done: 'success' }

function statusLabel(s) {
  return STATUS_LABEL[s] || s
}
function statusTag(s) {
  return STATUS_TAG[s] || ''
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  margin-bottom: 12px;
}
</style>
