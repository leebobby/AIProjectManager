<template>
  <div>
    <el-page-header @back="goBack">
      <template #content>
        <span v-if="iteration">
          {{ iteration.year }}年{{ iteration.month }}月迭代 · {{ iteration.name || '未命名' }}
        </span>
        <span v-else>加载中…</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="card">
      <div class="toolbar">
        <el-button type="primary" :icon="Plus" @click="openCreate">新增需求</el-button>
        <el-button :icon="Upload" type="warning" @click="openImport">批量导入</el-button>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button v-if="isAdmin" :icon="Download" type="success" @click="onExport">导出 PPT</el-button>
        <span class="tip">提示：基础列双击编辑，6 个进展直接下拉切换；备注列记录变更说明</span>
      </div>

      <el-table :data="list" v-loading="loading" border stripe style="width: 100%">
        <el-table-column prop="seq" label="序号" width="70" align="center" />
        <el-table-column label="需求编号" width="160">
          <template #default="{ row }">
            <el-input
              v-if="isEditing(row, 'req_no')"
              v-model="row.req_no"
              size="small"
              autofocus
              @blur="commit(row, 'req_no')"
              @keyup.enter="commit(row, 'req_no')"
              @keyup.esc="cancel(row, 'req_no')"
            />
            <div v-else class="editable-cell" @dblclick="startEdit(row, 'req_no')">
              <el-link v-if="row.req_url" :href="row.req_url" type="primary" target="_blank">
                {{ row.req_no || '（点此查看）' }}
              </el-link>
              <span v-else>{{ row.req_no || '—' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="需求标题" min-width="240">
          <template #default="{ row }">
            <el-input
              v-if="isEditing(row, 'title')"
              v-model="row.title"
              size="small"
              autofocus
              @blur="commit(row, 'title')"
              @keyup.enter="commit(row, 'title')"
              @keyup.esc="cancel(row, 'title')"
            />
            <div v-else class="editable-cell" @dblclick="startEdit(row, 'title')">
              {{ row.title || '—' }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="责任人" width="120">
          <template #default="{ row }">
            <el-input
              v-if="isEditing(row, 'owner')"
              v-model="row.owner"
              size="small"
              autofocus
              @blur="commit(row, 'owner')"
              @keyup.enter="commit(row, 'owner')"
              @keyup.esc="cancel(row, 'owner')"
            />
            <div v-else class="editable-cell" @dblclick="startEdit(row, 'owner')">
              {{ row.owner || '—' }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="优先级" width="100" align="center">
          <template #default="{ row }">
            <el-select
              :model-value="row.priority"
              size="small"
              @change="(v) => onFieldChange(row, 'priority', v)"
            >
              <el-option v-for="p in PRIORITIES" :key="p" :label="p" :value="p" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="计划交付版本" width="170">
          <template #default="{ row }">
            <el-select
              :model-value="row.planned_version"
              size="small"
              clearable
              filterable
              allow-create
              placeholder="选择或输入版本"
              style="width: 100%"
              @change="(v) => onFieldChange(row, 'planned_version', v)"
            >
              <el-option-group
                v-for="group in versionGroups"
                :key="group.label"
                :label="group.label"
              >
                <el-option
                  v-for="ver in group.options"
                  :key="ver.id"
                  :label="ver.version_no"
                  :value="ver.version_no"
                >
                  <span>{{ ver.version_no }}</span>
                  <span v-if="ver.title" style="color:#909399; margin-left:6px; font-size:12px">{{ ver.title }}</span>
                </el-option>
              </el-option-group>
            </el-select>
          </template>
        </el-table-column>

        <el-table-column label="交付进展跟踪" align="center">
          <el-table-column
            v-for="col in PROGRESS_COLS"
            :key="col.field"
            :label="col.label"
            width="110"
            align="center"
          >
            <template #default="{ row }">
              <el-select
                :model-value="row[col.field]"
                size="small"
                @change="(v) => onFieldChange(row, col.field, v)"
              >
                <el-option
                  v-for="s in PROGRESS_STATUSES"
                  :key="s"
                  :label="s"
                  :value="s"
                />
              </el-select>
            </template>
          </el-table-column>
        </el-table-column>

        <el-table-column label="备注" min-width="180">
          <template #default="{ row }">
            <el-input
              v-if="isEditing(row, 'remark')"
              v-model="row.remark"
              size="small"
              autofocus
              type="textarea"
              :rows="2"
              @blur="commit(row, 'remark')"
              @keyup.enter.ctrl="commit(row, 'remark')"
              @keyup.esc="cancel(row, 'remark')"
            />
            <div v-else class="editable-cell" @dblclick="startEdit(row, 'remark')">
              <el-tag v-if="row.remark" type="warning" size="small" effect="plain" class="remark-tag">变更</el-tag>
              <span :class="row.remark ? 'remark-text' : 'remark-empty'">{{ row.remark || '—' }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">完整编辑</el-button>
            <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑需求' : '新增需求'" width="640px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="序号">
          <el-input-number v-model="form.seq" :min="0" />
        </el-form-item>
        <el-form-item label="需求编号">
          <el-input v-model="form.req_no" />
        </el-form-item>
        <el-form-item label="需求超链接">
          <el-input v-model="form.req_url" placeholder="https://..." />
        </el-form-item>
        <el-form-item label="需求标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="责任人">
          <el-input v-model="form.owner" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority" style="width: 100%">
            <el-option v-for="p in PRIORITIES" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="计划交付版本">
          <el-select
            v-model="form.planned_version"
            clearable
            filterable
            allow-create
            placeholder="选择或输入版本"
            style="width: 100%"
          >
            <el-option-group
              v-for="group in versionGroups"
              :key="group.label"
              :label="group.label"
            >
              <el-option
                v-for="ver in group.options"
                :key="ver.id"
                :label="ver.version_no"
                :value="ver.version_no"
              >
                <span>{{ ver.version_no }}</span>
                <span v-if="ver.title" style="color:#909399; margin-left:6px; font-size:12px">{{ ver.title }}</span>
              </el-option>
            </el-option-group>
          </el-select>
        </el-form-item>
        <el-form-item v-for="col in PROGRESS_COLS" :key="col.field" :label="col.label">
          <el-select v-model="form[col.field]" style="width: 100%">
            <el-option v-for="s in PROGRESS_STATUSES" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="如有变更，请说明……" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importVisible" title="批量导入需求" width="520px">
      <p class="import-tip">
        1. 先下载模板，按格式填写需求清单；<br />
        2. 表头列名请勿改动；进展列填写「未开始/进行中/已完成/已延期/不涉及」；<br />
        3. 上传 .xlsx 文件，系统将批量创建到当前迭代下。
      </p>
      <el-button :icon="Download" link type="primary" @click="onDownloadTemplate">
        下载导入模板 (.xlsx)
      </el-button>

      <el-divider />

      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :limit="1"
        :on-exceed="onExceed"
        :on-change="onFileChange"
        :show-file-list="true"
        accept=".xlsx"
        drag
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽 .xlsx 文件到此，或<em>点击选择</em></div>
      </el-upload>

      <div v-if="importResult" class="import-result">
        <el-alert
          :title="`成功导入 ${importResult.created} 条`"
          :type="importResult.errors?.length ? 'warning' : 'success'"
          :description="importResult.errors?.length ? importResult.errors.join('\n') : '无错误'"
          show-icon
          :closable="false"
        />
      </div>

      <template #footer>
        <el-button @click="importVisible = false">关闭</el-button>
        <el-button type="primary" :loading="importing" :disabled="!importFile" @click="onSubmitImport">
          开始导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Plus, Refresh, Upload, UploadFilled } from '@element-plus/icons-vue'
import { annualIterationApi, downloadBlob, iterationRequirementApi, majorVersionApi } from '../api'
import { auth } from '../store/auth'

const route = useRoute()
const router = useRouter()
const isAdmin = auth.isAdmin

const PROGRESS_COLS = [
  { field: 'progress_walkthrough', label: '需求串讲' },
  { field: 'progress_reverse', label: '反串讲' },
  { field: 'progress_stc', label: 'STC设计' },
  { field: 'progress_coding', label: '编码' },
  { field: 'progress_bbit', label: 'BBIT' },
  { field: 'progress_clarify', label: '转测澄清' },
]
const PROGRESS_STATUSES = ['未开始', '进行中', '已完成', '已延期', '不涉及']
const PRIORITIES = ['P0', 'P1', 'P2', 'P3']

const iterationId = Number(route.params.id)
const iteration = ref(null)
const list = ref([])
const versionGroups = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const form = reactive(defaultForm())
const editingCell = ref(null)

const importVisible = ref(false)
const importing = ref(false)
const importFile = ref(null)
const importResult = ref(null)
const uploadRef = ref(null)

function defaultForm() {
  return {
    seq: 0,
    req_no: '',
    req_url: '',
    title: '',
    owner: '',
    priority: 'P2',
    planned_version: '',
    progress_walkthrough: '未开始',
    progress_reverse: '未开始',
    progress_stc: '未开始',
    progress_coding: '未开始',
    progress_bbit: '未开始',
    progress_clarify: '未开始',
    remark: '',
  }
}

async function loadIteration() {
  try {
    const { data } = await annualIterationApi.get(iterationId)
    iteration.value = data
  } catch (e) {
    ElMessage.error('迭代不存在')
    router.push('/iterations')
  }
}

async function loadVersionGroups() {
  try {
    const { data } = await majorVersionApi.allIterationVersions()
    // Group by project_name > major_version_no
    const map = new Map()
    for (const v of data) {
      const groupLabel = v.project_name
        ? `${v.project_name} · ${v.major_version_no}`
        : v.major_version_no
      if (!map.has(groupLabel)) map.set(groupLabel, [])
      map.get(groupLabel).push(v)
    }
    versionGroups.value = Array.from(map.entries()).map(([label, options]) => ({ label, options }))
  } catch (e) {
    // non-fatal: dropdown just empty
  }
}

async function load() {
  loading.value = true
  try {
    const { data } = await iterationRequirementApi.list(iterationId)
    list.value = data
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/iterations')
}

function openCreate() {
  editing.value = null
  Object.assign(form, defaultForm())
  form.seq = (list.value.length || 0) + 1
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
      await iterationRequirementApi.update(editing.value.id, form)
      ElMessage.success('已更新')
      dialogVisible.value = false
      load()
    } else {
      await iterationRequirementApi.create({ ...form, iteration_id: iterationId })
      ElMessage.success('已创建')
      dialogVisible.value = false
      load()
    }
  } catch (e) {
    if (e.response?.status !== 409) ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确认删除需求「${row.req_no || row.title}」吗？`, '提示', { type: 'warning' })
  await iterationRequirementApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

// ===== 行内编辑 =====
function isEditing(row, field) {
  return editingCell.value && editingCell.value.id === row.id && editingCell.value.field === field
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
    const { data } = await iterationRequirementApi.update(row.id, { [field]: newVal, version: row.version })
    row.version = data.version
    ElMessage.success('已保存')
  } catch (e) {
    row[field] = original
    if (e.response?.status !== 409) ElMessage.error(e.response?.data?.detail || '保存失败')
    else load()
  }
}

async function onFieldChange(row, field, value) {
  const original = row[field]
  if (value === original) return
  try {
    const { data } = await iterationRequirementApi.update(row.id, { [field]: value, version: row.version })
    row[field] = value
    row.version = data.version
  } catch (e) {
    row[field] = original
    if (e.response?.status !== 409) ElMessage.error(e.response?.data?.detail || '保存失败')
    else load()
  }
}

async function onExport() {
  try {
    const resp = await annualIterationApi.exportPptx(iterationId)
    const tag = iteration.value ? `${iteration.value.year}-${String(iteration.value.month).padStart(2, '0')}` : iterationId
    downloadBlob(resp.data, `iteration-${tag}.pptx`)
    ElMessage.success('已导出')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '导出失败')
  }
}

// ===== 批量导入 =====
function openImport() {
  importFile.value = null
  importResult.value = null
  importVisible.value = true
  if (uploadRef.value) uploadRef.value.clearFiles?.()
}

function onExceed() {
  ElMessage.warning('一次仅可上传一个文件，请先移除已选文件')
}

function onFileChange(file) {
  importFile.value = file.raw
  importResult.value = null
}

async function onDownloadTemplate() {
  try {
    const resp = await iterationRequirementApi.importTemplate()
    downloadBlob(resp.data, 'iteration-requirements-template.xlsx')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '下载失败')
  }
}

async function onSubmitImport() {
  if (!importFile.value) {
    ElMessage.warning('请先选择 .xlsx 文件')
    return
  }
  importing.value = true
  try {
    const { data } = await iterationRequirementApi.importExcel(iterationId, importFile.value)
    importResult.value = data
    if (data.created > 0) {
      ElMessage.success(`成功导入 ${data.created} 条`)
      load()
    } else {
      ElMessage.warning('未导入任何数据')
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}

onMounted(() => {
  loadIteration()
  load()
  loadVersionGroups()
})
</script>

<style scoped>
.card {
  margin-top: 12px;
}
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
.remark-tag {
  margin-right: 6px;
}
.remark-text { color: #e6a23c; }
.remark-empty { color: #c0c4cc; }
.import-tip {
  color: #606266;
  line-height: 1.7;
  font-size: 13px;
  margin: 0 0 8px 0;
}
.import-result {
  margin-top: 12px;
}
.import-result :deep(.el-alert__description) {
  white-space: pre-wrap;
}
</style>
