<template>
  <div class="domain-page">
    <div class="page-head">
      <div class="head-left">
        <span class="muted">需求口径：</span>
        <el-tag type="primary" effect="plain">{{ data.iteration_label || '—' }}</el-tag>
        <span class="muted" style="margin-left: 16px">问题单：</span>
        <el-tag v-if="issueMeta.available" type="success" effect="plain">
          {{ issueMeta.file_mtime || '已接入' }}
        </el-tag>
        <el-tooltip v-else :content="issueMeta.note || '未接入'" placement="top">
          <el-tag type="info" effect="plain">未接入</el-tag>
        </el-tooltip>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
    </div>

    <el-table :data="data.rows" border stripe v-loading="loading" class="domain-table">
      <el-table-column label="领域" min-width="180" fixed>
        <template #default="{ row }">
          <div class="domain-name">{{ row.name }}</div>
          <div class="domain-meta">
            <el-tag v-if="row.dept_name" size="small" effect="plain">{{ row.dept_name }}</el-tag>
            <span v-if="row.leader_name" class="muted">PL：{{ row.leader_name }}</span>
            <span class="muted">{{ row.member_count }} 人</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="需求情况" min-width="200">
        <template #default="{ row }">
          <div v-if="row.req_summary.total" class="cell-clickable" @click="openReq(row)">
            <div class="sum-line">
              <b>{{ row.req_summary.total }}</b> 项
              <el-tag size="small" type="success" effect="plain">完成 {{ row.req_summary.done }}</el-tag>
              <el-tag size="small" type="warning" effect="plain">进行 {{ row.req_summary.in_progress }}</el-tag>
              <el-tag size="small" type="info" effect="plain">未开始 {{ row.req_summary.not_started }}</el-tag>
              <el-tag v-if="row.req_summary.delayed" size="small" type="danger">延期 {{ row.req_summary.delayed }}</el-tag>
            </div>
            <div class="prio-line">
              <span v-for="(n, p) in row.req_summary.by_priority" :key="p" class="prio">{{ p }}:{{ n }}</span>
            </div>
          </div>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>

      <el-table-column label="问题单情况" min-width="170">
        <template #default="{ row }">
          <template v-if="row.issue_summary.available">
            <div v-if="row.issue_summary.total" class="cell-clickable" @click="openIssues(row)">
              <b>{{ row.issue_summary.total }}</b> 个
              <span v-for="(n, s) in row.issue_summary.by_severity" :key="s">
                <el-tag size="small" :type="sevType(s)" effect="plain">{{ s }} {{ n }}</el-tag>
              </span>
            </div>
            <span v-else class="muted">无</span>
          </template>
          <span v-else class="muted">未接入</span>
        </template>
      </el-table-column>

      <el-table-column label="最近主要工作" min-width="260">
        <template #default="{ row }">
          <div v-if="row.recent_work" class="rich-cell" v-html="row.recent_work" />
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>

      <el-table-column label="风险与求助" min-width="240">
        <template #default="{ row }">
          <div v-if="row.risks && row.risks.length" class="risk-list">
            <div v-for="(r, i) in row.risks" :key="i" class="risk-item">
              <el-tag size="small" :type="r.type === '求助' ? 'warning' : 'danger'" effect="plain">{{ r.type }}</el-tag>
              <span class="risk-content">{{ r.content }}</span>
              <span v-if="r.status" class="muted">（{{ r.status }}）</span>
            </div>
          </div>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 编辑：最近主要工作 + 风险求助 -->
    <el-dialog v-model="editVisible" :title="`编辑 · ${editRow?.name || ''}`" width="760px" :close-on-click-modal="false">
      <div class="edit-section-title">最近主要工作</div>
      <RichTextEditor v-model="editForm.recent_work" min-height="140px" placeholder="本周期该领域的主要进展…" />

      <div class="edit-section-title" style="margin-top: 18px">
        风险与求助
        <el-button size="small" :icon="Plus" @click="addRisk">添加一条</el-button>
      </div>
      <div v-if="!editForm.risks.length" class="muted" style="padding: 8px 0">暂无，点击「添加一条」。</div>
      <div v-for="(r, i) in editForm.risks" :key="i" class="risk-edit-row">
        <el-select v-model="r.type" style="width: 90px">
          <el-option label="风险" value="风险" />
          <el-option label="求助" value="求助" />
        </el-select>
        <el-input v-model="r.content" placeholder="内容" />
        <el-input v-model="r.status" placeholder="状态/进展" style="width: 160px" />
        <el-button :icon="Delete" circle type="danger" plain @click="editForm.risks.splice(i, 1)" />
      </div>

      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 下钻：需求明细 -->
    <el-dialog v-model="reqVisible" :title="`需求明细 · ${drillName}`" width="900px">
      <el-table :data="reqRows" border stripe max-height="60vh" v-loading="reqLoading">
        <el-table-column label="编号" width="120">
          <template #default="{ row }">
            <a v-if="row.req_url" :href="row.req_url" target="_blank" class="link">{{ row.req_no || '查看' }}</a>
            <span v-else>{{ row.req_no || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="owner" label="责任人" width="90" />
        <el-table-column prop="priority" label="优先级" width="80" />
        <el-table-column v-for="c in PROG_COLS" :key="c.key" :label="c.label" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="progType(row[c.key])" effect="plain">{{ row[c.key] || '—' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 下钻：问题单 -->
    <el-dialog v-model="issueVisible" :title="`问题单 · ${drillName}`" width="900px">
      <el-table :data="issueRows" border stripe max-height="60vh" v-loading="issueLoading">
        <el-table-column prop="issue_id" label="编号" width="130" />
        <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="owner" label="责任人" width="90" />
        <el-table-column prop="severity" label="严重度" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="sevType(row.severity)" effect="plain">{{ row.severity || '—' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进展" min-width="160" show-overflow-tooltip />
        <el-table-column prop="version" label="版本" width="120" show-overflow-tooltip />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Plus, Refresh } from '@element-plus/icons-vue'
import { domainApi } from '../api'
import RichTextEditor from '../components/RichTextEditor.vue'

const PROG_COLS = [
  { key: 'progress_walkthrough', label: '需求串讲' },
  { key: 'progress_reverse', label: '反串讲' },
  { key: 'progress_stc', label: 'STC' },
  { key: 'progress_coding', label: '编码' },
  { key: 'progress_bbit', label: 'BBIT' },
  { key: 'progress_clarify', label: '转测澄清' },
]

const data = reactive({ iteration_label: '', rows: [] })
const issueMeta = reactive({ available: false, file_mtime: null, note: '' })
const loading = ref(false)

function sevType(s) {
  return { '严重': 'danger', '一般': 'warning', '提示': 'info' }[s] || 'info'
}
function progType(v) {
  return {
    '已完成': 'success', '进行中': 'warning', '已延期': 'danger',
    '已变更': 'warning', '未开始': 'info', '不涉及': 'info',
  }[v] || 'info'
}

async function load() {
  loading.value = true
  try {
    const { data: d } = await domainApi.list()
    data.iteration_label = d.iteration_label
    data.rows = d.rows
    // 问题单接入状态取首行（全表一致）
    const first = d.rows[0]?.issue_summary
    issueMeta.available = !!first?.available
    issueMeta.file_mtime = first?.file_mtime || null
    issueMeta.note = first?.note || ''
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

// ── 编辑 ──────────────────────────────────────────────
const editVisible = ref(false)
const editRow = ref(null)
const saving = ref(false)
const editForm = reactive({ recent_work: '', risks: [], version: 0 })

function openEdit(row) {
  editRow.value = row
  editForm.recent_work = row.recent_work || ''
  editForm.risks = (row.risks || []).map((r) => ({ ...r }))
  editForm.version = row.version || 0
  editVisible.value = true
}
function addRisk() {
  editForm.risks.push({ content: '', type: '风险', status: '' })
}
async function saveEdit() {
  saving.value = true
  try {
    const { data: updated } = await domainApi.updateContent(editRow.value.group_id, {
      recent_work: editForm.recent_work,
      risks: editForm.risks,
      version: editForm.version,
    })
    const idx = data.rows.findIndex((r) => r.group_id === updated.group_id)
    if (idx >= 0) data.rows[idx] = updated
    ElMessage.success('已保存')
    editVisible.value = false
  } catch (e) {
    // 409 由 axios 拦截器统一提示；这里刷新拿最新版本号
    if (e.response?.status === 409) {
      load()
      editVisible.value = false
    } else {
      ElMessage.error(e.response?.data?.detail || '保存失败')
    }
  } finally {
    saving.value = false
  }
}

// ── 下钻 ──────────────────────────────────────────────
const drillName = ref('')
const reqVisible = ref(false)
const reqLoading = ref(false)
const reqRows = ref([])
const issueVisible = ref(false)
const issueLoading = ref(false)
const issueRows = ref([])

async function openReq(row) {
  drillName.value = row.name
  reqVisible.value = true
  reqLoading.value = true
  reqRows.value = []
  try {
    const { data: rows } = await domainApi.requirements(row.group_id)
    reqRows.value = rows
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加载失败')
  } finally {
    reqLoading.value = false
  }
}
async function openIssues(row) {
  drillName.value = row.name
  issueVisible.value = true
  issueLoading.value = true
  issueRows.value = []
  try {
    const { data: res } = await domainApi.issues(row.group_id)
    issueRows.value = res.rows || []
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加载失败')
  } finally {
    issueLoading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.domain-page { padding: 4px; }
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.muted { color: #909399; font-size: 13px; }
.domain-name { font-weight: 600; }
.domain-meta { display: flex; align-items: center; gap: 6px; margin-top: 4px; flex-wrap: wrap; }
.cell-clickable { cursor: pointer; }
.cell-clickable:hover { color: #409EFF; }
.sum-line { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.prio-line { margin-top: 4px; }
.prio { color: #909399; font-size: 12px; margin-right: 8px; }
.rich-cell {
  max-height: 96px;
  overflow: auto;
  font-size: 13px;
  line-height: 1.5;
}
.risk-list { display: flex; flex-direction: column; gap: 4px; }
.risk-item { display: flex; align-items: baseline; gap: 6px; font-size: 13px; }
.risk-content { flex: 1; }
.edit-section-title {
  font-weight: 600;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.risk-edit-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.link, a.link { color: #409EFF; text-decoration: none; }
</style>
