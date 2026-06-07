<template>
  <div class="dv-panel">
    <!-- ===== 调试版本 ===== -->
    <div class="sec-head">
      <span class="sec-title">客户面调试版本</span>
      <el-button type="primary" size="small" :icon="Plus" @click="openVer()">新增调试版本</el-button>
      <el-button size="small" :icon="Refresh" @click="load">刷新</el-button>
    </div>
    <el-table :data="versions" v-loading="loading" border stripe size="small" style="width: 100%">
      <el-table-column prop="version_no" label="版本号" width="130" fixed show-overflow-tooltip />
      <el-table-column prop="baseline_version" label="基线版本" width="120" show-overflow-tooltip />
      <el-table-column label="目标客户" width="130">
        <template #default="{ row }">
          <el-tag v-if="row.target_customer_name" size="small" effect="plain">{{ row.target_customer_name }}</el-tag>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column label="计划发布" width="110">
        <template #default="{ row }">{{ fmt(row.planned_release_date) || '—' }}</template>
      </el-table-column>
      <el-table-column label="发布时间" width="110">
        <template #default="{ row }">
          <el-tag v-if="row.release_date" size="small" type="success">{{ fmt(row.release_date) }}</el-tag>
          <span v-else class="muted">待发布</span>
        </template>
      </el-table-column>
      <el-table-column label="合入内容" align="center">
        <el-table-column prop="merge_offline_cluster" label="离线集群" min-width="120" show-overflow-tooltip />
        <el-table-column prop="merge_online_flow" label="在线流程" min-width="120" show-overflow-tooltip />
        <el-table-column prop="merge_offline_analysis" label="离线分析软件" min-width="130" show-overflow-tooltip />
      </el-table-column>
      <el-table-column prop="selfcheck_archive" label="自验证报告归档" min-width="140" show-overflow-tooltip />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openVer(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="delVer(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- ===== 诉求收集 ===== -->
    <div class="sec-head" style="margin-top: 22px">
      <span class="sec-title">诉求收集</span>
      <el-button type="primary" size="small" :icon="Plus" @click="openDem()">新增诉求</el-button>
    </div>
    <el-table :data="demands" v-loading="loading" border stripe size="small" style="width: 100%">
      <el-table-column prop="seq" label="序号" width="64" align="center" />
      <el-table-column prop="demand" label="诉求" min-width="200" show-overflow-tooltip />
      <el-table-column prop="problem_solved" label="解决问题" min-width="180" show-overflow-tooltip />
      <el-table-column prop="feature" label="特性" width="130" show-overflow-tooltip />
      <el-table-column label="涉及战场" min-width="150">
        <template #default="{ row }">
          <el-tag v-for="(n, i) in row.battlefield_names" :key="i" size="small" effect="plain" style="margin: 1px 2px">{{ n }}</el-tag>
          <span v-if="!row.battlefield_names?.length" class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column prop="expected_time" label="期望时间" width="110" />
      <el-table-column prop="actual_version" label="实际合入版本" width="130" show-overflow-tooltip />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openDem(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="delDem(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 调试版本 弹窗 -->
    <el-dialog v-model="verVisible" :title="verForm.id ? '编辑调试版本' : '新增调试版本'" width="640px" :close-on-click-modal="false">
      <el-form :model="verForm" label-width="110px">
        <el-form-item label="版本号" required>
          <el-input v-model="verForm.version_no" placeholder="如 C10SPC090T01" />
        </el-form-item>
        <el-form-item label="基线版本">
          <el-input v-model="verForm.baseline_version" />
        </el-form-item>
        <el-form-item label="目标客户">
          <el-select v-model="verForm.target_customer_id" clearable filterable placeholder="选择客户" style="width: 100%">
            <el-option v-for="c in customers" :key="c.id" :value="c.id" :label="custLabel(c)" />
          </el-select>
        </el-form-item>
        <el-form-item label="计划发布时间">
          <el-date-picker v-model="verForm.planned_release_date" type="date" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="发布时间">
          <el-date-picker v-model="verForm.release_date" type="date" value-format="YYYY-MM-DDTHH:mm:ss" placeholder="发布后填写" style="width: 100%" />
        </el-form-item>
        <el-form-item label="离线集群">
          <el-input v-model="verForm.merge_offline_cluster" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="在线流程">
          <el-input v-model="verForm.merge_online_flow" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="离线分析软件">
          <el-input v-model="verForm.merge_offline_analysis" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="自验证报告归档">
          <el-input v-model="verForm.selfcheck_archive" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="verVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveVer">保存</el-button>
      </template>
    </el-dialog>

    <!-- 诉求 弹窗 -->
    <el-dialog v-model="demVisible" :title="demForm.id ? '编辑诉求' : '新增诉求'" width="600px" :close-on-click-modal="false">
      <el-form :model="demForm" label-width="110px">
        <el-form-item label="诉求" required>
          <el-input v-model="demForm.demand" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="解决问题">
          <el-input v-model="demForm.problem_solved" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="特性">
          <el-input v-model="demForm.feature" />
        </el-form-item>
        <el-form-item label="涉及战场">
          <el-select v-model="demForm.battlefields" multiple filterable clearable placeholder="可多选客户" style="width: 100%">
            <el-option v-for="c in customers" :key="c.id" :value="c.id" :label="custLabel(c)" />
          </el-select>
        </el-form-item>
        <el-form-item label="期望时间">
          <el-input v-model="demForm.expected_time" placeholder="如 2026-07 或 7月底" />
        </el-form-item>
        <el-form-item label="实际合入版本">
          <el-input v-model="demForm.actual_version" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="demVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveDem">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { debugVersionApi, debugDemandApi, customerApi } from '../api'

const loading = ref(false)
const saving = ref(false)
const versions = ref([])
const demands = ref([])
const customers = ref([])

function fmt(d) {
  if (!d) return ''
  const dt = new Date(d)
  return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`
}
function custLabel(c) {
  return c.display_name || c.code
}

async function load() {
  loading.value = true
  try {
    const [v, d] = await Promise.all([debugVersionApi.list(), debugDemandApi.list()])
    versions.value = v.data
    demands.value = d.data
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}
async function loadCustomers() {
  try {
    const { data } = await customerApi.list()
    customers.value = data
  } catch { /* 下拉为空不阻塞 */ }
}

// ── 调试版本 ──
const verVisible = ref(false)
const verForm = reactive(blankVer())
function blankVer() {
  return {
    id: null, version: 0, version_no: '', baseline_version: '', target_customer_id: null,
    planned_release_date: null, release_date: null,
    merge_offline_cluster: '', merge_online_flow: '', merge_offline_analysis: '', selfcheck_archive: '',
  }
}
function openVer(row) {
  Object.assign(verForm, blankVer(), row ? { ...row } : {})
  verVisible.value = true
}
async function saveVer() {
  if (!verForm.version_no.trim()) { ElMessage.warning('版本号不能为空'); return }
  saving.value = true
  try {
    if (verForm.id) await debugVersionApi.update(verForm.id, verForm)
    else await debugVersionApi.create(verForm)
    ElMessage.success('已保存')
    verVisible.value = false
    load()
  } catch (e) {
    if (e.response?.status === 409) { verVisible.value = false; load() }
    else ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}
async function delVer(row) {
  await ElMessageBox.confirm(`确认删除调试版本「${row.version_no}」吗？`, '提示', { type: 'warning' })
  try {
    await debugVersionApi.remove(row.id)
    ElMessage.success('已删除')
    load()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '删除失败') }
}

// ── 诉求 ──
const demVisible = ref(false)
const demForm = reactive(blankDem())
function blankDem() {
  return {
    id: null, version: 0, demand: '', problem_solved: '', feature: '',
    battlefields: [], expected_time: '', actual_version: '',
  }
}
function openDem(row) {
  Object.assign(demForm, blankDem(), row ? { ...row, battlefields: [...(row.battlefields || [])] } : {})
  demVisible.value = true
}
async function saveDem() {
  if (!demForm.demand.trim()) { ElMessage.warning('诉求不能为空'); return }
  saving.value = true
  try {
    if (demForm.id) await debugDemandApi.update(demForm.id, demForm)
    else await debugDemandApi.create(demForm)
    ElMessage.success('已保存')
    demVisible.value = false
    load()
  } catch (e) {
    if (e.response?.status === 409) { demVisible.value = false; load() }
    else ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}
async function delDem(row) {
  await ElMessageBox.confirm('确认删除该诉求吗？', '提示', { type: 'warning' })
  try {
    await debugDemandApi.remove(row.id)
    ElMessage.success('已删除')
    load()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '删除失败') }
}

onMounted(() => { load(); loadCustomers() })
</script>

<style scoped>
.dv-panel { padding: 2px; }
.sec-head { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.sec-title { font-size: 15px; font-weight: 600; color: #303133; margin-right: 4px; }
.muted { color: #c0c4cc; }
</style>
