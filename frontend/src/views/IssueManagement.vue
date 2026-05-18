<template>
  <div class="issue-page">

    <!-- ── 管理员配置区 ─────────────────────────────── -->
    <el-card v-if="isAdmin" shadow="never" class="config-card">
      <el-form :inline="true" size="small" label-position="left">
        <el-form-item label="报表目录">
          <el-input v-model="cfg.reportPath" placeholder="填目录路径（按 _YYYYMMDD 取最新）或具体 xlsx 路径" style="width:380px" clearable />
          <el-button style="margin-left:6px" @click="saveCfg('reportPath')">保存</el-button>
        </el-form-item>
        <el-form-item label="刷新脚本" style="margin-left:16px">
          <el-input v-model="cfg.scriptPath" placeholder="脚本路径（.py / .bat / .exe）" style="width:280px" clearable />
          <el-button style="margin-left:6px" @click="saveCfg('scriptPath')">保存</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ── 模式切换栏 ────────────────────────────────── -->
    <div class="mode-bar">
      <el-button-group>
        <el-button :type="mode==='today'  ? 'primary' : ''" @click="switchMode('today')">
          <el-icon><DataLine /></el-icon> 当天数据
        </el-button>
        <el-button :type="mode==='trend'  ? 'primary' : ''" @click="switchMode('trend')">
          <el-icon><TrendCharts /></el-icon> 查看趋势
        </el-button>
      </el-button-group>

      <!-- 日期选择器（当天数据模式） -->
      <el-select
        v-if="mode==='today' && availableDates.length"
        v-model="selectedDate"
        placeholder="选择日期"
        size="small"
        style="width:150px"
        @change="onDateChange"
      >
        <el-option
          v-for="d in availableDates"
          :key="d"
          :label="d"
          :value="d"
        />
      </el-select>

      <span v-if="fileHint" class="file-hint">
        <el-icon><Document /></el-icon> {{ fileHint }}
      </span>

      <el-button
        v-if="todayData?.raw"
        type="success"
        :icon="Download"
        :loading="exporting"
        style="margin-left:auto"
        @click="exportPptx"
      >导出 PPT</el-button>
    </div>

    <!-- ══════════════════════════════════════════════ -->
    <!-- 模式 1：当天数据                                -->
    <!-- ══════════════════════════════════════════════ -->
    <template v-if="mode==='today'">
      <div v-if="loading" class="hint">加载中…</div>
      <el-empty v-else-if="!todayData?.configured" description="请配置报表目录" />

      <template v-else-if="todayData?.raw">
        <!-- 统计卡片 -->
        <div class="stat-row">
          <div class="stat-card" @click="openDrill({}, '全部问题单')">
            <div class="stat-num">{{ todayData.raw.length }}</div>
            <div class="stat-label">合计</div>
          </div>
          <div class="stat-card sev" @click="openDrill({severity:'严重'},'严重缺陷')">
            <div class="stat-num">{{ countBy('severity','严重') }}</div>
            <div class="stat-label">严重</div>
          </div>
          <div class="stat-card nor" @click="openDrill({severity:'一般'},'一般缺陷')">
            <div class="stat-num">{{ countBy('severity','一般') }}</div>
            <div class="stat-label">一般</div>
          </div>
          <div class="stat-card tip" @click="openDrill({severity:'提示'},'提示缺陷')">
            <div class="stat-num">{{ countBy('severity','提示') }}</div>
            <div class="stat-label">提示</div>
          </div>
        </div>

        <!-- 主内容 -->
        <el-card shadow="never" class="main-card">
          <el-tabs v-model="subTab" @tab-change="onSubTabChange">

            <!-- 统计明细（表格 + 直方图） -->
            <el-tab-pane label="统计明细" name="stats">
              <!-- 按小组×月度 -->
              <div class="section-title">按小组 × 月度</div>
              <el-row :gutter="16">
                <el-col :span="14">
                  <StatsTable
                    :columns="todayData.monthly_by_group.columns"
                    :rows="todayData.monthly_by_group.rows"
                    @cell-click="(r,c,v)=>onMonthlyClick(r,c,v)"
                  />
                </el-col>
                <el-col :span="10">
                  <div ref="monthlyBarEl" class="chart-sm" />
                </el-col>
              </el-row>

              <!-- 按客户分布 -->
              <div class="section-title" style="margin-top:20px">按客户分布</div>
              <el-row :gutter="16">
                <el-col :span="14">
                  <StatsTable
                    :columns="todayData.by_customer.columns"
                    :rows="todayData.by_customer.rows"
                    @cell-click="(r,c,v)=>onCustomerClick(r,c,v)"
                  />
                </el-col>
                <el-col :span="10">
                  <div ref="customerBarEl" class="chart-sm" />
                </el-col>
              </el-row>

              <!-- 特性×小组 -->
              <div class="section-title" style="margin-top:20px">特性 × 小组</div>
              <el-row :gutter="16">
                <el-col :span="14">
                  <StatsTable
                    :columns="todayData.feature_by_group.columns"
                    :rows="todayData.feature_by_group.rows"
                    @cell-click="(r,c,v)=>onFeatureClick(r,c,v)"
                  />
                </el-col>
                <el-col :span="10">
                  <div ref="featureBarEl" class="chart-sm" />
                </el-col>
              </el-row>
            </el-tab-pane>

            <!-- 原始数据 -->
            <el-tab-pane label="原始数据" name="raw">
              <div class="raw-toolbar">
                <el-input v-model="rawSearch" :prefix-icon="Search" clearable
                          placeholder="搜索标题 / 编号 / 责任人 / 小组" style="width:300px" />
                <span class="raw-count">共 {{ filteredRaw.length }} 条</span>
              </div>
              <IssueTable :data="filteredRaw" max-height="540" />
            </el-tab-pane>

          </el-tabs>
        </el-card>
      </template>
    </template>

    <!-- ══════════════════════════════════════════════ -->
    <!-- 模式 2：查看趋势                                -->
    <!-- ══════════════════════════════════════════════ -->
    <template v-else-if="mode==='trend'">
      <div v-if="trendLoading" class="hint">正在汇总所有报表文件…</div>
      <el-empty v-else-if="!trendData" description="暂无趋势数据" />
      <template v-else>
        <el-card shadow="never" class="detail-card">
          <template #header>
            <span class="card-title">每日缺陷趋势 · 按小组</span>
            <span class="card-hint">共 {{ trendData.daily.length }} 个报表文件</span>
          </template>
          <div ref="trendGroupEl" class="chart-lg" />
        </el-card>
        <el-card shadow="never" class="detail-card">
          <template #header><span class="card-title">每日缺陷趋势 · 按严重程度</span></template>
          <div ref="trendSeverityEl" class="chart-lg" />
        </el-card>
        <!-- 数据明细表 -->
        <el-card shadow="never" class="detail-card">
          <template #header><span class="card-title">每日数据明细</span></template>
          <el-table :data="trendData.daily" border stripe size="small" max-height="400">
            <el-table-column prop="date" label="日期" width="120" align="center" />
            <el-table-column prop="file" label="文件" min-width="260" show-overflow-tooltip />
            <el-table-column prop="total" label="合计" width="80" align="center" />
            <el-table-column
              v-for="g in trendData.all_groups" :key="g" :label="g" width="120" align="center"
            >
              <template #default="{ row }">{{ row.by_group[g] ?? 0 }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </template>
    </template>

    <!-- ══════════════════════════════════════════════ -->
    <!-- 模式 3：实时刷新（仅管理员）                     -->
    <!-- ══════════════════════════════════════════════ -->
    <template v-else-if="mode==='script' && isAdmin">
      <el-card shadow="never">
        <template #header><span class="card-title"><el-icon><VideoPlay /></el-icon> 执行刷新脚本</span></template>
        <p class="script-tip">
          脚本路径已在上方管理员配置区设置（issue_script_path）。
          点击「执行」后系统将运行该脚本，执行完毕后可点「查看最新数据」切换至当天数据视图。
        </p>
        <el-alert
          v-if="remoteRunning && !scriptRunning"
          type="warning"
          :title="`脚本正在执行中，请等待完成后再操作${remoteStartedAt ? '（开始于 ' + new Date(remoteStartedAt).toLocaleTimeString() + '）' : ''}`"
          show-icon :closable="false"
          style="margin-bottom:14px"
        />
        <el-button
          type="danger" size="large"
          :loading="scriptRunning"
          :disabled="remoteRunning && !scriptRunning"
          :icon="VideoPlay"
          @click="doRunScript"
        >
          执行脚本
        </el-button>
        <template v-if="scriptResult">
          <el-divider />
          <el-alert
            :type="scriptResult.ok ? 'success' : 'error'"
            :title="scriptResult.ok ? `执行成功（退出码 ${scriptResult.exit_code}）` : `执行失败（退出码 ${scriptResult.exit_code}）`"
            show-icon :closable="false" style="margin-bottom:12px"
          />
          <div v-if="scriptResult.stdout" class="script-out">
            <div class="out-label">标准输出</div>
            <pre>{{ scriptResult.stdout }}</pre>
          </div>
          <div v-if="scriptResult.stderr" class="script-err">
            <div class="out-label">标准错误</div>
            <pre>{{ scriptResult.stderr }}</pre>
          </div>
          <el-button v-if="scriptResult.ok" type="primary" style="margin-top:12px" @click="afterScript">
            查看最新数据
          </el-button>
        </template>
      </el-card>
    </template>

    <!-- ── 钻取抽屉 ─────────────────────────────────── -->
    <el-drawer v-model="drillVisible" :title="drillTitle" size="78%" direction="rtl">
      <div class="drill-meta">共 {{ drillRows.length }} 条</div>
      <IssueTable :data="drillRows" max-height="calc(100vh - 120px)" />
    </el-drawer>

  </div>
