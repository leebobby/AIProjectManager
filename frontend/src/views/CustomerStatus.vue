<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <el-button type="primary" :icon="Plus" @click="openCreate">新增</el-button>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <span class="tip">提示：「近期重点事务」「关键问题」单元格双击可直接编辑</span>
      </div>

      <el-table :data="list" v-loading="loading" border stripe style="width: 100%">
        <el-table-column prop="machine_id" label="机台编号" width="120" />
        <el-table-column prop="battlefield" label="战场" width="140" />
        <el-table-column prop="current_stage" label="当前阶段" width="140" />
        <el-table-column label="近期关注度" width="180" align="center">
          <template #default="{ row }">
            <el-rate
              :model-value="row.attention_level || 0"
              :max="5"
              show-score
              score-template="{value}"
              @change="(v) => onRateChange(row, v)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="customer_status" label="客户面进展" min-width="200" show-overflow-tooltip />

        <el-table-column label="近期重点事务" min-width="220">
          <template #default="{ row }">
            <el-input
              v-if="isEditing(row, 'recent_focus')"
              ref="editRef"
              v-model="row.recent_focus"
              size="small"
              autofocus
              @blur="commit(row, 'recent_focus')"
              @keyup.enter="commit(row, 'recent_focus')"
              @keyup.esc="cancel(row, 'recent_focus')"
            />
            <div v-else class="editable-cell" @dblclick="startEdit(row, 'recent_focus')">
              {{ row.recent_focus || '—' }}
            </div>
          </template>
        </el-table-column>

        <el-table-column label="关键问题" min-width="220">
          <template #default="{ row }">
            <el-input
              v-if="isEditing(row, 'key_issues')"
              ref="editRef"
              v-model="row.key_issues"
              size="small"
              autofocus
              @blur="commit(row, 'key_issues')"
              @keyup.enter="commit(row, 'key_issues')"
              @keyup.esc="cancel(row, 'key_issues')"
            />
            <div v-else class="editable-cell" @dblclick="startEdit(row, 'key_issues')">
              {{ row.key_issues || '—' }}
            </div>
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

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑' : '新增'" width="600px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="机台编号">
          <el-input
            v-model="form.machine_id"
            :disabled="!!editing"
            :placeholder="editing ? '创建后不可修改' : '请输入'"
          />
        </el-form-item>
        <el-form-item label="战场">
          <el-input
            v-model="form.battlefield"
            :disabled="!!editing"
            :placeholder="editing ? '创建后不可修改' : '请输入'"
          />
        </el-form-item>
        <el-form-item label="当前阶段">
          <el-select v-model="form.current_stage" placeholder="请选择" style="width: 100%">
            <el-option v-for="s in stages" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="近期关注度">
          <el-rate v-model="form.attention_level" :max="5" show-score score-template="{value} 星" />
        </el-form-item>
        <el-form-item label="客户面进展">
          <el-input v-model="form.customer_status" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="近期重点事务">
          <el-input v-model="form.recent_focus" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="关键问题">
          <el-input v-model="form.key_issues" type="textarea" :rows="2" />
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
import { configApi, customerStatusApi } from '../api'

const list = ref([])
const stages = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const form = reactive(defaultForm())

const editingCell = ref(null)

function defaultForm() {
  return {
    machine_id: '',
    battlefield: '',
    current_stage: '',
    attention_level: 0,
    customer_status: '',
    recent_focus: '',
    key_issues: '',
  }
}

async function load() {
  loading.value = true
  try {
    const { data } = await customerStatusApi.list()
    list.value = data
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

async function loadConfig() {
  try {
    const { data } = await configApi.get()
    stages.value = data.current_stages || []
  } catch (e) {
    // 配置拉取失败不阻塞主流程
  }
}

function openCreate() {
  editing.value = null
  Object.assign(form, defaultForm())
  if (stages.value.length) form.current_stage = stages.value[0]
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = row
  Object.assign(form, row)
  dialogVisible.value = true
}

async function onSubmit() {
  if (!editing.value) {
    if (!form.machine_id || !form.battlefield) {
      ElMessage.warning('机台编号、战场必填')
      return
    }
  }
  try {
    if (editing.value) {
      // 后端编辑接口只接受可改字段
      const payload = {
        current_stage: form.current_stage,
        attention_level: form.attention_level,
        customer_status: form.customer_status,
        recent_focus: form.recent_focus,
        key_issues: form.key_issues,
      }
      await customerStatusApi.update(editing.value.id, payload)
      ElMessage.success('已更新')
    } else {
      await customerStatusApi.create(form)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确认删除机台 ${row.machine_id} 吗？`, '提示', { type: 'warning' })
  await customerStatusApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

// ===== 双击行内编辑 =====
function isEditing(row, field) {
  return (
    editingCell.value &&
    editingCell.value.id === row.id &&
    editingCell.value.field === field
  )
}

function startEdit(row, field) {
  editingCell.value = { id: row.id, field, original: row[field] }
}

function cancel(row, field) {
  if (!editingCell.value) return
  row[field] = editingCell.value.original
  editingCell.value = null
}

async function commit(row, field) {
  if (!editingCell.value) return
  const original = editingCell.value.original
  const newVal = row[field]
  editingCell.value = null
  if (newVal === original) return
  try {
    await customerStatusApi.update(row.id, { [field]: newVal })
    ElMessage.success('已保存')
  } catch (e) {
    row[field] = original
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

async function onRateChange(row, value) {
  const original = row.attention_level || 0
  if (value === original) return
  try {
    await customerStatusApi.update(row.id, { attention_level: value })
    row.attention_level = value
    ElMessage.success('已保存')
  } catch (e) {
    row.attention_level = original
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

onMounted(() => {
  load()
  loadConfig()
})
</script>

<style scoped>
.toolbar {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.tip {
  margin-left: auto;
  color: #909399;
  font-size: 12px;
}
</style>
