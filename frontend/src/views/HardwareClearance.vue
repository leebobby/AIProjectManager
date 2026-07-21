<template>
  <div class="hw-page">
    <el-card shadow="never">
      <!-- ── 工具栏 ─────────────────────────────────── -->
      <div class="toolbar">
        <el-select v-model="filterCustomerId" placeholder="按战场筛选机台列" clearable filterable size="small" style="width:200px">
          <el-option v-for="b in battlefieldOptions" :key="b.customer_id" :label="b.battlefield" :value="b.customer_id" />
        </el-select>
        <el-input v-model="q" placeholder="搜索问题单 / 简述 / 部件 / 进展" clearable size="small" style="width:230px" :prefix-icon="Search" />

        <div class="toolbar-right">
          <span class="muted">共 {{ filteredRows.length }} 行 · {{ visibleMachines.length }} 台机台列</span>
          <el-button size="small" :type="editMode ? 'warning' : 'primary'" :icon="editMode ? Unlock : EditPen" @click="editMode = !editMode">
            {{ editMode ? '退出编辑' : '进入编辑' }}
          </el-button>
          <el-button size="small" :icon="Plus" :disabled="!editMode" @click="addRow">新增一行</el-button>
          <el-button size="small" text :icon="Document" @click="onImportTemplate">模板</el-button>
          <el-upload v-if="editMode" :auto-upload="false" :show-file-list="false" accept=".xlsx" :on-change="onImport">
            <el-button size="small" :icon="Upload" :loading="importing">导入</el-button>
          </el-upload>
          <el-button size="small" :icon="Download" :loading="exporting" @click="onExport">导出</el-button>
          <el-button v-if="isAdmin" size="small" :icon="Setting" @click="openConfig">配置</el-button>
        </div>
      </div>

      <!-- ── 主表（固定列 + 尾部机台列，横向滚动）─────────── -->
      <el-table :data="filteredRows" v-loading="loading" border stripe size="small"
                :row-class-name="rowClass" max-height="calc(100vh - 260px)">
        <el-table-column type="index" label="编号" width="56" align="center" fixed="left" />

        <el-table-column label="来源" min-width="110">
          <template #default="{ row }"><EditableCell :value="row.source" placeholder="—" @save="(v) => save(row, { source: v })" /></template>
        </el-table-column>
        <el-table-column label="问题单号" min-width="130">
          <template #default="{ row }"><EditableCell :value="row.issue_ref" placeholder="—" @save="(v) => save(row, { issue_ref: v })" /></template>
        </el-table-column>
        <el-table-column label="问题简述" min-width="200">
          <template #default="{ row }"><EditableCell :value="row.summary" multiline placeholder="点击填写" @save="(v) => save(row, { summary: v })" /></template>
        </el-table-column>
        <el-table-column label="更换部件" min-width="130">
          <template #default="{ row }"><EditableCell :value="row.replaced_part" placeholder="—" @save="(v) => save(row, { replaced_part: v })" /></template>
        </el-table-column>

        <el-table-column label="问题来源" width="130" align="center">
          <template #default="{ row }">
            <el-select :model-value="row.issue_source" size="small" clearable filterable placeholder="—"
                       :disabled="!editMode" @change="(v) => save(row, { issue_source: v || '' })">
              <el-option v-for="o in optionsWith(issueSources, row.issue_source)" :key="o" :label="o" :value="o" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="责任领域" width="130" align="center">
          <template #default="{ row }">
            <el-select :model-value="row.group_id" size="small" clearable filterable placeholder="—"
                       :disabled="!editMode" @change="(v) => save(row, { group_id: v ?? null })">
              <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="责任人" width="130" align="center">
          <template #default="{ row }">
            <el-select :model-value="row.owner_user_id" size="small" clearable filterable placeholder="未指派"
                       :disabled="!editMode" @change="(v) => save(row, { owner_user_id: v ?? null })">
              <el-option v-for="u in users" :key="u.id" :label="u.full_name || u.username" :value="u.id" />
            </el-select>
          </template>
        </el-table-column>

        <el-table-column label="CCB清零结论" min-width="160">
          <template #default="{ row }"><EditableCell :value="row.ccb_conclusion" multiline placeholder="—" @save="(v) => save(row, { ccb_conclusion: v })" /></template>
        </el-table-column>
        <el-table-column label="从#N发货清零" width="120" align="center">
          <template #default="{ row }"><EditableCell :value="row.ship_clear_from" placeholder="—" @save="(v) => save(row, { ship_clear_from: v })" /></template>
        </el-table-column>
        <el-table-column label="清零进展" min-width="160">
          <template #default="{ row }"><EditableCell :value="row.clear_progress" multiline placeholder="—" @save="(v) => save(row, { clear_progress: v })" /></template>
        </el-table-column>
        <el-table-column label="SOP情况" min-width="140">
          <template #default="{ row }"><EditableCell :value="row.sop_status" multiline placeholder="—" @save="(v) => save(row, { sop_status: v })" /></template>
        </el-table-column>

        <!-- 动态机台列 -->
        <el-table-column v-for="m in visibleMachines" :key="m.id" :label="m.machine_id" width="112" align="center" class-name="machine-col">
          <template #header>
            <router-link v-if="m.customer_id" :to="`/customers/${m.customer_id}?machine=${m.id}`" class="machine-link">{{ m.machine_id }}</router-link>
            <span v-else>{{ m.machine_id }}</span>
          </template>
          <template #default="{ row }">
            <el-select v-if="editMode" :model-value="cellVal(row, m.id)" size="small" clearable placeholder="—"
                       @change="(v) => saveCell(row, m.id, v)">
              <el-option v-for="o in optionsWith(cellOptions, cellVal(row, m.id))" :key="o" :label="o" :value="o" />
            </el-select>
            <span v-else class="status-chip" :class="{ empty: !cellVal(row, m.id) }" :style="chipStyle(cellVal(row, m.id))">
              {{ cellVal(row, m.id) || '—' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column v-if="isAdmin && editMode" label="操作" width="60" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" :icon="Delete" @click="onDelete(row)" />
          </template>
        </el-table-column>

        <template #empty>
          <div class="empty-hint">暂无硬件问题，点「新增一行」开始，或用「导入」批量导入。</div>
        </template>
      </el-table>

      <div class="legend muted">
        机台列表头可点击跳转到对应机台详情；单元格清零状态与「问题来源」的下拉选项在
        <template v-if="isAdmin"><el-link type="primary" @click="openConfig">配置</el-link></template>
        <template v-else>「配置」（管理员）</template>
        里维护。
      </div>
    </el-card>

    <!-- ── 管理员配置弹窗 ─────────────────────────────── -->
    <el-dialog v-model="cfgVisible" title="硬件问题清零 · 下拉选项配置" width="560px">
      <el-form label-position="top">
        <el-form-item label="问题来源选项（每行一个）">
          <el-input v-model="cfgForm.sources" type="textarea" :rows="5" placeholder="来料不良&#10;设计缺陷&#10;工艺问题" />
        </el-form-item>
        <el-form-item label="机台清零状态选项（每行一个）">
          <el-input v-model="cfgForm.cellOptions" type="textarea" :rows="5" placeholder="已清零&#10;未清零&#10;不涉及&#10;已发货待验证" />
        </el-form-item>
        <el-form-item label="状态颜色（可选，用于单元格着色）">
          <div class="color-map">
            <div v-for="opt in cfgCellOpts" :key="opt" class="color-row">
              <span class="status-chip" :style="cfgColors[opt] ? { backgroundColor: cfgColors[opt], color: '#fff', borderColor: cfgColors[opt] } : {}">{{ opt }}</span>
              <el-color-picker v-model="cfgColors[opt]" size="small" />
              <el-button v-if="cfgColors[opt]" link size="small" @click="cfgColors[opt] = ''">清除</el-button>
            </div>
            <div v-if="!cfgCellOpts.length" class="muted">先在上方填写状态选项，再为每个状态配色</div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cfgVisible = false">取消</el-button>
        <el-button type="primary" :loading="cfgSaving" @click="saveConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { ElInput, ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Document, Download, EditPen, Plus, Search, Setting, Unlock, Upload } from '@element-plus/icons-vue'
import { configApi, customerStatusApi, downloadBlob, hardwareIssueApi, resourceGroupApi, userApi } from '../api'
import { auth } from '../store/auth'
import { naturalCompare } from '../utils/format'

const isAdmin = auth.isAdmin

const rows = ref([])
const machines = ref([])
const users = ref([])
const groups = ref([])
const issueSources = ref([])
const cellOptions = ref([])
const loading = ref(false)
const exporting = ref(false)
const importing = ref(false)
const editMode = ref(false)        // 默认只读；进入编辑才可改，防止误改
const cellColors = ref({})         // {清零状态: 颜色}，用于机台格着色
const filterCustomerId = ref(null)
const q = ref('')

// 状态颜色的出厂默认（用户未配置时的建议值）
const DEFAULT_CELL_COLORS = { 已清零: '#67c23a', 未清零: '#e6a23c', 不涉及: '#909399' }

// ── 内联可编辑单元格（文本 / 多行）──
const EditableCell = defineComponent({
  props: {
    value: String,
    placeholder: { type: String, default: '点击填写' },
    multiline: { type: Boolean, default: false },
  },
  emits: ['save'],
  setup(props, { emit }) {
    const editing = ref(false)
    const draft = ref('')
    const start = () => {
      if (!editMode.value) return          // 只读模式不进入编辑
      draft.value = props.value || ''
      editing.value = true
    }
    const commit = () => {
      editing.value = false
      if (draft.value !== (props.value || '')) emit('save', draft.value)
    }
    return () => editing.value
      ? h(ElInput, {
          modelValue: draft.value, size: 'small', autofocus: true,
          type: props.multiline ? 'textarea' : 'text',
          autosize: props.multiline ? { minRows: 1, maxRows: 6 } : false,
          'onUpdate:modelValue': (v) => { draft.value = v },
          onBlur: commit,
          onKeyup: (e) => {
            if (e.key === 'Enter' && !props.multiline) commit()
            if (e.key === 'Escape') editing.value = false
          },
        })
      : h('span', {
          class: [
            props.value ? 'cell-text' : 'cell-text muted',
            props.multiline ? 'cell-multiline' : '',
            editMode.value ? '' : 'cell-readonly',
          ],
          onClick: start,
        }, props.value || (editMode.value ? props.placeholder : '—'))
  },
})

// 战场下拉：从机台去重派生，保证与实际机台一致
const battlefieldOptions = computed(() => {
  const seen = new Map()
  for (const m of machines.value) {
    if (m.customer_id && !seen.has(m.customer_id)) seen.set(m.customer_id, m.battlefield || '')
  }
  return [...seen.entries()].map(([customer_id, battlefield]) => ({ customer_id, battlefield }))
    .sort((a, b) => naturalCompare(a.battlefield, b.battlefield))
})

// 可见机台列：选了战场就只显示该战场机台
const visibleMachines = computed(() => {
  let ms = machines.value.slice()
  if (filterCustomerId.value) ms = ms.filter(m => m.customer_id === filterCustomerId.value)
  return ms.sort((a, b) => naturalCompare(a.battlefield || '', b.battlefield || '') || naturalCompare(a.machine_id, b.machine_id))
})

const filteredRows = computed(() => {
  if (!q.value.trim()) return rows.value
  const kw = q.value.trim().toLowerCase()
  return rows.value.filter(r =>
    (r.issue_ref || '').toLowerCase().includes(kw)
    || (r.summary || '').toLowerCase().includes(kw)
    || (r.replaced_part || '').toLowerCase().includes(kw)
    || (r.source || '').toLowerCase().includes(kw)
    || (r.clear_progress || '').toLowerCase().includes(kw)
    || (r.owner_display || '').toLowerCase().includes(kw))
})

function cellVal(row, machineId) {
  return (row.machine_cells && row.machine_cells[String(machineId)]) || ''
}
// 已有值但不在选项里时补进下拉，避免旧值显示不出来
function optionsWith(list, cur) {
  const arr = list.value ? list.value : list
  if (cur && !arr.includes(cur)) return [cur, ...arr]
  return arr
}

function rowClass({ row }) {
  // 全部机台格都「已清零」或含"清零"字样时整行浅绿，提示已收尾
  const vals = Object.values(row.machine_cells || {})
  if (vals.length && vals.every(v => v && v.includes('清零') && !v.includes('未'))) return 'row-done'
  return ''
}

async function reload() {
  loading.value = true
  try {
    const { data } = await hardwareIssueApi.list()
    rows.value = data
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

async function save(row, patch) {
  try {
    const { data } = await hardwareIssueApi.update(row.id, { version: row.version, ...patch })
    const i = rows.value.findIndex(r => r.id === row.id)
    if (i >= 0) rows.value[i] = data
  } catch (e) {
    // 乐观锁冲突：他人已改同一行，明确提示并拉最新，避免静默覆盖
    if (e.response?.status === 409) ElMessage.warning('该行已被他人修改，已刷新为最新数据，请重新编辑')
    else ElMessage.error(e.response?.data?.detail || '保存失败')
    reload()
  }
}

// 机台格按清零状态着色（读取模式显示彩色胶囊）
function chipStyle(val) {
  const c = val && cellColors.value[val]
  if (!c) return {}
  return { backgroundColor: c, color: '#fff', borderColor: c }
}

function saveCell(row, machineId, val) {
  const cells = { ...(row.machine_cells || {}) }
  if (val) cells[String(machineId)] = val
  else delete cells[String(machineId)]
  save(row, { machine_cells: cells })
}

async function addRow() {
  try {
    const { data } = await hardwareIssueApi.create({})
    rows.value.push(data)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '新增失败')
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除「${row.summary || '该行'}」吗？`, '提示', { type: 'warning' })
  } catch { return }
  try {
    await hardwareIssueApi.remove(row.id)
    rows.value = rows.value.filter(r => r.id !== row.id)
    ElMessage.success('已删除')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

async function onExport() {
  exporting.value = true
  try {
    const resp = await hardwareIssueApi.exportXlsx()
    const ts = new Date().toISOString().replace(/[:T]/g, '-').slice(0, 19)
    downloadBlob(resp.data, `硬件问题清零_${ts}.xlsx`)
    ElMessage.success('已导出')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '导出失败')
  } finally {
    exporting.value = false
  }
}

async function onImportTemplate() {
  try {
    const resp = await hardwareIssueApi.importTemplate()
    downloadBlob(resp.data, '硬件问题清零_导入模板.xlsx')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '模板下载失败')
  }
}

async function onImport(uploadFile) {
  const file = uploadFile?.raw
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.xlsx')) {
    ElMessage.error('仅支持 .xlsx 文件')
    return
  }
  importing.value = true
  try {
    const { data } = await hardwareIssueApi.importXlsx(file)
    await reload()
    const errs = data.errors || []
    if (errs.length) {
      ElMessageBox.alert(
        `成功导入 <b>${data.created}</b> 行，另有 <b>${errs.length}</b> 处未导入：<br><br>`
          + errs.map(e => `· ${e}`).join('<br>'),
        '导入完成（部分未成功）',
        { type: 'warning', dangerouslyUseHTMLString: true, customClass: 'hw-import-box' },
      )
    } else {
      ElMessage.success(`成功导入 ${data.created} 行`)
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '导入失败，请检查文件格式')
  } finally {
    importing.value = false
  }
}

// ── 配置 ──
const cfgVisible = ref(false)
const cfgSaving = ref(false)
const cfgForm = ref({ sources: '', cellOptions: '' })
const cfgColors = ref({})   // 弹窗内编辑中的 {状态: 颜色}

// 弹窗里根据"状态选项"文本实时解析出的选项列表，用来渲染配色行
const cfgCellOpts = computed(() => splitLines(cfgForm.value.cellOptions))

function openConfig() {
  cfgForm.value = {
    sources: (issueSources.value || []).join('\n'),
    cellOptions: (cellOptions.value || []).join('\n'),
  }
  // 未配过色的常见状态给出默认建议色，配过的沿用
  cfgColors.value = { ...DEFAULT_CELL_COLORS, ...(cellColors.value || {}) }
  cfgVisible.value = true
}

function splitLines(s) {
  return (s || '').split(/[\n;；,，]/).map(x => x.trim()).filter(Boolean)
}

async function saveConfig() {
  cfgSaving.value = true
  try {
    const sources = splitLines(cfgForm.value.sources)
    const cells = splitLines(cfgForm.value.cellOptions)
    // 只保留当前仍存在的选项的颜色，避免删了选项残留脏色
    const colors = {}
    for (const opt of cells) {
      if (cfgColors.value[opt]) colors[opt] = cfgColors.value[opt]
    }
    await configApi.save({
      hw_issue_sources: sources,
      hw_machine_cell_options: cells,
      hw_machine_cell_colors: colors,
    })
    issueSources.value = sources
    cellOptions.value = cells
    cellColors.value = colors
    cfgVisible.value = false
    ElMessage.success('已保存')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    cfgSaving.value = false
  }
}

async function loadConfig() {
  try {
    const { data } = await configApi.get()
    issueSources.value = Array.isArray(data.hw_issue_sources) ? data.hw_issue_sources : []
    cellOptions.value = Array.isArray(data.hw_machine_cell_options) ? data.hw_machine_cell_options : []
    cellColors.value = (data.hw_machine_cell_colors && typeof data.hw_machine_cell_colors === 'object')
      ? data.hw_machine_cell_colors : {}
  } catch { /* 静默 */ }
}

onMounted(async () => {
  const [ms, u, g] = await Promise.allSettled([
    customerStatusApi.list(),
    userApi.options({ only_can_login: true }),
    resourceGroupApi.list({ kind: 'pl' }),
  ])
  if (ms.status === 'fulfilled') machines.value = ms.value.data
  if (u.status === 'fulfilled') users.value = u.value.data
  if (g.status === 'fulfilled') groups.value = g.value.data
  await Promise.all([loadConfig(), reload()])
})
</script>

<style scoped>
.hw-page { display: flex; flex-direction: column; gap: 14px; }
.toolbar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.toolbar-right { display: flex; align-items: center; gap: 8px; margin-left: auto; }
.muted { color: #909399; font-size: 13px; }
.empty-hint { color: #909399; padding: 24px 0; }
.legend { margin-top: 10px; font-size: 12px; }

:deep(.row-done td.el-table__cell) { background: #f0f9eb !important; }
:deep(.machine-col) { background: #fafcff; }
:deep(.machine-link) { color: #409eff; text-decoration: none; }
:deep(.machine-link:hover) { text-decoration: underline; }
:deep(.cell-text) { cursor: pointer; display: inline-block; min-height: 20px; min-width: 40px; }
:deep(.cell-text:hover) { color: #409eff; }
:deep(.cell-multiline) { white-space: pre-wrap; line-height: 1.5; }
/* 只读模式：不显示可编辑的手型/悬停高亮 */
:deep(.cell-readonly) { cursor: default; }
:deep(.cell-readonly:hover) { color: inherit; }

/* 机台清零状态胶囊 */
.status-chip {
  display: inline-block; padding: 2px 10px; border-radius: 10px;
  border: 1px solid #dcdfe6; font-size: 12px; line-height: 18px; color: #606266;
}
.status-chip.empty { border-color: transparent; color: #c0c4cc; }

/* 配置弹窗：状态配色 */
.color-map { display: flex; flex-direction: column; gap: 8px; width: 100%; }
.color-row { display: flex; align-items: center; gap: 10px; }
.color-row .status-chip { min-width: 90px; text-align: center; }
</style>