</template>

<script setup>
import { computed, defineComponent, h, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { ElMessage, ElTable, ElTableColumn, ElTag } from 'element-plus'
import { DataLine, Document, Download, Search, TrendCharts, VideoPlay } from '@element-plus/icons-vue'
// VideoPlay kept for script mode template (mode still accessible but button removed)
import * as echarts from 'echarts'
import { configApi, downloadBlob, issueApi } from '../api'
import { auth } from '../store/auth'

const isAdmin = auth.isAdmin

// ── 调色板 ────────────────────────────────────────────
const PAL = ['#4073ba','#67C23A','#E6A23C','#F56C6C','#909399','#8E7AD8','#26C9C3','#F9A825']

// ── 内联子组件：统计表格 ──────────────────────────────
const StatsTable = defineComponent({
  props: { columns: Array, rows: Array },
  emits: ['cell-click'],
  setup(props, { emit }) {
    return () => h(ElTable, { data: props.rows || [], border: true, stripe: true, size: 'small' }, {
      default: () => [
        h(ElTableColumn, { prop: 'label', label: '小组', width: 160, fixed: true }),
        ...(props.columns || []).map(col =>
          h(ElTableColumn, { key: col, label: col, align: 'center', width: 90 }, {
            default: ({ row }) => {
              const val = row[col] ?? 0
              const isTotal = col === '合计' || row.label === '合计'
              return h('span', {
                class: val && !isTotal ? 'num-link' : isTotal && val ? 'num-total' : 'num-zero',
                onClick: (val && !isTotal) ? () => emit('cell-click', row.label, col, val) : undefined,
              }, String(val))
            },
          })
        ),
      ],
    })
  },
})

// ── 内联子组件：问题单表格 ────────────────────────────
const IssueTable = defineComponent({
  props: { data: Array, maxHeight: [String, Number] },
  setup(props) {
    const sevType = s => s === '严重' ? 'danger' : s === '一般' ? 'warning' : 'info'
    return () => h(ElTable, {
      data: props.data || [], border: true, stripe: true, size: 'small', maxHeight: props.maxHeight,
    }, {
      default: () => [
        h(ElTableColumn, { prop: 'version',  label: '版本信息',           width: 180, showOverflowTooltip: true }),
        h(ElTableColumn, { prop: 'issue_id', label: '缺陷业务编号',       width: 200 }),
        h(ElTableColumn, { prop: 'title',    label: '标题', minWidth: 260, showOverflowTooltip: true }),
        h(ElTableColumn, { prop: 'owner',    label: '当前责任人',          width: 110 }),
        h(ElTableColumn, { prop: 'group',    label: '当前责任人所属小组',  width: 160 }),
        h(ElTableColumn, { prop: 'progress', label: '进展',                width: 100 }),
        h(ElTableColumn, { prop: 'severity', label: '严重程度', width: 90, align: 'center' }, {
          default: ({ row }) => h(ElTag, { type: sevType(row.severity), size: 'small' }, () => row.severity),
        }),
      ],
    })
  },
})

// ── 配置 ─────────────────────────────────────────────
const cfg = ref({ reportPath: '', scriptPath: '' })
async function loadCfg() {
  try {
    const { data } = await configApi.get()
    cfg.value.reportPath = data.issue_report_path || ''
    cfg.value.scriptPath = data.issue_script_path || ''
  } catch { /* 忽略 */ }
}
async function saveCfg(key) {
  const map = { reportPath: 'issue_report_path', scriptPath: 'issue_script_path' }
  try {
    await configApi.save({ [map[key]]: cfg.value[key] })
    ElMessage.success('已保存')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

// ── 模式切换 ──────────────────────────────────────────
const mode = ref('today')
async function switchMode(m) {
  if (mode.value === 'script' && m !== 'script') stopStatusPoll()
  mode.value = m
  if (m === 'script') startStatusPoll()
  else if (m === 'trend' && !trendData.value) await loadTrend()
  else if (m === 'today' && !todayData.value) await loadToday()
  await nextTick()
  if (m === 'trend') initTrendCharts()
}

// ── 日期选择 ──────────────────────────────────────────
const availableDates = ref([])
const selectedDate   = ref(null)

async function loadDates() {
  try {
    const { data } = await issueApi.listDates()
    availableDates.value = data
    if (data.length && !selectedDate.value) {
      selectedDate.value = data[0]
    }
  } catch { /* 忽略，可能是平铺结构 */ }
}

async function onDateChange() {
  todayData.value = null
  await loadToday()
  await nextTick()
  initTodayCharts()
}

// ── 当天数据 ──────────────────────────────────────────
const todayData  = ref(null)
const loading    = ref(false)
const subTab     = ref('stats')
const rawSearch  = ref('')

async function loadToday() {
  loading.value = true
  try {
    const { data } = await issueApi.getData(selectedDate.value || null)
    todayData.value = data
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '读取失败')
  } finally {
    loading.value = false
  }
}

const filteredRaw = computed(() => {
  if (!todayData.value?.raw) return []
  const q = rawSearch.value.trim().toLowerCase()
  if (!q) return todayData.value.raw
  return todayData.value.raw.filter(r =>
    [r.issue_id, r.title, r.owner, r.group, r.progress].some(v => v?.toLowerCase().includes(q))
  )
})

function countBy(field, val) {
  return todayData.value?.raw?.filter(r => r[field] === val).length ?? 0
}

// ── 趋势数据 ──────────────────────────────────────────
const trendData    = ref(null)
const trendLoading = ref(false)

async function loadTrend() {
  trendLoading.value = true
  try {
    const { data } = await issueApi.getTrend()
    trendData.value = data
    await nextTick()
    initTrendCharts()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '趋势加载失败')
  } finally {
    trendLoading.value = false
  }
}

// ── 脚本执行 & 状态轮询 ───────────────────────────────
const scriptRunning   = ref(false)
const scriptResult    = ref(null)
const remoteRunning   = ref(false)
const remoteStartedAt = ref(null)
let   _statusTimer    = null

async function fetchScriptStatus() {
  try {
    const { data } = await issueApi.scriptStatus()
    remoteRunning.value   = data.running
    remoteStartedAt.value = data.started_at
  } catch {}
}

function startStatusPoll() {
  fetchScriptStatus()
  _statusTimer = setInterval(fetchScriptStatus, 3000)
}

function stopStatusPoll() {
  if (_statusTimer) { clearInterval(_statusTimer); _statusTimer = null }
  remoteRunning.value   = false
  remoteStartedAt.value = null
}

async function doRunScript() {
  scriptRunning.value = true
  scriptResult.value  = null
  try {
    const { data } = await issueApi.runScript()
    scriptResult.value = data
    if (data.ok) ElMessage.success('脚本执行成功')
    else         ElMessage.warning('脚本执行完毕，退出码非 0，请检查输出')
  } catch (e) {
    const msg = e.response?.data?.detail || '执行失败'
    ElMessage.error(msg)
  } finally {
    scriptRunning.value = false
    fetchScriptStatus()
  }
}

async function afterScript() {
  mode.value = 'today'
  todayData.value = null
  await loadToday()
  await nextTick()
  initTodayCharts()
}

// ── 刷新 & 导出 ───────────────────────────────────────
async function refresh() {
  if (mode.value === 'trend') await loadTrend()
  else { await loadToday(); await nextTick(); initTodayCharts() }
}

const exporting = ref(false)
async function exportPptx() {
  exporting.value = true
  try {
    const resp = await issueApi.exportPptx(selectedDate.value || null)
    const ts   = new Date().toISOString().replace(/[:.T]/g, '-').slice(0, 19)
    downloadBlob(resp.data, `缺陷统计报表_${ts}.pptx`)
    ElMessage.success('已导出')
  } catch (e) {
    let msg = '导出失败'
    try {
      if (e.response?.data instanceof Blob) {
        const text = await e.response.data.text()
        msg = JSON.parse(text).detail || msg
      } else {
        msg = e.response?.data?.detail || msg
      }
    } catch {}
    ElMessage.error(msg)
  } finally {
    exporting.value = false
  }
}

// ── 文件提示 ──────────────────────────────────────────
const fileHint = computed(() => {
  const d = todayData.value
  if (!d?.actual_file) return ''
  return d.file_mtime ? `${d.actual_file} · ${d.file_mtime}` : d.actual_file
})

// ── 钻取 ─────────────────────────────────────────────
const drillVisible = ref(false)
const drillTitle   = ref('')
const drillRows    = ref([])

function openDrill(filters, title = '问题单明细') {
  let rows = todayData.value?.raw || []
  if (filters.severity)   rows = rows.filter(r => r.severity   === filters.severity)
  if (filters.group)      rows = rows.filter(r => r.group      === filters.group)
  if (filters.year_month) rows = rows.filter(r => r.year_month === filters.year_month)
  if (filters.category)   rows = rows.filter(r => r.category   === filters.category)
  if (filters.feature)    rows = rows.filter(r => r.feature    === filters.feature)
  drillRows.value   = rows
  drillTitle.value  = title
  drillVisible.value = true
}

function onMonthlyClick(group, col, v) {
  if (!v) return
  const f = {}; const t = []
  if (group !== '合计') { f.group = group; t.push(group) }
  if (col   !== '合计') { f.year_month = col; t.push(col) }
  openDrill(f, t.join(' · ') || '全部')
}
function onCustomerClick(group, col, v) {
  if (!v) return
  const f = {}; const t = []
  if (group !== '合计') { f.group = group; t.push(group) }
  if (col   !== '合计') { f.category = col; t.push(`客户:${col}`) }
  openDrill(f, t.join(' · ') || '全部')
}
function onFeatureClick(group, col, v) {
  if (!v) return
  const f = {}; const t = []
  if (group !== '合计') { f.group = group; t.push(group) }
  if (col   !== '合计') { f.feature = col; t.push(`特性:${col}`) }
  openDrill(f, t.join(' · ') || '全部')
}

// ── ECharts 管理 ─────────────────────────────────────
const monthlyBarEl   = ref(null)
const customerBarEl  = ref(null)
const featureBarEl   = ref(null)
const trendGroupEl   = ref(null)
const trendSeverityEl = ref(null)

const instances = {}
function setChart(key, el, option) {
  if (!el) return
  if (!instances[key]) instances[key] = echarts.init(el)
  instances[key].setOption(option, { notMerge: true })
}

function onSubTabChange(tab) {
  nextTick(() => {
    if (tab === 'stats') initStatsBarCharts()
    Object.values(instances).forEach(c => c.resize())
  })
}

function _stackedBarOption(cross, labelField = 'label') {
  const { columns = [], rows = [] } = cross
  const xLabels = columns.filter(c => c !== '合计')
  const series  = rows.filter(r => r.label !== '合计')
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: series.map(s => s.label), bottom: 0, type: 'scroll' },
    grid:   { top: 10, left: 50, right: 10, bottom: 50 },
    xAxis:  { type: 'category', data: xLabels, axisLabel: { rotate: xLabels.length > 5 ? 30 : 0 } },
    yAxis:  { type: 'value', minInterval: 1 },
    series: series.map((s, i) => ({
      name: s.label, type: 'bar', stack: 'total',
      color: PAL[i % PAL.length],
      data: xLabels.map(x => s[x] ?? 0),
      label: { show: false },
    })),
  }
}

