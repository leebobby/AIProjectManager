<template>
  <div v-loading="loading" class="special-page">
    <div v-if="special" class="page-card">
      <!-- 编辑锁提示：他人正在编辑时，本页为只读 -->
      <el-alert
        v-if="lockedByOther"
        type="warning"
        :closable="false"
        show-icon
        class="lock-banner"
        :title="`${lock.by || '他人'} 正在编辑${lock.since ? `（自 ${fmtSince(lock.since)}）` : ''}，当前为只读模式${auth.isAdmin.value ? '；管理员可点右上角「强制接管」' : '，请稍后再试'}`"
      />
      <!-- 标题 -->
      <div class="sec-title-main">
        <el-tag :type="isAssault ? 'danger' : 'info'" effect="dark" style="margin-right: 8px">{{ label }}</el-tag>
        <span>{{ special.name }}</span>
        <div class="owner-and-actions">
          <span class="owner">责任人：{{ special.owner || '-' }}</span>
          <SubscribeButton source-type="special" :source-id="Number(route.params.id)" />
          <el-button
            v-if="auth.isLoggedIn.value"
            size="small"
            :type="editMode ? 'success' : (lockedByOther ? 'info' : 'warning')"
            :icon="editMode ? Check : EditPen"
            :disabled="lockedByOther && !auth.isAdmin.value"
            :loading="extraSaving || formationSaving"
            @click="toggleEdit"
          >{{ editBtnLabel }}</el-button>
          <el-button size="small" :icon="Download" @click="onExportXlsx">导出 Excel</el-button>
          <el-button size="small" type="primary" :icon="Message" @click="openReportDialog">发周报</el-button>
        </div>
      </div>

      <!-- 1. 目标 -->
      <div class="sec">
        <div class="sec-head">{{ label }}目标</div>
        <div class="sec-body">
          <EditableText
            :value="content.goal"
            :editable="canEdit"
            rich
            :placeholder="`点击填写${label}目标...`"
            @save="onSaveField('goal', $event)"
          />
        </div>
      </div>

      <!-- 2. 计划 -->
      <div class="sec">
        <div class="sec-head">
          <span>{{ label }}计划</span>
          <el-button v-if="canEdit" size="small" :icon="Plus" @click="openMilestoneDialog(null)">新增里程碑</el-button>
        </div>
        <div class="sec-body">
          <MilestoneTimeline
            :milestones="milestones"
            :editable="canEdit"
            @edit="openMilestoneDialog"
            @remove="onRemoveMilestone"
          />
        </div>
      </div>

      <!-- 3. 整体进展 -->
      <div class="sec">
        <div class="sec-head">整体进展</div>
        <div class="sec-body">
          <EditableText
            :value="content.progress_summary"
            :editable="canEdit"
            rich
            placeholder="本周完成 xx 工作内容，整体进展..."
            @save="onSaveField('progress_summary', $event)"
          />
        </div>
      </div>

      <!-- 4. 求助 -->
      <div class="sec">
        <div class="sec-head">求助</div>
        <div class="sec-body">
          <EditableText
            :value="content.help_request"
            :editable="canEdit"
            rich
            placeholder="需要协调的资源 / 需上级支持的事项..."
            @save="onSaveField('help_request', $event)"
          />
        </div>
      </div>

      <!-- 4. 全景图 -->
      <div class="sec">
        <div class="sec-head">
          <span>{{ label }}全景图</span>
          <span class="muted-hint">{{ isAssault ? '建议使用思维导图（支持 SVG）' : '建议使用逻辑框图（支持 SVG）' }}</span>
          <el-upload
            v-if="canEdit"
            :auto-upload="false"
            :on-change="onUploadPanorama"
            :show-file-list="false"
            accept="image/*,.svg"
          >
            <el-button size="small">{{ content.panorama_image_name ? '替换图片' : '上传图片' }}</el-button>
          </el-upload>
        </div>
        <div class="sec-body panorama-body">
          <img v-if="panoramaSrc" :src="panoramaSrc" :alt="`${label}全景图`" class="panorama-img" />
          <div v-else class="panorama-empty">还没有上传{{ label }}全景图</div>
        </div>
      </div>

      <!-- 5. 风险和问题（调整到事务之前） -->
      <div class="sec">
        <div class="sec-head">
          <span>风险和问题</span>
          <el-button v-if="canEdit" size="small" :icon="Plus" @click="openItemDialog('risk', null)">新增风险</el-button>
          <el-checkbox v-model="showClosedRisks" size="small" class="closed-toggle">显示已闭环</el-checkbox>
        </div>
        <el-table :data="visibleRisks" :row-class-name="rowClass" border stripe size="small" style="width: 100%">
          <el-table-column type="index" label="序号" width="70" align="center" />
          <el-table-column prop="content" label="问题内容" min-width="240">
            <template #default="{ row }">
              <div class="cell-multiline rich-cell" v-html="row.content || '-'" />
            </template>
          </el-table-column>
          <el-table-column prop="progress" label="当前进展" min-width="200">
            <template #default="{ row }">
              <div class="cell-multiline rich-cell" v-html="row.progress || '-'" />
            </template>
          </el-table-column>
          <el-table-column prop="owner" label="责任人" width="110" />
          <el-table-column prop="planned_close_date" label="计划闭环时间" width="130" />
          <el-table-column label="当前状态" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'closed' ? 'success' : 'warning'" size="small" effect="plain">
                {{ row.status === 'closed' ? 'Closed' : 'Open' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column v-if="canEdit" label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openItemDialog('risk', row)">编辑</el-button>
              <el-button size="small" type="danger" @click="onRemoveItem('risk', row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 6. 事务 -->
      <div class="sec">
        <div class="sec-head">
          <span>{{ label }}事务</span>
          <el-button v-if="canEdit" size="small" :icon="Plus" @click="openItemDialog('task', null)">新增事务</el-button>
          <el-button v-if="canEdit" size="small" @click="addExtraGrid">+ 添加表格</el-button>
          <el-checkbox v-model="showClosedTasks" size="small" class="closed-toggle">显示已闭环</el-checkbox>
        </div>
        <el-table :data="visibleTasks" :row-class-name="rowClass" border stripe size="small" style="width: 100%">
          <el-table-column type="index" label="序号" width="70" align="center" />
          <el-table-column prop="content" label="事务内容" min-width="240">
            <template #default="{ row }">
              <div class="cell-multiline rich-cell" v-html="row.content || '-'" />
            </template>
          </el-table-column>
          <el-table-column prop="progress" label="当前进展" min-width="200">
            <template #default="{ row }">
              <div class="cell-multiline rich-cell" v-html="row.progress || '-'" />
            </template>
          </el-table-column>
          <el-table-column prop="owner" label="责任人" width="110" />
          <el-table-column prop="planned_close_date" label="计划闭环时间" width="130" />
          <el-table-column label="当前状态" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'closed' ? 'success' : 'warning'" size="small" effect="plain">
                {{ row.status === 'closed' ? 'Closed' : 'Open' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column v-if="canEdit" label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openItemDialog('task', row)">编辑</el-button>
              <el-button size="small" type="danger" @click="onRemoveItem('task', row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 附加自由表格（每个专项独立，按 _uid 作为稳定 key 避免切换专项串台） -->
        <div v-for="(grid, gi) in extraGrids" :key="grid._uid" class="extra-grid">
          <div class="extra-grid-head">
            <input
              v-if="canEdit"
              v-model="grid.title"
              class="extra-grid-title-input"
              placeholder="表格标题（点击编辑）"
            />
            <span v-else>{{ grid.title || '附加表格' }}</span>
            <div class="spacer" />
            <el-button v-if="canEdit" size="small" type="danger" @click="removeExtraGrid(gi)">删除整表</el-button>
          </div>
          <RichGrid v-model="extraGrids[gi]" :editable="canEdit" />
        </div>
        <div v-if="canEdit && extraGrids.length > 0" class="save-extra">
          <el-button size="small" type="primary" :loading="extraSaving" @click="saveExtraGrids">保存附加表格</el-button>
        </div>
      </div>

      <!-- 7. 阵型 -->
      <div class="sec">
        <div class="sec-head">
          <span>{{ label }}阵型</span>
          <template v-if="canEdit">
            <el-button size="small" @click="addFormationRow">+行</el-button>
            <el-button size="small" @click="addFormationCol">+列</el-button>
            <el-button size="small" @click="saveFormation" :loading="formationSaving">保存阵型</el-button>
          </template>
        </div>
        <div class="formation-wrap">
          <FormationGrid v-if="formation.headers.length || formation.rows.length" v-model="formation" :editable="canEdit" />
          <div v-else class="muted">点击 +列 / +行 开始填写阵型</div>
        </div>
      </div>
    </div>

    <!-- 里程碑对话框 -->
    <el-dialog v-model="msDialog.visible" :title="msDialog.editing != null ? '编辑里程碑' : '新增里程碑'" width="480px">
      <el-form :model="msDialog.form" label-width="80px">
        <el-form-item label="名称">
          <el-input
            v-model="msDialog.form.name"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 6 }"
            placeholder="可输入多行，例如&#10;1. 完成 xxx&#10;2. 输出 yyy"
          />
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker v-model="msDialog.form.date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="msDialog.form.status" style="width: 100%">
            <el-option label="未开始" value="planning" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="done" />
            <el-option label="已延期" value="delayed" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="msDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="onSaveMilestone">保存</el-button>
      </template>
    </el-dialog>

    <!-- 事务/风险 对话框 -->
    <el-dialog
      v-model="itemDialog.visible"
      :title="(itemDialog.editing ? '编辑' : '新增') + (itemDialog.kind === 'task' ? '事务' : '风险/问题')"
      width="520px"
    >
      <el-form :model="itemDialog.form" label-width="100px">
        <el-form-item :label="itemDialog.kind === 'task' ? '事务内容' : '问题内容'">
          <RichTextEditor v-model="itemDialog.form.content" min-height="90px" placeholder="支持加粗 / 字号 / 颜色" />
        </el-form-item>
        <el-form-item label="当前进展">
          <RichTextEditor v-model="itemDialog.form.progress" min-height="70px" placeholder="支持加粗 / 字号 / 颜色" />
        </el-form-item>
        <el-form-item label="责任人">
          <el-input v-model="itemDialog.form.owner" />
        </el-form-item>
        <el-form-item label="计划闭环时间">
          <el-input v-model="itemDialog.form.planned_close_date" placeholder="YYYY-MM-DD 或自由文本" />
        </el-form-item>
        <el-form-item label="当前状态">
          <el-radio-group v-model="itemDialog.form.status">
            <el-radio value="open">Open</el-radio>
            <el-radio value="closed">Closed</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="itemDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="onSaveItem">保存</el-button>
      </template>
    </el-dialog>

    <!-- 周报草稿对话框 -->
    <el-dialog v-model="reportDialog.visible" :title="`${label}周报草稿`" width="720px" top="6vh">
      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 12px"
      >
        <template #title>
          下载 <code>.eml</code> 后双击即可在 Outlook / Foxmail 等邮件客户端中以草稿形式打开，
          内容包含富文本表格的 HTML 版本，发件人地址留空由你本地客户端自动填上。
        </template>
      </el-alert>
      <el-form :model="reportDialog.form" label-width="80px" v-loading="reportDialog.loading">
        <el-form-item label="主送">
          <el-input v-model="reportDialog.form.to" placeholder="多个邮箱用 , 分隔" />
        </el-form-item>
        <el-form-item label="抄送">
          <el-input v-model="reportDialog.form.cc" placeholder="多个邮箱用 , 分隔（可空）" />
        </el-form-item>
        <el-form-item label="主题">
          <el-input v-model="reportDialog.form.subject" />
        </el-form-item>
        <el-form-item label="正文">
          <el-input v-model="reportDialog.form.body" type="textarea" :rows="12" />
          <div class="report-tip">.eml 中的纯文本部分使用此正文；HTML 富文本部分基于当前页面数据由后端实时美化渲染。</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reportDialog.visible = false">关闭</el-button>
        <el-button @click="onCopyReport">复制纯文本</el-button>
        <el-button type="primary" :icon="Download" :loading="reportDialog.downloading" @click="onDownloadEml">下载 .eml</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Download, EditPen, Message, Plus } from '@element-plus/icons-vue'
import http, { specialApi, downloadBlob } from '../api'
import { auth } from '../store/auth'
import { checkStorageOrWarn } from '../store/storage'
import EditableText from '../components/EditableText.vue'
import MilestoneTimeline from '../components/MilestoneTimeline.vue'
import FormationGrid from '../components/FormationGrid.vue'
import RichGrid from '../components/RichGrid.vue'
import RichTextEditor from '../components/RichTextEditor.vue'
import SubscribeButton from '../components/SubscribeButton.vue'

const route = useRoute()
const loading = ref(false)
const special = ref(null)
const content = ref({
  goal: '', progress_summary: '', help_request: '',
  panorama_image_path: '', panorama_image_name: '',
  milestones_json: '[]',
  formation_json: '{"headers":[],"rows":[]}',
  extra_grids_json: '[]',
  version: 0,
})
const tasks = ref([])
const risks = ref([])
const milestones = ref([])
const formation = ref({ headers: [], rows: [] })
const extraGrids = ref([])
const extraSaving = ref(false)
const formationSaving = ref(false)
const panoramaSrc = ref('')

const isAssault = computed(() => special.value?.kind === 'assault')
const label = computed(() => (isAssault.value ? '攻关' : '专项'))

// 编辑模式：登录用户点击「进入编辑」后才显示各类编辑控件，点「完成编辑」退出
const editMode = ref(false)
const canEdit = computed(() => auth.isLoggedIn.value && editMode.value)

// 编辑锁：同一专项同一时刻只允许一人编辑
const lock = ref({ locked: false, mine: false, by: null, by_user_id: null, since: null, ttl: 180 })
const lockedByOther = computed(() => lock.value.locked && !lock.value.mine)
const editBtnLabel = computed(() => {
  if (editMode.value) return '完成编辑'
  if (lockedByOther.value) return auth.isAdmin.value ? '强制接管' : '他人编辑中'
  return '进入编辑'
})
let heartbeatTimer = null
let pollTimer = null
let loadToken = 0

function fmtSince(s) {
  if (!s) return ''
  const iso = /[zZ]|[+-]\d\d:?\d\d$/.test(s) ? s : `${s}Z` // 后端为 UTC，无时区后缀时补 Z
  const d = new Date(iso)
  return isNaN(d.getTime()) ? '' : d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

async function refreshLock() {
  if (!special.value) return
  try {
    const { data } = await specialApi.getLock(special.value.id)
    if (!editMode.value) lock.value = data
  } catch { /* 忽略查询失败 */ }
}

function startHeartbeat() {
  stopHeartbeat()
  // TTL 180s，每 60s 续期一次
  heartbeatTimer = setInterval(async () => {
    if (!special.value) return
    try {
      const { data } = await specialApi.acquireLock(special.value.id)
      lock.value = data
      if (!data.mine) {
        // 编辑权被管理员强制接管 → 退回只读，避免之后保存白费
        stopHeartbeat()
        editMode.value = false
        ElMessage.warning(`编辑权已被 ${data.by || '他人'} 接管，已切换为只读`)
      }
    } catch { /* 网络抖动忽略，靠下次续期或 TTL */ }
  }, 60000)
}
function stopHeartbeat() {
  if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null }
}
function startPoll() {
  stopPoll()
  pollTimer = setInterval(refreshLock, 20000)
}
function stopPoll() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

// 取锁并进入编辑；force=管理员强制接管
async function enterEdit(force = false) {
  try {
    const { data } = await specialApi.acquireLock(special.value.id, force)
    lock.value = data
    if (!data.mine) {
      if (auth.isAdmin.value) {
        try {
          await ElMessageBox.confirm(
            `${data.by || '他人'} 正在编辑该${label.value}，是否强制接管？接管后对方将无法保存其改动。`,
            '该内容正被编辑',
            { type: 'warning', confirmButtonText: '强制接管', cancelButtonText: '仅查看' },
          )
        } catch { return } // 取消 = 保持只读
        return enterEdit(true)
      }
      ElMessage.warning(`${data.by || '他人'} 正在编辑，当前为只读`)
      return
    }
    editMode.value = true
    startHeartbeat()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '进入编辑失败')
  }
}

// 释放锁（持锁人退出 / 离开页面），best-effort
async function releaseLockSafe() {
  stopHeartbeat()
  if (editMode.value && lock.value.mine && special.value) {
    try { await specialApi.releaseLock(special.value.id) } catch { /* ignore */ }
  }
  editMode.value = false
  lock.value = { locked: false, mine: false, by: null, by_user_id: null, since: null, ttl: 180 }
}

// 已闭环（closed）事项的显示开关
const showClosedTasks = ref(true)
const showClosedRisks = ref(true)
const visibleTasks = computed(() =>
  showClosedTasks.value ? tasks.value : tasks.value.filter(t => (t.status || 'open') !== 'closed'),
)
const visibleRisks = computed(() =>
  showClosedRisks.value ? risks.value : risks.value.filter(r => (r.status || 'open') !== 'closed'),
)
function rowClass({ row }) {
  return (row.status || 'open') === 'closed' ? 'closed-row' : ''
}

async function toggleEdit() {
  if (!editMode.value) {
    await enterEdit()
    return
  }
  // 退出编辑前，把附加表格 / 阵型的未保存改动一并落库
  if (extraGrids.value.length > 0) await saveExtraGrids(true)
  if (formation.value.headers.length || formation.value.rows.length) await saveFormation(true)
  await releaseLockSafe()
  ElMessage.success('已退出编辑模式')
}

const msDialog = reactive({ visible: false, editing: null, form: { name: '', date: '', status: 'planning' } })
const itemDialog = reactive({ visible: false, editing: null, kind: 'task', form: defaultItem() })
const reportDialog = reactive({
  visible: false,
  loading: false,
  downloading: false,
  form: { to: '', cc: '', subject: '', body: '' },
})

function defaultItem() {
  return { content: '', progress: '', owner: '', planned_close_date: '', status: 'open' }
}

async function load() {
  // 请求令牌：若 await 期间又发起了新的一次 load，则丢弃本次迟到响应，避免写错专项
  const myToken = ++loadToken
  loading.value = true
  try {
    const id = route.params.id
    const { data } = await specialApi.detail(id)
    if (myToken !== loadToken) return
    special.value = data
    content.value = data.content || content.value
    tasks.value = data.tasks || []
    risks.value = data.risks || []
    parseMilestones()
    parseFormation()
    parseExtraGrids()
    await loadPanorama()
    if (myToken !== loadToken) return
    await refreshLock()
  } catch (e) {
    if (myToken === loadToken) ElMessage.error(e.response?.data?.detail || '加载失败')
  } finally {
    if (myToken === loadToken) loading.value = false
  }
}

function parseMilestones() {
  try {
    const arr = JSON.parse(content.value.milestones_json || '[]')
    milestones.value = Array.isArray(arr) ? arr : []
  } catch { milestones.value = [] }
}

function parseFormation() {
  try {
    const obj = JSON.parse(content.value.formation_json || '{}')
    formation.value = {
      headers: Array.isArray(obj.headers) ? [...obj.headers] : [],
      rows: Array.isArray(obj.rows) ? obj.rows.map(r => [...r]) : [],
    }
  } catch { formation.value = { headers: [], rows: [] } }
}

let _gridUid = 0

function normHeader(h) {
  if (h && typeof h === 'object') {
    return { text: String(h.text ?? ''), colspan: Number(h.colspan) || 1, align: h.align || 'center' }
  }
  return { text: String(h ?? ''), colspan: 1, align: 'center' }
}
function normCell(c) {
  if (c && typeof c === 'object') {
    return { text: String(c.text ?? ''), align: c.align || 'left', color: c.color || '' }
  }
  return { text: String(c ?? ''), align: 'left', color: '' }
}
const DEFAULT_COL_W = 130
function normGrid(g) {
  const headers = Array.isArray(g.headers) ? g.headers.map(normHeader) : []
  const rows = Array.isArray(g.rows) ? g.rows.map(r => (Array.isArray(r) ? r.map(normCell) : [])) : []
  const bodyCols = headers.reduce((n, h) => n + (Number(h.colspan) || 1), 0)
  // 列宽随表持久化；旧数据无 colWidths 时按默认值补齐到正文列数
  let widths = Array.isArray(g.colWidths) ? g.colWidths.map(w => Number(w) || DEFAULT_COL_W) : []
  if (widths.length < bodyCols) widths = widths.concat(Array(bodyCols - widths.length).fill(DEFAULT_COL_W))
  else if (widths.length > bodyCols) widths = widths.slice(0, bodyCols)
  return {
    _uid: `g${++_gridUid}`,
    title: String(g.title || ''),
    headers,
    rows,
    colWidths: widths,
  }
}

function parseExtraGrids() {
  try {
    const arr = JSON.parse(content.value.extra_grids_json || '[]')
    extraGrids.value = Array.isArray(arr) ? arr.map(normGrid) : []
  } catch { extraGrids.value = [] }
}

async function loadPanorama() {
  if (!special.value || !content.value.panorama_image_path) {
    panoramaSrc.value = ''
    return
  }
  try {
    const resp = await http.get(`/specials/${special.value.id}/panorama`, { responseType: 'blob' })
    if (panoramaSrc.value) URL.revokeObjectURL(panoramaSrc.value)
    panoramaSrc.value = URL.createObjectURL(resp.data)
  } catch {
    panoramaSrc.value = ''
  }
}

async function onSaveField(key, val) {
  if (!special.value) return
  try {
    const { data } = await specialApi.updateContent(special.value.id, {
      version: content.value.version,
      [key]: val,
    })
    content.value = data
    ElMessage.success('已保存')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

// 里程碑
function openMilestoneDialog(idx) {
  if (idx == null) {
    msDialog.editing = null
    msDialog.form = { name: '', date: '', status: 'planning' }
  } else {
    msDialog.editing = idx
    msDialog.form = { ...milestones.value[idx] }
  }
  msDialog.visible = true
}

async function onSaveMilestone() {
  if (!msDialog.form.name.trim()) {
    ElMessage.warning('请输入名称')
    return
  }
  const next = milestones.value.slice()
  if (msDialog.editing != null) next[msDialog.editing] = { ...msDialog.form }
  else next.push({ ...msDialog.form })
  next.sort((a, b) => (a.date || '').localeCompare(b.date || ''))
  try {
    const { data } = await specialApi.updateContent(special.value.id, {
      version: content.value.version,
      milestones_json: JSON.stringify(next),
    })
    content.value = data
    parseMilestones()
    msDialog.visible = false
    ElMessage.success('已保存')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

async function onRemoveMilestone(idx) {
  await ElMessageBox.confirm('确认删除该里程碑？', '提示', { type: 'warning' })
  const next = milestones.value.slice()
  next.splice(idx, 1)
  try {
    const { data } = await specialApi.updateContent(special.value.id, {
      version: content.value.version,
      milestones_json: JSON.stringify(next),
    })
    content.value = data
    parseMilestones()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

// 全景图
async function onUploadPanorama(uploadFile) {
  const file = uploadFile?.raw || uploadFile
  const ct = (file?.type || '').toLowerCase()
  const okType = ct.startsWith('image/') || ct === 'image/svg+xml' || (file?.name || '').toLowerCase().endsWith('.svg')
  if (!file || !okType) {
    ElMessage.warning('仅支持图片或 SVG 文件')
    return
  }
  await checkStorageOrWarn()
  try {
    const { data } = await specialApi.uploadPanorama(special.value.id, file)
    content.value = data
    await loadPanorama()
    ElMessage.success('全景图已更新')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '上传失败')
  }
}

// 事务 / 风险
function openItemDialog(kind, row) {
  itemDialog.kind = kind
  itemDialog.editing = row || null
  itemDialog.form = row
    ? {
        content: row.content, progress: row.progress, owner: row.owner,
        planned_close_date: row.planned_close_date, status: row.status || 'open',
      }
    : defaultItem()
  itemDialog.visible = true
}

async function onSaveItem() {
  const { kind, editing, form } = itemDialog
  try {
    if (editing) {
      const api = kind === 'task' ? specialApi.updateTask : specialApi.updateRisk
      await api(editing.id, form)
    } else {
      const api = kind === 'task' ? specialApi.createTask : specialApi.createRisk
      await api(special.value.id, form)
    }
    itemDialog.visible = false
    await reloadItems(kind)
    ElMessage.success('已保存')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

async function onRemoveItem(kind, row) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  try {
    const api = kind === 'task' ? specialApi.removeTask : specialApi.removeRisk
    await api(row.id)
    await reloadItems(kind)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

async function reloadItems(kind) {
  if (kind === 'task') {
    const { data } = await specialApi.listTasks(special.value.id)
    tasks.value = data
  } else {
    const { data } = await specialApi.listRisks(special.value.id)
    risks.value = data
  }
}

// 阵型
function addFormationRow() {
  if (formation.value.headers.length === 0) {
    ElMessage.warning('请先添加列')
    return
  }
  formation.value.rows.push(Array(formation.value.headers.length).fill(''))
}
function addFormationCol() {
  formation.value.headers.push(`列${formation.value.headers.length + 1}`)
  formation.value.rows.forEach(r => r.push(''))
}
async function saveFormation(silent = false) {
  formationSaving.value = true
  try {
    const { data } = await specialApi.updateContent(special.value.id, {
      version: content.value.version,
      formation_json: JSON.stringify(formation.value),
    })
    content.value = data
    parseFormation()
    if (silent !== true) ElMessage.success('阵型已保存')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    formationSaving.value = false
  }
}

// 附加自由表格（RichGrid 模型：headers=[{text,colspan,align}], rows=[[{text,align,color}]]）
function addExtraGrid() {
  extraGrids.value.push(normGrid({
    title: `附加表格 ${extraGrids.value.length + 1}`,
    headers: [{ text: '列1', colspan: 1, align: 'center' }, { text: '列2', colspan: 1, align: 'center' }],
    rows: [
      [{ text: '', align: 'left', color: '' }, { text: '', align: 'left', color: '' }],
      [{ text: '', align: 'left', color: '' }, { text: '', align: 'left', color: '' }],
    ],
  }))
}
function removeExtraGrid(gi) {
  extraGrids.value.splice(gi, 1)
}
async function saveExtraGrids(silent = false) {
  extraSaving.value = true
  // 去掉前端内部的 _uid 再持久化
  const payload = extraGrids.value.map(({ _uid, ...g }) => g)
  try {
    const { data } = await specialApi.updateContent(special.value.id, {
      version: content.value.version,
      extra_grids_json: JSON.stringify(payload),
    })
    content.value = data
    parseExtraGrids()
    if (silent !== true) ElMessage.success('附加表格已保存')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    extraSaving.value = false
  }
}

// 周报
async function onExportXlsx() {
  try {
    const resp = await specialApi.exportXlsx(special.value.id)
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, '')
    const safeName = (special.value.name || 'special').replace(/[\\/:*?"<>|]/g, '')
    downloadBlob(resp.data, `${safeName}_${today}.xlsx`)
    ElMessage.success('已导出')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '导出失败')
  }
}

async function openReportDialog() {
  reportDialog.visible = true
  reportDialog.loading = true
  try {
    const { data } = await specialApi.reportDraft(special.value.id)
    reportDialog.form = {
      to: data.to || '',
      cc: data.cc || '',
      subject: data.subject || '',
      body: data.body || '',
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '生成草稿失败')
  } finally {
    reportDialog.loading = false
  }
}

async function onCopyReport() {
  const f = reportDialog.form
  try {
    await navigator.clipboard.writeText(f.body || '')
    ElMessage.success('正文纯文本已复制到剪贴板')
  } catch {
    ElMessage.warning('剪贴板不可用，请手动选中复制')
  }
}

async function onDownloadEml() {
  const f = reportDialog.form
  if (!f.to.trim()) {
    ElMessage.warning('请填写主送收件人，否则邮件客户端无法识别')
    return
  }
  reportDialog.downloading = true
  try {
    const { data } = await specialApi.reportEml(special.value.id, {
      to: f.to, cc: f.cc, subject: f.subject, body: f.body,
    })
    const safeName = (special.value.name || 'report').replace(/[\\/:*?"<>|]/g, '_')
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, '')
    downloadBlob(data, `${safeName}_${today}.eml`)
    ElMessage.success('已下载 .eml，双击在邮件客户端打开')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '导出失败')
  } finally {
    reportDialog.downloading = false
  }
}

// 切换到另一专项前，先释放当前专项的锁，再加载新数据
watch(() => route.params.id, async () => {
  await releaseLockSafe()
  await load()
})

function onBeforeUnload() {
  // 关闭/刷新页签时尽力释放锁；若未及发出，由服务端 TTL 兜底
  if (editMode.value && lock.value.mine && special.value) {
    specialApi.releaseLock(special.value.id).catch(() => {})
  }
}

onMounted(async () => {
  await load()
  startPoll()
  window.addEventListener('beforeunload', onBeforeUnload)
})
onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', onBeforeUnload)
  stopPoll()
  releaseLockSafe()
})
</script>

<style scoped>
.special-page {
  min-height: 200px;
  /* 页面默认字体微软雅黑；富文本区可在编辑器中切换宋体/微软雅黑 */
  font-family: '微软雅黑', 'Microsoft YaHei', 'PingFang SC', sans-serif;
}
.page-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}
.lock-banner :deep(.el-alert) { border-radius: 0; }
.lock-banner { border-radius: 0; }
.sec-title-main {
  background: #fff;
  text-align: center;
  font-size: 18px;
  font-weight: 600;
  padding: 12px 20px;
  border-bottom: 1px solid #ebeef5;
  position: relative;
}
.owner-and-actions {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
}
.owner-and-actions .owner {
  font-size: 13px;
  font-weight: normal;
  color: #909399;
}
.sec {
  border-bottom: 1px solid #ebeef5;
}
.sec:last-child { border-bottom: none; }
.sec-head {
  background: #f5f7fa;
  padding: 8px 16px;
  font-weight: 600;
  /* #1 分段标题 18px */
  font-size: 18px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}
.sec-head > :first-child { flex: 1; }
.sec-head .muted-hint { color: #909399; font-weight: normal; font-size: 12px; }
.sec-head .closed-toggle { font-weight: normal; }
.sec-body {
  padding: 12px 16px;
  min-height: 60px;
  /* #1 其他子项内容默认 16px */
  font-size: 16px;
}

/* #1 #2 专项页表格：正文 16px、文字用近黑色（原默认偏灰） */
.special-page :deep(.el-table) {
  font-size: 16px;
  color: #1f2329;
}
.special-page :deep(.el-table th .cell) {
  font-size: 16px;
  color: #1f2329;
}
.special-page :deep(.el-table .cell) {
  color: #1f2329;
}
/* #3 已闭环行单独底色（盖过斑马纹） */
.special-page :deep(.el-table .closed-row td.el-table__cell) {
  background: #f0f9eb !important;
}
.special-page :deep(.el-table .closed-row .cell) {
  color: #6b7d6b;
}
.panorama-body {
  text-align: center;
  background: #fafafa;
}
.panorama-img {
  max-width: 100%;
  max-height: 600px;
}
.panorama-empty {
  color: #c0c4cc;
  padding: 40px 0;
}
.cell-multiline {
  white-space: pre-wrap;
  word-break: break-word;
}
.rich-cell :deep(p) { margin: 0; }
.rich-cell :deep(div) { display: inline; }
.muted { color: #909399; padding: 12px 16px; }

/* 附加表格 */
.extra-grid {
  margin-top: 12px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}
.extra-grid-head {
  background: #fafbfc;
  padding: 6px 10px;
  display: flex;
  gap: 8px;
  align-items: center;
  border-bottom: 1px solid #ebeef5;
}
.extra-grid-head .spacer { flex: 1; }
.extra-grid-title-input {
  border: none;
  outline: none;
  background: transparent;
  font-weight: 600;
  font-size: 14px;
  min-width: 200px;
}
.save-extra {
  padding: 8px 12px 4px;
  text-align: right;
}
.formation-wrap {
  padding: 12px 16px;
  overflow-x: auto;
}
.report-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
  margin-top: 4px;
}
</style>
