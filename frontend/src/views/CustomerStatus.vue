<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <el-button :type="editMode ? 'warning' : 'primary'" :icon="editMode ? Check : Edit" @click="editMode = !editMode">
          {{ editMode ? '完成' : '编辑' }}
        </el-button>
        <el-button v-if="isAdmin && editMode" :icon="Plus" @click="openCreate">新增</el-button>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button v-if="isAdmin" :icon="Download" type="success" @click="onExport">导出 PPT</el-button>
        <el-button-group>
          <el-button :type="tableMode==='compact'?'primary':''" size="small" @click="tableMode='compact'">精简</el-button>
          <el-button :type="tableMode==='detail'?'primary':''" size="small" @click="tableMode='detail'">详细</el-button>
        </el-button-group>
        <span class="tip">
          {{ editMode ? '编辑模式：可直接修改各字段，完成后点「完成」退出' : '只读模式：点「编辑」进入可修改各字段' }}
        </span>
      </div>

      <el-table :data="list" v-loading="loading" border stripe style="width:100%"
        :default-sort="{ prop: 'machine_id', order: 'ascending' }">
        <el-table-column type="index" label="序号" width="60" align="center" :index="(i) => i + 1" />
        <el-table-column prop="machine_id" label="机台编号" width="110" align="center" sortable
          :sort-method="(a, b) => naturalCompare(a.machine_id, b.machine_id)" />
        <el-table-column prop="battlefield" label="客户" width="140" align="center" sortable
          :sort-method="(a, b) => naturalCompare(a.battlefield, b.battlefield)">
          <template #default="{ row }">
            <a class="bf-link" :title="'点击查看客户详情'" @click.stop="openCustomerDetail(row)">
              {{ row.battlefield || '—' }}
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="model" label="型号" width="120" align="center" sortable />

        <el-table-column prop="current_stage" label="当前阶段" width="160" align="center" sortable>
          <template #default="{ row }">
            <el-select v-if="isAdmin && editMode" :model-value="row.current_stage" size="small" @change="(v) => onStageChange(row, v)">
              <el-option v-for="s in stages" :key="s" :label="s" :value="s" />
            </el-select>
            <span v-else>{{ row.current_stage || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="field_version" label="现场版本" width="170" align="center" sortable
          :sort-method="(a, b) => naturalCompare(a.field_version, b.field_version)">
          <template #default="{ row }">
            <el-select v-if="isAdmin && editMode" :model-value="row.field_version" size="small" filterable allow-create
              default-first-option placeholder="选择或输入" @change="(v) => onVersionChange(row, v)">
              <el-option v-for="v in versionOptions" :key="v.value" :label="v.label" :value="v.value" />
            </el-select>
            <span v-else>{{ row.field_version || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="attention_level" label="近期关注度" width="170" align="center" sortable
          :sort-method="(a, b) => (a.attention_level || 0) - (b.attention_level || 0)">
          <template #default="{ row }">
            <el-rate :model-value="row.attention_level || 0" :max="5" :disabled="!isAdmin || !editMode"
              show-score score-template="{value}" @change="(v) => onRateChange(row, v)" />
          </template>
        </el-table-column>

        <el-table-column label="当前进展" min-width="180">
          <template #default="{ row }">
            <el-input v-if="isEditing(row, 'customer_status')" v-model="row.customer_status"
              size="small" autofocus type="textarea" :rows="2"
              @blur="commit(row, 'customer_status')"
              @keyup.enter.ctrl="commit(row, 'customer_status')"
              @keyup.esc="cancel(row, 'customer_status')" />
            <div v-else :class="{ 'editable-cell': editMode }" @dblclick="editMode && startEdit(row, 'customer_status')">
              {{ row.customer_status || '—' }}
            </div>
          </template>
        </el-table-column>

        <!-- ── 现场关键事务 ────────────────────────────── -->
        <el-table-column label="现场关键事务" min-width="240">
          <template #default="{ row }">
            <div class="cl-cell">
              <!-- 无数据 -->
              <template v-if="!row.recent_focus_items.length">
                <div class="cl-compact-line">
                  <span class="cl-empty">—</span>
                  <button v-if="editMode" class="cl-add-btn-mini" type="button" title="新增条目" @click.stop="startAdding(row,'recent_focus')">＋</button>
                </div>
              </template>

              <!-- 精简模式：只显第一条 -->
              <template v-else-if="tableMode==='compact'">
                <div class="cl-compact-line">
                  <label class="cl-item" :class="{ ro: !editMode }" @click.prevent="editMode && toggleItem(row,'recent_focus',0)">
                    <span class="cl-box" :class="{ checked: row.recent_focus_items[0].done }">
                      <svg v-if="row.recent_focus_items[0].done" class="cl-check-svg" viewBox="0 0 10 8" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1,4 4,7 9,1"/></svg>
                    </span>
                    <span class="cl-text" :class="{ done: row.recent_focus_items[0].done }">{{ row.recent_focus_items[0].text }}</span>
                  </label>
                  <span v-if="row.recent_focus_items.length > 1" class="cl-more">+{{ row.recent_focus_items.length - 1 }}</span>
                  <button v-if="editMode" class="cl-add-btn-mini" type="button" title="新增条目" @click.stop="startAdding(row,'recent_focus')">＋</button>
                </div>
              </template>

              <!-- 详细模式：全部展开 -->
              <template v-else>
                <label v-for="(item, idx) in row.recent_focus_items" :key="idx"
                  class="cl-item" :class="{ ro: !editMode }" @click.prevent="editMode && toggleItem(row,'recent_focus',idx)">
                  <span class="cl-box" :class="{ checked: item.done }">
                    <svg v-if="item.done" class="cl-check-svg" viewBox="0 0 10 8" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1,4 4,7 9,1"/></svg>
                  </span>
                  <span class="cl-text" :class="{ done: item.done }">{{ item.text }}</span>
                  <button v-if="editMode && isAdmin" class="cl-del" type="button" @click.stop="deleteItem(row,'recent_focus',idx)">×</button>
                </label>
                <div class="cl-progress-wrap">
                  <div class="cl-bar"><div class="cl-fill" :style="{ width: clPct(row.recent_focus_items)+'%' }" /></div>
                  <span class="cl-pct-text">{{ clDone(row.recent_focus_items) }}/{{ row.recent_focus_items.length }}</span>
                </div>
                <button v-if="editMode" class="cl-add-btn" type="button" @click.stop="startAdding(row,'recent_focus')">＋ 新增</button>
              </template>

              <!-- 新增输入行（各模式共用）-->
              <div v-if="editMode && addingState && addingState.rowId===row.id && addingState.field==='recent_focus'" class="cl-add-row">
                <input :ref="el => setAddInputRef(el, row.id, 'recent_focus')" v-model="addingText" class="cl-add-input" placeholder="输入新条目…"
                  @keydown.enter.prevent="confirmAdd(row,'recent_focus')"
                  @keydown.esc="cancelAdding" />
                <button class="cl-btn-ok" type="button" @click="confirmAdd(row,'recent_focus')">确认</button>
                <button class="cl-btn-no" type="button" @click="cancelAdding">取消</button>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- ── 软件类风险和问题 ──────────────────────── -->
        <el-table-column label="软件类风险和问题" min-width="240">
          <template #default="{ row }">
            <div class="cl-cell">
              <template v-if="!row.key_issues_items.length">
                <div class="cl-compact-line">
                  <span class="cl-empty">—</span>
                  <button v-if="editMode" class="cl-add-btn-mini" type="button" title="新增条目" @click.stop="startAdding(row,'key_issues')">＋</button>
                </div>
              </template>

              <template v-else-if="tableMode==='compact'">
                <div class="cl-compact-line">
                  <label class="cl-item" :class="{ ro: !editMode }" @click.prevent="editMode && toggleItem(row,'key_issues',0)">
                    <span class="cl-box" :class="{ checked: row.key_issues_items[0].done }">
                      <svg v-if="row.key_issues_items[0].done" class="cl-check-svg" viewBox="0 0 10 8" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1,4 4,7 9,1"/></svg>
                    </span>
                    <span class="cl-text" :class="{ done: row.key_issues_items[0].done }">{{ row.key_issues_items[0].text }}</span>
                  </label>
                  <span v-if="row.key_issues_items.length > 1" class="cl-more">+{{ row.key_issues_items.length - 1 }}</span>
                  <button v-if="editMode" class="cl-add-btn-mini" type="button" title="新增条目" @click.stop="startAdding(row,'key_issues')">＋</button>
                </div>
              </template>

              <template v-else>
                <label v-for="(item, idx) in row.key_issues_items" :key="idx"
                  class="cl-item" :class="{ ro: !editMode }" @click.prevent="editMode && toggleItem(row,'key_issues',idx)">
                  <span class="cl-box" :class="{ checked: item.done }">
                    <svg v-if="item.done" class="cl-check-svg" viewBox="0 0 10 8" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1,4 4,7 9,1"/></svg>
                  </span>
                  <span class="cl-text" :class="{ done: item.done }">{{ item.text }}</span>
                  <button v-if="editMode && isAdmin" class="cl-del" type="button" @click.stop="deleteItem(row,'key_issues',idx)">×</button>
                </label>
                <div class="cl-progress-wrap">
                  <div class="cl-bar"><div class="cl-fill" :style="{ width: clPct(row.key_issues_items)+'%' }" /></div>
                  <span class="cl-pct-text">{{ clDone(row.key_issues_items) }}/{{ row.key_issues_items.length }}</span>
                </div>
                <button v-if="editMode" class="cl-add-btn" type="button" @click.stop="startAdding(row,'key_issues')">＋ 新增</button>
              </template>

              <!-- 新增输入行（各模式共用）-->
              <div v-if="editMode && addingState && addingState.rowId===row.id && addingState.field==='key_issues'" class="cl-add-row">
                <input :ref="el => setAddInputRef(el, row.id, 'key_issues')" v-model="addingText" class="cl-add-input" placeholder="输入新条目…"
                  @keydown.enter.prevent="confirmAdd(row,'key_issues')"
                  @keydown.esc="cancelAdding" />
                <button class="cl-btn-ok" type="button" @click="confirmAdd(row,'key_issues')">确认</button>
                <button class="cl-btn-no" type="button" @click="cancelAdding">取消</button>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column v-if="isAdmin && editMode" label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ── 新增 / 编辑弹窗 ──────────────────────────── -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑' : '新增'" width="640px">
      <el-form :model="form" label-width="130px">
        <el-form-item label="机台编号">
          <el-input v-model="form.machine_id" :disabled="!!editing" :placeholder="editing ? '创建后不可修改' : '请输入'" />
        </el-form-item>
        <el-form-item label="客户">
          <template v-if="editing">
            <el-input v-model="form.battlefield" disabled placeholder="创建后不可修改" />
          </template>
          <template v-else>
            <el-select
              v-model="form.battlefield"
              filterable
              placeholder="请选择客户（仅可从客户管理中选）"
              style="width: 100%"
              no-data-text="客户管理中暂无客户，请先到「客户管理」新增"
            >
              <el-option
                v-for="c in customers"
                :key="c.id"
                :label="c.display_name ? `${c.code} · ${c.display_name}` : c.code"
                :value="c.code"
              />
            </el-select>
            <div class="dialog-tip">
              候选来自<router-link to="/customers" class="bf-link">客户管理</router-link>；如缺少请先到那里新增
            </div>
          </template>
        </el-form-item>
        <el-form-item label="型号">
          <el-input v-model="form.model" :disabled="!!editing" :placeholder="editing ? '创建后不可修改' : '请输入'" />
        </el-form-item>
        <el-form-item label="当前阶段">
          <el-select v-model="form.current_stage" placeholder="请选择" style="width:100%">
            <el-option v-for="s in stages" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="现场版本">
          <el-select v-model="form.field_version" filterable allow-create default-first-option placeholder="选择或输入" style="width:100%">
            <el-option v-for="v in versionOptions" :key="v.value" :label="v.label" :value="v.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="近期关注度">
          <el-rate v-model="form.attention_level" :max="5" show-score score-template="{value} 星" />
        </el-form-item>
        <el-form-item label="当前进展">
          <el-input v-model="form.customer_status" type="textarea" :rows="2" />
        </el-form-item>

        <!-- 现场关键事务 编辑器 -->
        <el-form-item label="现场关键事务">
          <div class="dialog-cl">
            <div v-for="(item, idx) in formChecklists.recent_focus" :key="idx" class="dialog-cl-row">
              <span class="cl-box sm" :class="{ checked: item.done }" @click="item.done = !item.done">
                <svg v-if="item.done" class="cl-check-svg" viewBox="0 0 10 8" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1,4 4,7 9,1"/></svg>
              </span>
              <el-input v-model="item.text" size="small" placeholder="条目内容" style="flex:1" />
              <el-button :icon="Delete" size="small" circle plain type="danger" @click="formChecklists.recent_focus.splice(idx,1)" />
            </div>
            <el-button size="small" style="margin-top:4px" @click="formChecklists.recent_focus.push({text:'',done:false})">＋ 添加条目</el-button>
          </div>
        </el-form-item>

        <!-- 软件类风险和问题 编辑器 -->
        <el-form-item label="软件类风险和问题">
          <div class="dialog-cl">
            <div v-for="(item, idx) in formChecklists.key_issues" :key="idx" class="dialog-cl-row">
              <span class="cl-box sm" :class="{ checked: item.done }" @click="item.done = !item.done">
                <svg v-if="item.done" class="cl-check-svg" viewBox="0 0 10 8" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1,4 4,7 9,1"/></svg>
              </span>
              <el-input v-model="item.text" size="small" placeholder="条目内容" style="flex:1" />
              <el-button :icon="Delete" size="small" circle plain type="danger" @click="formChecklists.key_issues.splice(idx,1)" />
            </div>
            <el-button size="small" style="margin-top:4px" @click="formChecklists.key_issues.push({text:'',done:false})">＋ 添加条目</el-button>
          </div>
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
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Delete, Download, Edit, Plus, Refresh } from '@element-plus/icons-vue'
import { configApi, customerApi, customerStatusApi, downloadBlob, majorVersionApi } from '../api'
import { auth } from '../store/auth'

const router = useRouter()

const isAdmin = auth.isAdmin

const list    = ref([])
const stages  = ref([])
const versions = ref([])
const customers = ref([])     // 来自客户管理的主数据，用于"新增机台"时的下拉
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const form    = reactive(defaultForm())

const editingCell = ref(null)
const tableMode   = ref('compact')  // 'compact' | 'detail'
const editMode    = ref(false)      // 顶部「编辑」开关：默认只读，开启后才可改

const ADMIN_FIELDS = ['current_stage', 'field_version', 'attention_level', 'issue_url']
const USER_FIELDS  = ['customer_status', 'recent_focus', 'key_issues']

const versionOptions = computed(() => versions.value)

// 自然排序：让 M2 < M10、V2.2 < V2.10（数字段按数值比较，而非字符串）
function naturalCompare(a, b) {
  return String(a ?? '').localeCompare(String(b ?? ''), 'zh-Hans-CN', { numeric: true, sensitivity: 'base' })
}

function defaultForm() {
  return {
    machine_id: '', battlefield: '', model: '',
    current_stage: '', field_version: '',
    attention_level: 0, customer_status: '',
    recent_focus: '', key_issues: '', issue_url: '',
  }
}

// ── 清单数据解析 ──────────────────────────────────────
function parseChecklist(val) {
  if (!val) return []
  try {
    const parsed = JSON.parse(val)
    if (Array.isArray(parsed)) return parsed.map(i => ({ text: String(i.text ?? ''), done: !!i.done }))
  } catch {}
  // 兼容旧格式：每行一条
  return val.split('\n').filter(s => s.trim()).map(t => ({ text: t.trim(), done: false }))
}

function serializeChecklist(items) {
  return items.length ? JSON.stringify(items) : ''
}

function clDone(items) { return items.filter(i => i.done).length }
function clPct(items)  { return items.length ? Math.round(clDone(items) / items.length * 100) : 0 }

// ── 数据加载 ──────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    const { data } = await customerStatusApi.list()
    list.value = data.map(row => ({
      ...row,
      recent_focus_items: parseChecklist(row.recent_focus),
      key_issues_items:   parseChecklist(row.key_issues),
    }))
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
  } catch {}
}

async function loadCustomers() {
  try {
    const { data } = await customerApi.list()
    customers.value = data
  } catch (e) {
    console.error('[CustomerStatus] 加载客户主数据失败:', e)
  }
}

async function loadVersions() {
  try {
    const [majorRes, iterRes] = await Promise.all([
      majorVersionApi.list(),
      majorVersionApi.allIterationVersions(),
    ])
    const iter = (iterRes.data || []).map(v => ({
      value: v.version_no,
      label: v.title ? `${v.version_no} · ${v.title}` : v.version_no,
    }))
    const major = (majorRes.data || []).map(v => ({
      value: v.version_no,
      label: v.title ? `${v.version_no} · ${v.title}` : v.version_no,
    }))
    // 去重，迭代版本在前（更接近客户实际现场版本）
    const seen = new Set()
    const merged = []
    for (const v of [...iter, ...major]) {
      if (!seen.has(v.value)) { seen.add(v.value); merged.push(v) }
    }
    versions.value = merged
    if (!merged.length) {
      console.warn('[CustomerStatus] 版本列表为空：请到「版本管理」新增大版本/迭代版本')
    }
  } catch (e) {
    console.error('[CustomerStatus] 加载版本列表失败:', e)
  }
}

// ── Dialog ────────────────────────────────────────────
const formChecklists = reactive({ recent_focus: [], key_issues: [] })

function openCreate() {
  editing.value = null
  Object.assign(form, defaultForm())
  formChecklists.recent_focus = []
  formChecklists.key_issues   = []
  if (stages.value.length) form.current_stage = stages.value[0]
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = row
  Object.assign(form, row)
  formChecklists.recent_focus = parseChecklist(row.recent_focus).map(i => ({ ...i }))
  formChecklists.key_issues   = parseChecklist(row.key_issues).map(i => ({ ...i }))
  dialogVisible.value = true
}

async function onSubmit() {
  if (!editing.value) {
    if (!form.machine_id || !form.battlefield) {
      ElMessage.warning('机台编号、客户必填')
      return
    }
  }
  form.recent_focus = serializeChecklist(formChecklists.recent_focus.filter(i => i.text.trim()))
  form.key_issues   = serializeChecklist(formChecklists.key_issues.filter(i => i.text.trim()))
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
  }
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确认删除机台 ${row.machine_id} 吗？`, '提示', { type: 'warning' })
  await customerStatusApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

// ── 行内文本编辑（当前进展 / 问题单链接） ───────────────
function isEditing(row, field) {
  return editingCell.value?.id === row.id && editingCell.value?.field === field
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
  const newVal   = row[field]
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

// ── 清单交互 ──────────────────────────────────────────
const addingState  = ref(null)   // { rowId, field }
const addingText   = ref('')
let _pendingFocusEl = null

/** 函数式 ref：v-for/多列模板会导致 string ref 收集为数组；用函数 ref 单值赋值。 */
function setAddInputRef(el, rowId, field) {
  if (el && addingState.value && addingState.value.rowId === rowId && addingState.value.field === field) {
    _pendingFocusEl = el
  }
}

async function startAdding(row, field) {
  addingState.value = { rowId: row.id, field }
  addingText.value  = ''
  _pendingFocusEl = null
  await nextTick()
  _pendingFocusEl?.focus()
}

function cancelAdding() {
  addingState.value = null
  addingText.value  = ''
}

async function confirmAdd(row, field) {
  const text = addingText.value.trim()
  if (!text) { cancelAdding(); return }
  const itemsField = field + '_items'
  row[itemsField].push({ text, done: false })
  await saveChecklist(row, field)
  cancelAdding()
}

async function toggleItem(row, field, idx) {
  const itemsField = field + '_items'
  if (!row[itemsField][idx]) return
  row[itemsField][idx].done = !row[itemsField][idx].done
  await saveChecklist(row, field)
}

async function deleteItem(row, field, idx) {
  const itemsField = field + '_items'
  row[itemsField].splice(idx, 1)
  await saveChecklist(row, field)
}

async function saveChecklist(row, field) {
  const itemsField = field + '_items'
  const newVal     = serializeChecklist(row[itemsField])
  const original   = row[field]
  row[field] = newVal
  try {
    const { data } = await customerStatusApi.update(row.id, { [field]: newVal, version: row.version })
    row.version = data.version
  } catch (e) {
    row[field]      = original
    row[itemsField] = parseChecklist(original)
    if (e.response?.status !== 409) ElMessage.error(e.response?.data?.detail || '保存失败')
    else load()
  }
}

// ── 其他字段快速保存 ──────────────────────────────────
async function onRateChange(row, value) {
  if (!isAdmin.value) { ElMessage.warning('关注度仅管理员可修改'); return }
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

// ── 点击客户列：跳到完整的客户详情页 ──────────────────
async function openCustomerDetail(row) {
  const name = (row.battlefield || '').trim()
  if (!name) {
    ElMessage.warning('该机台未设置客户')
    return
  }
  try {
    const { data } = await customerApi.resolve(name)
    if (data && data.id) {
      router.push(`/customers/${data.id}`)
    } else {
      ElMessageBox.confirm(
        `「${name}」尚未在客户管理中登记（或作为别名关联）。是否现在去客户管理新建？`,
        '客户未关联',
        { type: 'info', confirmButtonText: '去客户管理', cancelButtonText: '取消' }
      ).then(() => router.push('/customers')).catch(() => {})
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '查询客户失败')
  }
}

onMounted(async () => {
  loadConfig()
  loadVersions()
  loadCustomers()
  await load()
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
.bf-link {
  color: #409eff;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
}
.bf-link:hover { text-decoration: underline; }
.dialog-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
.hint {
  color: #909399;
  font-size: 13px;
  padding: 8px 4px;
}

/* ── 清单单元格 ── */
.cl-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cl-empty { color: #c0c4cc; font-size: 13px; }

.cl-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  cursor: pointer;
  user-select: none;
  line-height: 1.5;
}
/* 只读模式：清单项不可点 */
.cl-item.ro { cursor: default; }

.cl-box {
  width: 14px;
  height: 14px;
  border: 1.5px solid #c0c4cc;
  border-radius: 3px;
  background: #fff;
  flex-shrink: 0;
  margin-top: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .15s;
}
.cl-box.checked {
  background: #67c23a;
  border-color: #67c23a;
}
.cl-box.sm { width: 13px; height: 13px; margin-top: 1px; }

.cl-check-svg { width: 8px; height: 8px; display: block; }

.cl-text { flex: 1; font-size: 13px; transition: color .15s; }
.cl-text.done { color: #b0b3b8; text-decoration: line-through; }

.cl-del {
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  border: none;
  background: transparent;
  color: #c0c4cc;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  padding: 0;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 2px;
  transition: all .15s;
}
.cl-del:hover { background: #fef0f0; color: #f56c6c; }

.cl-more {
  display: inline-block;
  margin-left: 4px;
  padding: 1px 6px;
  border-radius: 8px;
  background: #ecf5ff;
  color: #409eff;
  font-size: 11px;
  font-weight: 500;
  align-self: center;
}

/* 进度条 */
.cl-progress-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 3px;
}
.cl-bar {
  flex: 1;
  height: 3px;
  background: #e4e7ed;
  border-radius: 2px;
  overflow: hidden;
}
.cl-fill {
  height: 100%;
  background: linear-gradient(90deg, #67c23a, #95d475);
  border-radius: 2px;
  transition: width .3s;
}
.cl-pct-text { font-size: 11px; color: #909399; white-space: nowrap; }

/* 新增行 */
.cl-add-row {
  display: flex;
  gap: 4px;
  align-items: center;
  margin-top: 2px;
}
.cl-add-input {
  flex: 1;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 2px 7px;
  font-size: 12px;
  outline: none;
  color: #303133;
  font-family: inherit;
  min-width: 0;
}
.cl-add-input:focus { border-color: #409eff; }
.cl-btn-ok, .cl-btn-no {
  padding: 1px 7px;
  border-radius: 3px;
  border: 1px solid;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
}
.cl-btn-ok { background: #409eff; border-color: #409eff; color: #fff; }
.cl-btn-no { background: #fff; border-color: #dcdfe6; color: #606266; }

.cl-add-btn {
  align-self: flex-start;
  margin-top: 3px;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px dashed #c0c4cc;
  background: transparent;
  color: #909399;
  font-size: 12px;
  cursor: pointer;
  transition: all .15s;
}
.cl-add-btn:hover { border-color: #409eff; color: #409eff; background: #ecf5ff; }

/* Dialog 清单编辑器 */
.dialog-cl { display: flex; flex-direction: column; gap: 6px; width: 100%; }
.dialog-cl-row { display: flex; align-items: center; gap: 6px; }

/* 紧凑模式行 + 迷你新增按钮 */
.cl-compact-line {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: nowrap;
}
.cl-compact-line .cl-item { flex: 1; min-width: 0; }
.cl-compact-line .cl-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cl-add-btn-mini {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border-radius: 4px;
  border: 1px dashed #c0c4cc;
  background: transparent;
  color: #909399;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all .15s;
}
.cl-add-btn-mini:hover {
  border-color: #409eff;
  color: #409eff;
  background: #ecf5ff;
  border-style: solid;
}

/* 问题单分布 drawer */
.drill-meta { color: #909399; font-size: 12px; margin-bottom: 6px; }
.drill-summary {
  background: #f5f7fa;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
}
.drill-summary b { color: #409eff; font-size: 15px; margin: 0 2px; }
.hint { color: #909399; font-size: 13px; padding: 24px 0; text-align: center; }

.drill-sub-header {
  margin: 16px 0 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #303133;
}
.drill-sub-header b { color: #409eff; }
.drill-note { color: #909399; font-size: 12px; margin: 0 0 8px; }
:deep(.drill-row-active) { background: #ecf5ff !important; }
:deep(.drill-row-active td) { color: #409eff !important; font-weight: 600; }
</style>
