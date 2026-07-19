<template>
  <div class="track-page">
    <!-- ── 统计卡 ─────────────────────────────────── -->
    <div class="stat-row">
      <div class="stat-card" :class="{ active: !filters.status && !filters.overdue_only }" @click="resetStatusFilter">
        <div class="stat-num">{{ stats.open }}</div><div class="stat-label">未闭环</div>
      </div>
      <div class="stat-card crit" :class="{ active: filters.urgency === '重要紧急' }" @click="toggleFilter('urgency', '重要紧急')">
        <div class="stat-num">{{ stats.critical }}</div><div class="stat-label">重要紧急</div>
      </div>
      <div class="stat-card over" :class="{ active: filters.overdue_only }" @click="toggleOverdue">
        <div class="stat-num">{{ stats.overdue }}</div><div class="stat-label">逾期未闭环</div>
      </div>
      <div class="stat-card hold" :class="{ active: filters.status === '挂起' }" @click="toggleFilter('status', '挂起')">
        <div class="stat-num">{{ stats.on_hold }}</div><div class="stat-label">挂起</div>
      </div>
      <div class="stat-card done" :class="{ active: filters.status === 'CLOSED' }" @click="toggleFilter('status', 'CLOSED')">
        <div class="stat-num">{{ stats.closed }}</div><div class="stat-label">已闭环</div>
      </div>
    </div>

    <el-card shadow="never">
      <!-- ── 筛选栏 ───────────────────────────────── -->
      <div class="filter-bar">
        <el-select v-model="filters.customer_id" placeholder="战场" clearable size="small" style="width:150px" @change="reload">
          <el-option v-for="c in customers" :key="c.id" :label="c.display_name || c.code" :value="c.id" />
        </el-select>
        <el-select v-model="filters.kind" placeholder="类型" clearable size="small" style="width:130px" @change="reload">
          <el-option label="软件类问题" value="issue" />
          <el-option label="关键事务" value="task" />
        </el-select>
        <el-select v-model="filters.urgency" placeholder="紧急程度" clearable size="small" style="width:130px" @change="reload">
          <el-option v-for="u in URGENCIES" :key="u" :label="u" :value="u" />
        </el-select>
        <el-select v-model="filters.status" placeholder="状态" clearable size="small" style="width:120px" @change="reload">
          <el-option v-for="s in STATUSES" :key="s" :label="s" :value="s" />
        </el-select>
        <el-select v-model="filters.owner_user_id" placeholder="责任人" clearable filterable size="small" style="width:140px" @change="reload">
          <el-option v-for="u in users" :key="u.id" :label="u.full_name || u.username" :value="u.id" />
        </el-select>
        <el-input v-model="filters.q" placeholder="搜索描述 / 问题单 / 机台" clearable size="small" style="width:220px"
                  :prefix-icon="Search" @change="reload" />
        <el-checkbox v-model="includeClosed" size="small" @change="reload">含已闭环</el-checkbox>

        <div class="filter-right">
          <span class="muted">共 {{ rows.length }} 条</span>
          <el-button size="small" :icon="Refresh" @click="reload">刷新</el-button>
          <el-button size="small" :icon="Download" :loading="exporting" @click="onExport">导出 Excel</el-button>
        </div>
      </div>

      <!-- ── 主表 ─────────────────────────────────── -->
      <el-table :data="rows" v-loading="loading" border stripe size="small"
                :row-class-name="rowClass" max-height="calc(100vh - 320px)">
        <el-table-column prop="battlefield" label="战场" width="120" show-overflow-tooltip />
        <el-table-column prop="machine_id" label="机台" width="100" />
        <el-table-column label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.kind === 'issue' ? 'danger' : 'primary'" effect="plain">
              {{ row.kind === 'issue' ? '问题' : '事务' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="问题描述 / 任务" min-width="260">
          <template #default="{ row }">
            <EditableCell :value="row.description" type="text" @save="(v) => save(row, { description: v })" />
          </template>
        </el-table-column>

        <el-table-column label="关联问题单" width="150">
          <template #default="{ row }">
            <template v-if="row.kind === 'issue'">
              <EditableCell :value="row.issue_ref" type="text" placeholder="—"
                            @save="(v) => save(row, { issue_ref: v })" />
            </template>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>

        <el-table-column label="紧急程度" width="120" align="center">
          <template #default="{ row }">
            <el-select v-if="row.kind === 'issue'" :model-value="row.urgency" size="small"
                       @change="(v) => save(row, { urgency: v })">
              <el-option v-for="u in URGENCIES" :key="u" :label="u" :value="u" />
            </el-select>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>

        <el-table-column label="责任人" width="130" align="center">
          <template #default="{ row }">
            <el-select :model-value="row.owner_user_id" size="small" clearable filterable
                       placeholder="未指派" @change="(v) => save(row, { owner_user_id: v ?? null })">
              <el-option v-for="u in users" :key="u.id" :label="u.full_name || u.username" :value="u.id" />
            </el-select>
          </template>
        </el-table-column>

        <el-table-column label="提出时间" width="130" align="center">
          <template #default="{ row }">
            <el-date-picker :model-value="row.raised_at" type="date" size="small" value-format="YYYY-MM-DD"
                            placeholder="—" style="width:110px" @update:model-value="(v) => save(row, { raised_at: v || '' })" />
          </template>
        </el-table-column>

        <el-table-column label="预计闭环" width="130" align="center">
          <template #default="{ row }">
            <el-date-picker :model-value="row.due_date" type="date" size="small" value-format="YYYY-MM-DD"
                            placeholder="—" style="width:110px"
                            :class="{ 'dp-overdue': row.overdue }"
                            @update:model-value="(v) => save(row, { due_date: v || '' })" />
          </template>
        </el-table-column>

        <el-table-column label="闭环时间" width="110" align="center">
          <template #default="{ row }">
            <span :class="row.closed_at ? '' : 'muted'">{{ row.closed_at || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="110" align="center" fixed="right">
          <template #default="{ row }">
            <el-select :model-value="row.status" size="small" @change="(v) => save(row, { status: v })">
              <el-option v-for="s in STATUSES" :key="s" :label="s" :value="s" />
            </el-select>
          </template>
        </el-table-column>

        <el-table-column v-if="isAdmin" label="操作" width="70" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" :icon="Delete" @click="onDelete(row)" />
          </template>
        </el-table-column>
      </el-table>

      <div class="legend">
        <span><i class="dot d-open" />未闭环</span>
        <span><i class="dot d-hold" />挂起</span>
        <span><i class="dot d-done" />已闭环</span>
        <span><i class="dot d-over" />逾期</span>
        <span class="muted">条目在「客户面状态」总览的对应单元格里新增；此处维护跟踪信息。</span>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElInput, ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Download, Refresh, Search } from '@element-plus/icons-vue'
import { customerApi, customerIssueApi, downloadBlob, userApi } from '../api'
import { auth } from '../store/auth'

const route = useRoute()
const isAdmin = auth.isAdmin

// 与后端 enums.py 保持一致
const URGENCIES = ['重要紧急', '紧急', '一般']
const STATUSES = ['OPEN', 'CLOSED', '挂起']

// ── 内联组件：点击即改的文本单元格 ────────────────────
const EditableCell = defineComponent({
  props: { value: String, placeholder: { type: String, default: '点击填写' } },
  emits: ['save'],
  setup(props, { emit }) {
    const editing = ref(false)
    const draft = ref('')
    const start = () => { draft.value = props.value || ''; editing.value = true }
    const commit = () => {
      editing.value = false
      if (draft.value !== (props.value || '')) emit('save', draft.value)
    }
    return () => editing.value
      ? h(ElInput, {
          modelValue: draft.value, size: 'small', autofocus: true,
          'onUpdate:modelValue': (v) => { draft.value = v },
          onBlur: commit, onKeyup: (e) => { if (e.key === 'Enter') commit(); if (e.key === 'Escape') editing.value = false },
        })
      : h('span', {
          class: props.value ? 'cell-text' : 'cell-text muted',
          onClick: start,
        }, props.value || props.placeholder)
  },
})

const rows = ref([])
const users = ref([])
const customers = ref([])
const loading = ref(false)
const exporting = ref(false)
const includeClosed = ref(false)
const stats = reactive({ open: 0, closed: 0, on_hold: 0, critical: 0, overdue: 0, total: 0 })

const filters = reactive({
  customer_id: null, kind: null, urgency: null, status: null,
  owner_user_id: null, q: '', overdue_only: false,
})

// 从总览点条目跳过来时高亮那一条
const focusId = computed(() => Number(route.query.focus) || null)

function rowClass({ row }) {
  if (row.id === focusId.value) return 'row-focus'
  if (row.status === 'CLOSED') return 'row-done'
  if (row.status === '挂起') return 'row-hold'
  if (row.overdue) return 'row-overdue'
  return ''
}

function toggleFilter(key, val) {
  filters[key] = filters[key] === val ? null : val
  if (key === 'status' && filters.status === 'CLOSED') includeClosed.value = true
  filters.overdue_only = false
  reload()
}
function toggleOverdue() {
  filters.overdue_only = !filters.overdue_only
  reload()
}
function resetStatusFilter() {
  filters.status = null
  filters.urgency = null
  filters.overdue_only = false
  reload()
}

async function reload() {
  loading.value = true
  try {
    const params = { include_closed: includeClosed.value }
    for (const [k, v] of Object.entries(filters)) {
      if (v !== null && v !== '' && v !== false) params[k] = v
    }
    const [listRes, sumRes] = await Promise.all([
      customerIssueApi.list(params),
      customerIssueApi.summary(),
    ])
    rows.value = listRes.data
    Object.assign(stats, sumRes.data)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

// 逐格保存：后端会在状态流转时自动维护闭环时间，所以保存后用返回值整行替换
async function save(row, patch) {
  try {
    const { data } = await customerIssueApi.update(row.id, { version: row.version, ...patch })
    const idx = rows.value.findIndex((r) => r.id === row.id)
    if (idx >= 0) rows.value[idx] = data
    // 状态类改动会影响统计卡，刷一下数字
    if ('status' in patch || 'urgency' in patch || 'due_date' in patch) {
      customerIssueApi.summary().then(({ data: s }) => Object.assign(stats, s)).catch(() => {})
    }
  } catch (e) {
    if (e.response?.status !== 409) ElMessage.error(e.response?.data?.detail || '保存失败')
    reload()
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除「${row.description || '该条目'}」吗？`, '提示', { type: 'warning' })
  } catch { return }
  try {
    await customerIssueApi.remove(row.id)
    ElMessage.success('已删除')
    reload()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

async function onExport() {
  exporting.value = true
  try {
    const resp = await customerIssueApi.exportXlsx(includeClosed.value)
    const ts = new Date().toISOString().replace(/[:T]/g, '-').slice(0, 19)
    downloadBlob(resp.data, `客户面问题跟踪_${ts}.xlsx`)
    ElMessage.success('已导出')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '导出失败')
  } finally {
    exporting.value = false
  }
}

// 带 focus 参数进来时，把已闭环也放开，否则点进来可能一片空白
watch(focusId, (v) => { if (v) includeClosed.value = true }, { immediate: true })

onMounted(async () => {
  const [u, c] = await Promise.allSettled([userApi.options({ only_can_login: true }), customerApi.list()])
  if (u.status === 'fulfilled') users.value = u.value.data
  if (c.status === 'fulfilled') customers.value = c.value.data
  await reload()
})
</script>

<style scoped>
.track-page { display: flex; flex-direction: column; gap: 14px; }

/* 统计卡 */
.stat-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
.stat-card {
  background: #fff; border: 1px solid #eaecef; border-radius: 10px;
  padding: 14px 20px; cursor: pointer; text-align: center; transition: all .2s;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px -12px rgba(31,45,61,.3); }
.stat-card.active { border-color: #409eff; box-shadow: 0 0 0 2px #ecf5ff inset; }
.stat-num { font-size: 28px; font-weight: 700; color: #1f2329; line-height: 1.1; }
.stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
.crit .stat-num { color: #f56c6c; }
.over .stat-num { color: #e6a23c; }
.hold .stat-num { color: #909399; }
.done .stat-num { color: #67c23a; }

/* 筛选栏 */
.filter-bar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.filter-right { display: flex; align-items: center; gap: 8px; margin-left: auto; }
.muted { color: #909399; font-size: 13px; }

/* 行着色：已闭环整行变灰 + 删除线，挂起偏黄，逾期偏红 */
:deep(.row-done) { background: #fafafa !important; color: #a8abb2; }
:deep(.row-done .cell-text) { text-decoration: line-through; color: #a8abb2; }
:deep(.row-hold) { background: #fdf9f0 !important; }
:deep(.row-overdue) { background: #fef4f4 !important; }
:deep(.row-focus) { background: #ecf5ff !important; box-shadow: inset 3px 0 0 #409eff; }

:deep(.cell-text) { cursor: pointer; display: inline-block; min-height: 20px; min-width: 40px; }
:deep(.cell-text:hover) { color: #409eff; }
:deep(.dp-overdue .el-input__inner) { color: #f56c6c; }

/* 图例 */
.legend { display: flex; align-items: center; gap: 16px; margin-top: 10px; font-size: 12px; color: #606266; }
.legend .dot { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 5px; vertical-align: -1px; }
.d-open { background: #fff; border: 1px solid #dcdfe6; }
.d-hold { background: #fdf9f0; border: 1px solid #f3d19e; }
.d-done { background: #fafafa; border: 1px solid #dcdfe6; }
.d-over { background: #fef4f4; border: 1px solid #fab6b6; }
</style>
