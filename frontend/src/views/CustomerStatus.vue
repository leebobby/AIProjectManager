<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <el-button v-if="isAdmin" type="primary" :icon="Plus" @click="openCreate">新增</el-button>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button v-if="isAdmin" :icon="Download" type="success" @click="onExport">导出 PPT</el-button>
        <span class="tip">
          提示：「当前进展」「近期现场关键诉求」「软件类风险和问题」双击单元格直接编辑{{ isAdmin ? '；管理员可双击「问题单」编辑链接' : '' }}
        </span>
      </div>

      <el-table :data="list" v-loading="loading" border stripe style="width: 100%">
        <el-table-column type="index" label="序号" width="60" align="center" :index="(i) => i + 1" />
        <el-table-column prop="machine_id" label="机台编号" width="110" />
        <el-table-column prop="battlefield" label="客户" width="140" />
        <el-table-column prop="model" label="型号" width="120" />
        <el-table-column label="当前阶段" width="140">
          <template #default="{ row }">
            <el-select
              v-if="isAdmin"
              :model-value="row.current_stage"
              size="small"
              @change="(v) => onStageChange(row, v)"
            >
              <el-option v-for="s in stages" :key="s" :label="s" :value="s" />
            </el-select>
            <span v-else>{{ row.current_stage || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="现场版本" width="170">
          <template #default="{ row }">
            <el-select
              v-if="isAdmin"
              :model-value="row.field_version"
              size="small"
              filterable
              allow-create
              default-first-option
              placeholder="选择或输入"
              @change="(v) => onVersionChange(row, v)"
            >
              <el-option v-for="v in versionOptions" :key="v.value" :label="v.label" :value="v.value" />
            </el-select>
            <span v-else>{{ row.field_version || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="近期关注度" width="170" align="center">
          <template #default="{ row }">
            <el-rate
              :model-value="row.attention_level || 0"
              :max="5"
              :disabled="!isAdmin"
              show-score
              score-template="{value}"
              @change="(v) => onRateChange(row, v)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="customer_status" label="当前进展" min-width="200">
          <template #default="{ row }">
            <el-input
              v-if="isEditing(row, 'customer_status')"
              v-model="row.customer_status"
              size="small"
              autofocus
              type="textarea"
              :rows="2"
              @blur="commit(row, 'customer_status')"
              @keyup.enter.ctrl="commit(row, 'customer_status')"
              @keyup.esc="cancel(row, 'customer_status')"
            />
            <div v-else class="editable-cell" @dblclick="startEdit(row, 'customer_status')">
              {{ row.customer_status || '—' }}
            </div>
          </template>
        </el-table-column>

        <el-table-column label="近期现场关键诉求" min-width="220">
          <template #default="{ row }">
            <el-input
              v-if="isEditing(row, 'recent_focus')"
              v-model="row.recent_focus"
              size="small"
              autofocus
              type="textarea"
              :rows="2"
              @blur="commit(row, 'recent_focus')"
              @keyup.enter.ctrl="commit(row, 'recent_focus')"
              @keyup.esc="cancel(row, 'recent_focus')"
            />
            <div v-else class="editable-cell" @dblclick="startEdit(row, 'recent_focus')">
              {{ row.recent_focus || '—' }}
            </div>
          </template>
        </el-table-column>

        <el-table-column label="软件类风险和问题" min-width="220">
          <template #default="{ row }">
            <el-input
              v-if="isEditing(row, 'key_issues')"
              v-model="row.key_issues"
              size="small"
              autofocus
              type="textarea"
              :rows="2"
              @blur="commit(row, 'key_issues')"
              @keyup.enter.ctrl="commit(row, 'key_issues')"
              @keyup.esc="cancel(row, 'key_issues')"
            />
            <div v-else class="editable-cell" @dblclick="startEdit(row, 'key_issues')">
              {{ row.key_issues || '—' }}
            </div>
          </template>
        </el-table-column>

        <el-table-column label="问题单情况" width="140" align="center">
          <template #default="{ row }">
            <template v-if="isAdmin && isEditing(row, 'issue_url')">
              <el-input
                v-model="row.issue_url"
                size="small"
                autofocus
                placeholder="https://..."
                @blur="commit(row, 'issue_url')"
                @keyup.enter="commit(row, 'issue_url')"
                @keyup.esc="cancel(row, 'issue_url')"
              />
            </template>
            <template v-else>
              <el-button
                v-if="row.issue_url"
                size="small"
                type="primary"
                link
                :icon="Link"
                @click="openIssue(row)"
                @dblclick="isAdmin && startEdit(row, 'issue_url')"
              >
                查看
              </el-button>
              <el-button
                v-else-if="isAdmin"
                size="small"
                type="info"
                link
                @click="startEdit(row, 'issue_url')"
              >
                设置
              </el-button>
              <span v-else>—</span>
            </template>
          </template>
        </el-table-column>

        <el-table-column v-if="isAdmin" label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑' : '新增'" width="640px">
      <el-form :model="form" label-width="130px">
        <el-form-item label="机台编号">
          <el-input v-model="form.machine_id" :disabled="!!editing" :placeholder="editing ? '创建后不可修改' : '请输入'" />
        </el-form-item>
        <el-form-item label="客户">
          <el-input v-model="form.battlefield" :disabled="!!editing" :placeholder="editing ? '创建后不可修改' : '请输入'" />
        </el-form-item>
        <el-form-item label="型号">
          <el-input v-model="form.model" :disabled="!!editing" :placeholder="editing ? '创建后不可修改' : '请输入'" />
        </el-form-item>
        <el-form-item label="当前阶段">
          <el-select v-model="form.current_stage" placeholder="请选择" style="width: 100%">
            <el-option v-for="s in stages" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="现场版本">
          <el-select v-model="form.field_version" filterable allow-create default-first-option placeholder="选择或输入" style="width: 100%">
            <el-option v-for="v in versionOptions" :key="v.value" :label="v.label" :value="v.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="近期关注度">
          <el-rate v-model="form.attention_level" :max="5" show-score score-template="{value} 星" />
        </el-form-item>
        <el-form-item label="当前进展">
          <el-input v-model="form.customer_status" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="近期现场关键诉求">
          <el-input v-model="form.recent_focus" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="软件类风险和问题">
          <el-input v-model="form.key_issues" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="问题单链接">
          <el-input v-model="form.issue_url" placeholder="https://..." />
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
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Link, Plus, Refresh } from '@element-plus/icons-vue'
import { configApi, customerStatusApi, downloadBlob, versionApi } from '../api'
import { auth } from '../store/auth'

const isAdmin = auth.isAdmin

const list = ref([])
const stages = ref([])
const versions = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const form = reactive(defaultForm())

const editingCell = ref(null)

const ADMIN_FIELDS = ['current_stage', 'field_version', 'attention_level', 'issue_url']
const USER_FIELDS = ['customer_status', 'recent_focus', 'key_issues']

const versionOptions = computed(() => versions.value.map((v) => ({
  value: v.version_no,
  label: v.title ? `${v.version_no} · ${v.title}` : v.version_no,
})))

function defaultForm() {
  return {
    machine_id: '',
    battlefield: '',
    model: '',
    current_stage: '',
    field_version: '',
    attention_level: 0,
    customer_status: '',
    recent_focus: '',
    key_issues: '',
    issue_url: '',
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
    /* 不阻塞 */
  }
}

async function loadVersions() {
  try {
    const { data } = await versionApi.list()
    versions.value = data
  } catch (e) {
    /* 不阻塞 */
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
      ElMessage.warning('机台编号、客户必填')
      return
    }
  }
  try {
    if (editing.value) {
      const payload = { version: form.version }
      for (const k of [...ADMIN_FIELDS, ...USER_FIELDS]) payload[k] = form[k]
      await customerStatusApi.update(editing.value.id, payload)
      ElMessage.success('已更新')
      dialogVisible.value = false
      load()
    } else {
      await customerStatusApi.create(form)
      ElMessage.success('已创建')
      dialogVisible.value = false
      load()
    }
  } catch (e) {
    if (e.response?.status !== 409) ElMessage.error(e.response?.data?.detail || '保存失败')
    // 409: 拦截器已提示，对话框保持打开，让用户手动刷新后重试
  }
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确认删除机台 ${row.machine_id} 吗？`, '提示', { type: 'warning' })
  await customerStatusApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

// ===== 行内编辑 =====
function isEditing(row, field) {
  return editingCell.value && editingCell.value.id === row.id && editingCell.value.field === field
}

function startEdit(row, field) {
  if (ADMIN_FIELDS.includes(field) && !isAdmin.value) {
    ElMessage.warning('该字段仅管理员可修改')
    return
  }
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
    const { data } = await customerStatusApi.update(row.id, { [field]: newVal, version: row.version })
    row.version = data.version
    ElMessage.success('已保存')
  } catch (e) {
    row[field] = original
    if (e.response?.status !== 409) ElMessage.error(e.response?.data?.detail || '保存失败')
    else load()
  }
}

async function onRateChange(row, value) {
  if (!isAdmin.value) {
    ElMessage.warning('关注度仅管理员可修改')
    return
  }
  const original = row.attention_level || 0
  if (value === original) return
  try {
    const { data } = await customerStatusApi.update(row.id, { attention_level: value, version: row.version })
    row.attention_level = data.attention_level
    row.version = data.version
    ElMessage.success('已保存')
  } catch (e) {
    row.attention_level = original
    if (e.response?.status !== 409) ElMessage.error(e.response?.data?.detail || '保存失败')
    else load()
  }
}

async function onStageChange(row, value) {
  const original = row.current_stage
  if (value === original) return
  try {
    const { data } = await customerStatusApi.update(row.id, { current_stage: value, version: row.version })
    row.current_stage = data.current_stage
    row.version = data.version
    ElMessage.success('已保存')
  } catch (e) {
    row.current_stage = original
    if (e.response?.status !== 409) ElMessage.error(e.response?.data?.detail || '保存失败')
    else load()
  }
}

async function onVersionChange(row, value) {
  const original = row.field_version
  if (value === original) return
  try {
    const { data } = await customerStatusApi.update(row.id, { field_version: value, version: row.version })
    row.field_version = data.field_version
    row.version = data.version
    ElMessage.success('已保存')
  } catch (e) {
    row.field_version = original
    if (e.response?.status !== 409) ElMessage.error(e.response?.data?.detail || '保存失败')
    else load()
  }
}

function openIssue(row) {
  if (row.issue_url) window.open(row.issue_url, '_blank')
}

async function onExport() {
  try {
    const resp = await customerStatusApi.exportPptx()
    const ts = new Date().toISOString().replace(/[:T]/g, '-').slice(0, 19)
    downloadBlob(resp.data, `customer-status-${ts}.pptx`)
    ElMessage.success('已导出')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '导出失败')
  }
}

onMounted(() => {
  load()
  loadConfig()
  loadVersions()
})
</script>

<style scoped>
.toolbar {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.tip {
  margin-left: auto;
  color: #909399;
  font-size: 12px;
}
.editable-cell {
  cursor: text;
  min-height: 22px;
  white-space: pre-wrap;
}
</style>