function initStatsBarCharts() {
  const d = todayData.value
  if (!d) return
  if (monthlyBarEl.value)  setChart('monthlyBar',  monthlyBarEl.value,  _stackedBarOption(d.monthly_by_group))
  if (customerBarEl.value) setChart('customerBar', customerBarEl.value, _stackedBarOption(d.by_customer))
  if (featureBarEl.value)  setChart('featureBar',  featureBarEl.value,  _stackedBarOption(d.feature_by_group))
}

function initTodayCharts() {
  nextTick(() => {
    if (subTab.value === 'stats') initStatsBarCharts()
  })
}

function initTrendCharts() {
  const td = trendData.value
  if (!td) return
  const dates    = td.daily.map(d => d.date)
  const groups   = td.all_groups
  const sevs     = td.all_severities
  const SEV_CLR  = { '严重': '#F56C6C', '一般': '#E6A23C', '提示': '#909399' }

  if (trendGroupEl.value) {
    setChart('trendGroup', trendGroupEl.value, {
      tooltip: { trigger: 'axis' },
      legend: { data: groups, bottom: 0, type: 'scroll' },
      grid:   { top: 20, left: 50, right: 20, bottom: 50 },
      xAxis:  { type: 'category', data: dates, axisLabel: { rotate: dates.length > 10 ? 30 : 0 } },
      yAxis:  { type: 'value', minInterval: 1, name: '缺陷数' },
      series: groups.map((g, i) => ({
        name: g, type: 'line', smooth: true, symbolSize: 7,
        color: PAL[i % PAL.length],
        data: td.daily.map(d => d.by_group[g] ?? 0),
      })),
    })
  }

  if (trendSeverityEl.value) {
    setChart('trendSeverity', trendSeverityEl.value, {
      tooltip: { trigger: 'axis' },
      legend: { data: sevs, bottom: 0 },
      grid:   { top: 20, left: 50, right: 20, bottom: 50 },
      xAxis:  { type: 'category', data: dates, axisLabel: { rotate: dates.length > 10 ? 30 : 0 } },
      yAxis:  { type: 'value', minInterval: 1, name: '缺陷数' },
      series: sevs.map(s => ({
        name: s, type: 'line', smooth: true, symbolSize: 8, lineWidth: 2,
        color: SEV_CLR[s] || PAL[0],
        data: td.daily.map(d => d.by_severity[s] ?? 0),
        areaStyle: { opacity: 0.08 },
      })),
    })
  }
}

