<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <el-button type="primary" :icon="Plus" @click="openCreate">发布新版本</el-button>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </div>

      <el-table :data="list" v-loading="loading" border stripe style="width: 100%">
        <el-table-column prop="version_no" label="版本号" width="140" />
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="description" label="说明" min-width="240" show-overflow-tooltip />
        <el-table-column prop="released_at" label="发布时间" width="180">
          <template #default="{ row }">{{ formatDate(row.released_at) }}</template>
        </el-table-column>
        <el-table-column label="跳转" width="120">
          <template #default="{ row }">
            <el-link v-if="row.release_url" type="primary" :href="row.release_url" target="_blank">
              前往
            </el-link>
            <span v-else style="color:#bbb">—</span>
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

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑版本' : '发布新版本'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="版本号">
          <el-input v-model="form.version_no" placeholder="例如 v1.2.0" />
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="跳转链接">
          <el-input v-model="form.release_url" placeholder="https://..." />
        </el-form-item>
        <el-form-item label="发布时间">
          <el-date-picker v-model="form.released_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" />
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
import { versionApi } from '../api'

const list = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const form = reactive(defaultForm())

function defaultForm() {
  return {
    version_no: '',
    title: '',
    description: '',
    release_url: '',
    released_at: null,
  }
}

async function load() {
  loading.value = true
  try {
    const { data } = await versionApi.list()
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
      await versionApi.update(editing.value.id, form)
      ElMessage.success('已更新')
    } else {
      await versionApi.create(form)
      ElMessage.success('已发布')
    }
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确认删除版本 ${row.version_no} 吗？`, '提示', { type: 'warning' })
  await versionApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString()
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  margin-bottom: 12px;
}
</style>
