<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <el-button v-if="isAdmin" type="primary" :icon="Plus" @click="openCreate">新增</el-button>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button v-if="isAdmin" :icon="Download" type="success" @click="onExport">导出 PPT</el-button>
        <el-button-group>
          <el-button :type="tableMode==='compact'?'primary':''" size="small" @click="tableMode='compact'">精简</el-button>
          <el-button :type="tableMode==='detail'?'primary':''" size="small" @click="tableMode='detail'">详细</el-button>
        </el-button-group>
        <span class="tip">
          「当前进展」双击可编辑{{ isAdmin ? '；管理员可双击「问题单」编辑链接' : '' }}
        </span>
      </div>

      <el-table :data="list" v-loading="loading" border stripe style="width:100%">
        <el-table-column type="index" label="序号" width="60" align="center" :index="(i) => i + 1" />
        <el-table-column prop="machine_id" label="机台编号" width="110" align="center" />
        <el-table-column prop="battlefield" label="客户" width="140" align="center" />
        <el-table-column prop="model" label="型号" width="120" align="center" />

        <el-table-column label="当前阶段" width="140" align="center">
          <template #default="{ row }">
            <el-select v-if="isAdmin" :model-value="row.current_stage" size="small" @change="(v) => onStageChange(row, v)">
              <el-option v-for="s in stages" :key="s" :label="s" :value="s" />
            </el-select>
            <span v-else>{{ row.current_stage || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="现场版本" width="170" align="center">
          <template #default="{ row }">
            <el-select v-if="isAdmin" :model-value="row.field_version" size="small" filterable allow-create
              default-first-option placeholder="选择或输入" @change="(v) => onVersionChange(row, v)">
              <el-option v-for="v in versionOptions" :key="v.value" :label="v.label" :value="v.value" />
            </el-select>
            <span v-else>{{ row.field_version || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="近期关注度" width="170" align="center">
          <template #default="{ row }">
            <el-rate :model-value="row.attention_level || 0" :max="5" :disabled="!isAdmin"
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
            <div v-else class="editable-cell" @dblclick="startEdit(row, 'customer_status')">
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
                <span class="cl-empty">—</span>
                <button v-if="tableMode==='detail'" class="cl-add-btn" @click.stop="startAdding(row,'recent_focus')">＋ 新增</button>
              </template>

              <!-- 精简模式：只显第一条 -->
              <template v-else-if="tableMode==='compact'">
                <label class="cl-item" @click.prevent="toggleItem(row,'recent_focus',0)">
                  <span class="cl-box" :class="{ checked: row.recent_focus_items[0].done }">
                    <svg v-if="row.recent_focus_items[0].done" class="cl-check-svg" viewBox="0 0 10 8" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1,4 4,7 9,1"/></svg>
                  </span>
                  <span class="cl-text" :class="{ done: row.recent_focus_items[0].done }">{{ row.recent_focus_items[0].text }}</span>
                </label>
                <span v-if="row.recent_focus_items.length > 1" class="cl-more">+{{ row.recent_focus_items.length - 1 }}</span>
              </template>

              <!-- 详细模式：全部展开 -->
              <template v-else>
                <label v-for="(item, idx) in row.recent_focus_items" :key="idx"
                  class="cl-item" @click.prevent="toggleItem(row,'recent_focus',idx)">
                  <span class="cl-box" :class="{ checked: item.done }">
                    <svg v-if="item.done" class="cl-check-svg" viewBox="0 0 10 8" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1,4 4,7 9,1"/></svg>
                  </span>
                  <span class="cl-text" :class="{ done: item.done }">{{ item.text }}</span>
                  <button v-if="isAdmin" class="cl-del" @click.stop="deleteItem(row,'recent_focus',idx)">×</button>
                </label>
                <div class="cl-progress-wrap">
                  <div class="cl-bar"><div class="cl-fill" :style="{ width: clPct(row.recent_focus_items)+'%' }" /></div>
                  <span class="cl-pct-text">{{ clDone(row.recent_focus_items) }}/{{ row.recent_focus_items.length }}</span>
                </div>
                <div v-if="addingState?.rowId===row.id && addingState?.field==='recent_focus'" class="cl-add-row">
                  <input ref="addInputEl" v-model="addingText" class="cl-add-input" placeholder="输入新条目…"
                    @keydown.enter.prevent="confirmAdd(row,'recent_focus')"
                    @keydown.esc="cancelAdding" />
                  <button class="cl-btn-ok" @click="confirmAdd(row,'recent_focus')">确认</button>
                  <button class="cl-btn-no" @click="cancelAdding">取消</button>
                </div>
                <button v-else class="cl-add-btn" @click.stop="startAdding(row,'recent_focus')">＋ 新增</button>
              </template>
            </div>
          </template>
        </el-table-column>

        <!-- ── 软件类风险和问题 ──────────────────────── -->
        <el-table-column label="软件类风险和问题" min-width="240">
          <template #default="{ row }">
            <div class="cl-cell">
              <template v-if="!row.key_issues_items.length">
                <span class="cl-empty">—</span>
                <button v-if="tableMode==='detail'" class="cl-add-btn" @click.stop="startAdding(row,'key_issues')">＋ 新增</button>
              </template>

              <template v-else-if="tableMode==='compact'">
                <label class="cl-item" @click.prevent="toggleItem(row,'key_issues',0)">
                  <span class="cl-box" :class="{ checked: row.key_issues_items[0].done }">
                    <svg v-if="row.key_issues_items[0].done" class="cl-check-svg" viewBox="0 0 10 8" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1,4 4,7 9,1"/></svg>
                  </span>
                  <span class="cl-text" :class="{ done: row.key_issues_items[0].done }">{{ row.key_issues_items[0].text }}</span>
                </label>
                <span v-if="row.key_issues_items.length > 1" class="cl-more">+{{ row.key_issues_items.length - 1 }}</span>
              </template>

              <template v-else>
                <label v-for="(item, idx) in row.key_issues_items" :key="idx"
                  class="cl-item" @click.prevent="toggleItem(row,'key_issues',idx)">
                  <span class="cl-box" :class="{ checked: item.done }">
                    <svg v-if="item.done" class="cl-check-svg" viewBox="0 0 10 8" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1,4 4,7 9,1"/></svg>
                  </span>
                  <span class="cl-text" :class="{ done: item.done }">{{ item.text }}</span>
                  <button v-if="isAdmin" class="cl-del" @click.stop="deleteItem(row,'key_issues',idx)">×</button>
                </label>
                <div class="cl-progress-wrap">
                  <div class="cl-bar"><div class="cl-fill" :style="{ width: clPct(row.key_issues_items)+'%' }" /></div>
                  <span class="cl-pct-text">{{ clDone(row.key_issues_items) }}/{{ row.key_issues_items.length }}</span>
                </div>
                <div v-if="addingState?.rowId===row.id && addingState?.field==='key_issues'" class="cl-add-row">
                  <input ref="addInputEl" v-model="addingText" class="cl-add-input" placeholder="输入新条目…"
                    @keydown.enter.prevent="confirmAdd(row,'key_issues')"
                    @keydown.esc="cancelAdding" />
                  <button class="cl-btn-ok" @click="confirmAdd(row,'key_issues')">确认</button>
                  <button class="cl-btn-no" @click="cancelAdding">取消</button>
                </div>
                <button v-else class="cl-add-btn" @click.stop="startAdding(row,'key_issues')">＋ 新增</button>
              </template>
            </div>
          </template>
        </el-table-column>

        <!-- ── 问题单情况 ───────────────────────────── -->
        <el-table-column label="问题单情况" width="180" align="center">
          <template #default="{ row }">
            <template v-if="isAdmin && isEditing(row,'issue_url')">
              <el-input v-model="row.issue_url" size="small" autofocus placeholder="https://..."
                @blur="commit(row,'issue_url')"
                @keyup.enter="commit(row,'issue_url')"
                @keyup.esc="cancel(row,'issue_url')" />
            </template>
            <template v-else>
              <el-button size="small" type="primary" link @click="openIssueDrill(row)">
                查看分布<span v-if="row._issueCount != null">（{{ row._issueCount }}）</span>
              </el-button>
              <el-button v-if="row.issue_url" size="small" :icon="Link" link
                title="打开外部链接" @click="openIssue(row)" />
              <el-button v-if="isAdmin" size="small" :icon="Edit" link
                :title="row.issue_url ? '修改链接' : '设置链接'" @click="startEdit(row,'issue_url')" />
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

    <!-- ── 新增 / 编辑弹窗 ──────────────────────────── -->
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

    <!-- ── 问题单分布 drawer ── -->
    <el-drawer v-model="issueDrillVisible" :title="drillTitle" size="42%" direction="rtl">
      <div v-if="issueDataLoading" class="hint">加载问题单数据…</div>
      <template v-else-if="issueDataCache && currentDrillRow">
        <div class="drill-meta">
          数据来源：{{ issueDataCache.actual_file || '—' }}
          <span v-if="issueDataCache.file_mtime"> · {{ issueDataCache.file_mtime }}</span>
        </div>
        <template v-if="drillRows.length">
          <div class="drill-summary">
            合计 <b>{{ drillTotalCount }}</b> 个问题单
          </div>
          <el-table :data="drillRows" border stripe size="small" style="margin-top:8px">
            <el-table-column prop="group" label="责任小组" />
            <el-table-column prop="count" label="问题单数" align="center" width="140" />
          </el-table>
        </template>
        <el-empty v-else description="该客户在最新报表中无问题单" />
        <div v-if="currentDrillRow.issue_url" style="margin-top:14px">
          <el-button type="primary" :icon="Link" @click="openIssue(currentDrillRow)">
            打开外部问题单链接
          </el-button>
        </div>
      </template>
      <el-empty v-else description="无问题单数据，请检查是否已配置报表目录" />
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Download, Edit, Link, Plus, Refresh } from '@element-plus/icons-vue'
import { configApi, customerStatusApi, downloadBlob, issueApi, versionApi } from '../api'
import { auth } from '../store/auth'

const isAdmin = auth.isAdmin

const list    = ref([])
const stages  = ref([])
const versions = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const form    = reactive(defaultForm())

const editingCell = ref(null)
const tableMode   = ref('compact')  // 'compact' | 'detail'

const ADMIN_FIELDS = ['current_stage', 'field_version', 'attention_level', 'issue_url']
const USER_FIELDS  = ['customer_status', 'recent_focus', 'key_issues']

const versionOptions = computed(() => versions.value.map((v) => ({
  value: v.version_no,
  label: v.title ? `${v.version_no} · ${v.title}` : v.version_no,
})))

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
      _issueCount: null,   // 由 loadIssueData() 异步填充
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

async function loadVersions() {
  try {
    const { data } = await versionApi.list()
    versions.value = data
  } catch {}
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
const addInputEl   = ref(null)

async function startAdding(row, field) {
  addingState.value = { rowId: row.id, field }
  addingText.value  = ''
  await nextTick()
  addInputEl.value?.focus()
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

function openIssue(row) {
  if (row.issue_url) window.open(row.issue_url, '_blank')
}

// ── 问题单分布 drawer ──────────────────────────────────
const issueDataCache    = ref(null)
const issueDataLoading  = ref(false)
const issueDrillVisible = ref(false)
const currentDrillRow   = ref(null)

const drillTitle = computed(() =>
  currentDrillRow.value ? `「${currentDrillRow.value.battlefield}」问题单分布` : '问题单分布'
)

const drillRows = computed(() => {
  if (!issueDataCache.value || !currentDrillRow.value) return []
  const bc = issueDataCache.value.by_customer
  if (!bc?.columns || !bc?.rows) return []
  const colName = bc.columns.find(c => c === currentDrillRow.value.battlefield)
  if (!colName) return []
  return bc.rows
    .filter(r => r.label !== '合计')
    .map(r => ({ group: r.label, count: Number(r[colName]) || 0 }))
    .filter(r => r.count > 0)
})

const drillTotalCount = computed(() =>
  drillRows.value.reduce((s, r) => s + r.count, 0)
)

async function loadIssueData() {
  issueDataLoading.value = true
  try {
    const { data } = await issueApi.getData()
    if (!data?.configured) { issueDataCache.value = null; return }
    issueDataCache.value = data
    // 给每行注入 _issueCount（方便表格列显示数字）
    const bc = data.by_customer
    if (bc?.columns && bc?.rows) {
      const totalRow = bc.rows.find(r => r.label === '合计')
      if (totalRow) {
        for (const row of list.value) {
          const colName = bc.columns.find(c => c === row.battlefield)
          row._issueCount = colName ? (Number(totalRow[colName]) || 0) : null
        }
      }
    }
  } catch {
    /* 报表未配置/读取失败时静默 —— 链接仍可点，drawer 内提示用户 */
  } finally {
    issueDataLoading.value = false
  }
}

function openIssueDrill(row) {
  currentDrillRow.value = row
  issueDrillVisible.value = true
  if (!issueDataCache.value && !issueDataLoading.value) loadIssueData()
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

onMounted(async () => {
  loadConfig()
  loadVersions()
  await load()
  loadIssueData()   // 后台拉取问题单分布，不阻塞表格渲染
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
</style>
