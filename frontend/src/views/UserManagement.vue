<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <el-button type="primary" :icon="Plus" @click="openCreate">新增用户</el-button>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </div>

      <el-table :data="list" v-loading="loading" border stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="登录名" width="160" />
        <el-table-column prop="full_name" label="姓名" width="160" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" effect="dark">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="auth_provider" label="来源" width="120">
          <template #default="{ row }">
            {{ row.auth_provider === 'local' ? '本地账号' : '企业 SSO' }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button
              size="small"
              type="danger"
              :disabled="row.id === auth.state.user?.id"
              @click="onDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑用户' : '新增用户'" width="500px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="登录名">
          <el-input v-model="form.username" :disabled="!!editing" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.full_name" />
        </el-form-item>
        <el-form-item :label="editing ? '重置密码' : '密码'">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="editing ? '留空表示不修改' : '请输入密码'"
          />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="normal" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editing" label="状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
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
import { userApi } from '../api'
import { auth } from '../store/auth'

const list = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const form = reactive(defaultForm())

function defaultForm() {
  return {
    username: '',
    full_name: '',
    password: '',
    role: 'normal',
    is_active: true,
  }
}

async function load() {
  loading.value = true
  try {
    const { data } = await userApi.list()
    list.value = data
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加载失败')
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
  Object.assign(form, {
    username: row.username,
    full_name: row.full_name,
    password: '',
    role: row.role,
    is_active: row.is_active,
  })
  dialogVisible.value = true
}

async function onSubmit() {
  if (!editing.value && (!form.username || !form.password)) {
    ElMessage.warning('用户名和密码必填')
    return
  }
  try {
    if (editing.value) {
      const payload = {
        full_name: form.full_name,
        role: form.role,
        is_active: form.is_active,
      }
      if (form.password) payload.password = form.password
      await userApi.update(editing.value.id, payload)
      ElMessage.success('已更新')
    } else {
      await userApi.create({
        username: form.username,
        password: form.password,
        full_name: form.full_name,
        role: form.role,
      })
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确认删除用户 ${row.username} 吗？`, '提示', { type: 'warning' })
  try {
    await userApi.remove(row.id)
    ElMessage.success('已删除')
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
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
