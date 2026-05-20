<template>
  <div v-loading="loading" class="special-page">
    <div v-if="special" class="page-card">
      <!-- 标题 -->
      <div class="sec-title-main">
        <span>{{ special.name }}</span>
        <span class="owner">责任人：{{ special.owner || '-' }}</span>
      </div>

      <!-- 1. 专项目标 -->
      <div class="sec">
        <div class="sec-head">专项目标</div>
        <div class="sec-body">
          <EditableText :value="content.goal" :editable="canEdit" placeholder="点击填写专项目标..." @save="onSaveField('goal', $event)" />
        </div>
      </div>

      <!-- 2. 专项计划：里程碑 -->
      <div class="sec">
        <div class="sec-head">
          <span>专项计划</span>
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

      <!-- 3. 一句话进展&求助 -->
      <div class="sec">
        <div class="sec-head">一句话进展&求助</div>
        <div class="sec-body">
          <EditableText :value="content.progress_summary" :editable="canEdit" placeholder="本周完成 xx 工作内容，主要风险为..." @save="onSaveField('progress_summary', $event)" />
        </div>
      </div>

      <!-- 4. 专项全景图 -->
      <div class="sec">
        <div class="sec-head">
          <span>专项全景图</span>
          <el-upload
            v-if="auth.isAdmin.value"
            :auto-upload="false"
            :on-change="onUploadPanorama"
            :show-file-list="false"
            accept="image/*"
          >
            <el-button size="small">{{ content.panorama_image_name ? '替换图片' : '上传图片' }}</el-button>
          </el-upload>
        </div>
        <div class="sec-body panorama-body">
          <img v-if="panoramaSrc" :src="panoramaSrc" alt="专项全景图" class="panorama-img" />
          <div v-else class="panorama-empty">还没有上传全景图（一般是用逻辑框图）</div>
        </div>
      </div>

      <!-- 5. 专项事务 -->
      <div class="sec">
        <div class="sec-head">
          <span>专项事务</span>
          <el-button v-if="canEdit" size="small" :icon="Plus" @click="openItemDialog('task', null)">新增事务</el-button>
        </div>
        <el-table :data="tasks" border stripe size="small" style="width: 100%">
          <el-table-column type="index" label="序号" width="70" align="center" />
          <el-table-column prop="content" label="事务内容" min-width="260">
            <template #default="{ row }">
              <span class="cell-multiline">{{ row.content || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="progress" label="当前进展" min-width="200">
            <template #default="{ row }">
              <span class="cell-multiline">{{ row.progress || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="owner" label="责任人" width="120" />
          <el-table-column prop="planned_close_date" label="计划闭环时间" width="140" />
          <el-table-column v-if="canEdit" label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openItemDialog('task', row)">编辑</el-button>
              <el-button size="small" type="danger" @click="onRemoveItem('task', row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 6. 风险和问题 -->
      <div class="sec">
        <div class="sec-head">
          <span>风险和问题</span>
          <el-button v-if="canEdit" size="small" :icon="Plus" @click="openItemDialog('risk', null)">新增风险</el-button>
        </div>
        <el-table :data="risks" border stripe size="small" style="width: 100%">
          <el-table-column type="index" label="序号" width="70" align="center" />
          <el-table-column prop="content" label="问题内容" min-width="260">
            <template #default="{ row }">
              <span class="cell-multiline">{{ row.content || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="progress" label="当前进展" min-width="200">
            <template #default="{ row }">
              <span class="cell-multiline">{{ row.progress || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="owner" label="责任人" width="120" />
          <el-table-column prop="planned_close_date" label="计划闭环时间" width="140" />
          <el-table-column v-if="canEdit" label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openItemDialog('risk', row)">编辑</el-button>
              <el-button size="small" type="danger" @click="onRemoveItem('risk', row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 7. 专项阵型 -->
      <div class="sec">
        <div class="sec-head">
          <span>专项阵型</span>
          <template v-if="canEdit">
            <el-button size="small" @click="addFormationRow">+行</el-button>
            <el-button size="small" @click="addFormationCol">+列</el-button>
            <el-button size="small" @click="saveFormation" :loading="formationSaving">保存阵型</el-button>
          </template>
        </div>
        <div class="formation-wrap">
          <table v-if="formation.rows.length || formation.headers.length" class="formation-table">
            <thead>
              <tr>
                <th v-for="(h, ci) in formation.headers" :key="'h' + ci">
                  <input
                    v-if="canEdit"
                    v-model="formation.headers[ci]"
                    class="formation-input bold"
                    placeholder="列标题"
                  />
                  <span v-else>{{ h }}</span>
                  <el-button
                    v-if="canEdit && formation.headers.length > 1"
                    class="del-col-btn"
                    size="small"
                    link
                    @click="removeFormationCol(ci)"
                  >×</el-button>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, ri) in formation.rows" :key="'r' + ri">
                <td v-for="(_, ci) in formation.headers" :key="'c' + ri + '-' + ci">
                  <input
                    v-if="canEdit"
                    v-model="formation.rows[ri][ci]"
                    class="formation-input"
                  />
                  <span v-else>{{ formation.rows[ri][ci] }}</span>
                  <el-button
                    v-if="canEdit && ci === formation.headers.length - 1"
                    class="del-row-btn"
                    size="small"
                    link
                    @click="removeFormationRow(ri)"
                  >×</el-button>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="muted">点击 +列 / +行 开始填写阵型</div>
        </div>
      </div>
    </div>

    <!-- 里程碑对话框 -->
    <el-dialog v-model="msDialog.visible" :title="msDialog.editing != null ? '编辑里程碑' : '新增里程碑'" width="440px">
      <el-form :model="msDialog.form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="msDialog.form.name" />
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
          <el-input v-model="itemDialog.form.content" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="当前进展">
          <el-input v-model="itemDialog.form.progress" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="责任人">
          <el-input v-model="itemDialog.form.owner" />
        </el-form-item>
        <el-form-item label="计划闭环时间">
          <el-input v-model="itemDialog.form.planned_close_date" placeholder="YYYY-MM-DD 或自由文本" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="itemDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="onSaveItem">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import http, { specialApi } from '../api'
import { auth } from '../store/auth'
import EditableText from '../components/EditableText.vue'
import MilestoneTimeline from '../components/MilestoneTimeline.vue'
import { checkStorageOrWarn } from '../store/storage'

const route = useRoute()
const loading = ref(false)
const special = ref(null)
const content = ref({ goal: '', progress_summary: '', panorama_image_path: '', panorama_image_name: '', milestones_json: '[]', formation_json: '{"headers":[],"rows":[]}', version: 0 })
const tasks = ref([])
const risks = ref([])
const milestones = ref([])
const formation = ref({ headers: [], rows: [] })
const formationSaving = ref(false)
const panoramaSrc = ref('')

const canEdit = computed(() => auth.isLoggedIn.value)

const msDialog = reactive({ visible: false, editing: null, form: { name: '', date: '', status: 'planning' } })
const itemDialog = reactive({ visible: false, editing: null, kind: 'task', form: defaultItem() })

function defaultItem() {
  return { content: '', progress: '', owner: '', planned_close_date: '' }
}

async function load() {
  loading.value = true
  try {
    const slug = route.params.slug
    const { data } = await specialApi.detailBySlug(slug)
    special.value = data
    content.value = data.content || content.value
    tasks.value = data.tasks || []
    risks.value = data.risks || []
    parseMilestones()
    parseFormation()
    await loadPanorama()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

function parseMilestones() {
  try {
    const arr = JSON.parse(content.value.milestones_json || '[]')
    milestones.value = Array.isArray(arr) ? arr : []
  } catch {
    milestones.value = []
  }
}

function parseFormation() {
  try {
    const obj = JSON.parse(content.value.formation_json || '{}')
    formation.value = {
      headers: Array.isArray(obj.headers) ? [...obj.headers] : [],
      rows: Array.isArray(obj.rows) ? obj.rows.map(r => [...r]) : [],
    }
  } catch {
    formation.value = { headers: [], rows: [] }
  }
}

async function loadPanorama() {
  // 仅在路径存在时拉取
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
  if (msDialog.editing != null) {
    next[msDialog.editing] = { ...msDialog.form }
  } else {
    next.push({ ...msDialog.form })
  }
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

// 全景图：el-upload 在 auto-upload=false 时由 on-change 派发，
// 真实 File 在 uploadFile.raw 上。
async function onUploadPanorama(uploadFile) {
  const file = uploadFile?.raw || uploadFile
  if (!file || !file.type || !file.type.startsWith('image/')) {
    ElMessage.warning('仅支持图片')
    return
  }
  await checkStorageOrWarn()  // 上传前提示磁盘空间情况
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
    ? { content: row.content, progress: row.progress, owner: row.owner, planned_close_date: row.planned_close_date }
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

function removeFormationRow(ri) {
  formation.value.rows.splice(ri, 1)
}

function removeFormationCol(ci) {
  formation.value.headers.splice(ci, 1)
  formation.value.rows.forEach(r => r.splice(ci, 1))
}

async function saveFormation() {
  formationSaving.value = true
  try {
    const { data } = await specialApi.updateContent(special.value.id, {
      version: content.value.version,
      formation_json: JSON.stringify(formation.value),
    })
    content.value = data
    parseFormation()
    ElMessage.success('阵型已保存')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    formationSaving.value = false
  }
}

watch(() => route.params.slug, load)
onMounted(load)
</script>

<style scoped>
.special-page {
  min-height: 200px;
}
.page-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}
.sec-title-main {
  background: #fff;
  text-align: center;
  font-size: 18px;
  font-weight: 600;
  padding: 12px 20px;
  border-bottom: 1px solid #ebeef5;
  position: relative;
}
.sec-title-main .owner {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
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
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}
.sec-head > :first-child { flex: 1; }
.sec-body {
  padding: 12px 16px;
  min-height: 60px;
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
.muted { color: #909399; padding: 12px 16px; }

/* 阵型表格 */
.formation-wrap {
  padding: 12px 16px;
  overflow-x: auto;
}
.formation-table {
  border-collapse: collapse;
  width: 100%;
}
.formation-table th, .formation-table td {
  border: 1px solid #dcdfe6;
  padding: 4px 6px;
  min-width: 100px;
  height: 32px;
  position: relative;
  vertical-align: middle;
}
.formation-table th {
  background: #f5f7fa;
  font-weight: 600;
}
.formation-input {
  border: none;
  outline: none;
  width: 100%;
  background: transparent;
  font-size: 13px;
}
.formation-input.bold { font-weight: 600; text-align: center; }
.del-col-btn {
  position: absolute;
  right: 2px;
  top: 50%;
  transform: translateY(-50%);
  padding: 0 6px;
  color: #f56c6c;
}
.del-row-btn {
  position: absolute;
  right: -22px;
  top: 50%;
  transform: translateY(-50%);
  padding: 0 4px;
  color: #f56c6c;
}
</style>