// ── 监听数据变化后更新图表 ───────────────────────────
watch(todayData, async () => {
  await nextTick()
  initTodayCharts()
})

watch(trendData, async () => {
  await nextTick()
  initTrendCharts()
})

// ── resize ────────────────────────────────────────────
function onResize() { Object.values(instances).forEach(c => c.resize()) }

// ── 生命周期 ─────────────────────────────────────────
onMounted(async () => {
  await loadCfg()
  await loadDates()   // 先拿到日期列表，selectedDate 会自动设为最新
  await loadToday()
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  stopStatusPoll()
  Object.values(instances).forEach(c => c.dispose())
  window.removeEventListener('resize', onResize)
})
</script>

<style scoped>
.issue-page { display: flex; flex-direction: column; gap: 14px; }

/* 配置卡 */
.config-card :deep(.el-card__body) { padding: 10px 16px; }
.config-card :deep(.el-form-item) { margin-bottom: 0; }

/* 模式栏 */
.mode-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  border: 1px solid #eaecef;
  border-radius: 8px;
  padding: 10px 14px;
  flex-wrap: wrap;
}
.file-hint { color: #606266; font-size: 13px; display: inline-flex; align-items: center; gap: 4px; }

/* 统计卡片 */
.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.stat-card {
  background: #fff; border: 1px solid #eaecef; border-radius: 10px;
  padding: 20px 24px; cursor: pointer; text-align: center;
  transition: all .2s;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px -12px rgba(31,45,61,.3); border-color: #c6e2ff; }
.stat-num  { font-size: 36px; font-weight: 700; color: #303133; line-height: 1.1; }
.stat-label { font-size: 13px; color: #909399; margin-top: 6px; }
.sev .stat-num { color: #f56c6c; } .sev:hover { border-color: #fab6b6; }
.nor .stat-num { color: #e6a23c; } .nor:hover { border-color: #f3d19e; }
.tip .stat-num { color: #909399; }

/* 主卡 */
.main-card :deep(.el-card__body) { padding: 0 16px 16px; }

/* 图表 */
.chart-lg { width: 100%; height: 340px; margin-top: 8px; }
.chart-sm { width: 100%; height: 260px; }

/* 统计明细 */
.section-title {
  font-size: 14px; font-weight: 600; color: #303133;
  margin: 12px 0 8px; padding-left: 8px; border-left: 3px solid #4073ba;
}

/* 数字链接（由 StatsTable 子组件渲染，需穿透） */
:deep(.num-link) {
  color: #409EFF; font-weight: 600; cursor: pointer;
  padding: 2px 6px; border-radius: 4px; display: inline-block; min-width: 24px;
}
:deep(.num-link:hover) { background: #ecf5ff; }
:deep(.num-total) { color: #303133; font-weight: 700; display: inline-block; }
:deep(.num-zero)  { color: #c0c4cc; }
:deep(.total-row td) { background: #f5f7fa !important; font-weight: 600; }

/* 原始数据 */
.raw-toolbar { display: flex; align-items: center; gap: 12px; margin: 8px 0 10px; }
.raw-count   { color: #909399; font-size: 13px; }

/* 趋势卡 */
.detail-card { margin-bottom: 14px; }
.detail-card :deep(.el-card__header) { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-size: 15px; font-weight: 600; }
.card-hint  { font-size: 12px; color: #909399; }

/* 脚本模式 */
.script-tip  { color: #606266; font-size: 13px; margin-bottom: 16px; line-height: 1.7; }
.script-out, .script-err { margin-top: 12px; }
.out-label   { font-size: 12px; color: #909399; margin-bottom: 4px; }
.script-out pre { background: #f5f7fa; padding: 12px; border-radius: 6px; font-size: 12px; white-space: pre-wrap; max-height: 300px; overflow: auto; }
.script-err pre { background: #fef0f0; padding: 12px; border-radius: 6px; font-size: 12px; color: #f56c6c; white-space: pre-wrap; max-height: 200px; overflow: auto; }

/* 钻取 */
.drill-meta { color: #606266; font-size: 13px; margin-bottom: 10px; }
</style>
