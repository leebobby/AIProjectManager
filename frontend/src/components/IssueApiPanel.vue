<template>
  <div class="api-panel" v-loading="loading">
    <div class="api-bar">
      <el-tag type="primary" effect="plain">项目：{{ project }}</el-tag>
      <span v-if="data && data.fetched_at" class="muted">拉取于 {{ data.fetched_at }}</span>
      <el-button :icon="Refresh" size="small" :loading="loading" style="margin-left: auto" @click="load">刷新</el-button>
    </div>

    <el-alert
      v-if="!loading && data && !data.configured"
      type="warning" show-icon :closable="false"
      title="未配置 API 脚本"
      description="请管理员在「本地报表」tab 顶部填写「API 脚本」路径（issue_api_script_path），脚本用于按项目调用接口拉取问题单。"
    />
    <el-alert
      v-else-if="!loading && errorMsg"
      type="error" show-icon :closable="false"
      title="拉取失败" :description="errorMsg" style="white-space: pre-wrap"
    />

    <template v-else-if="data && data.configured">
      <!-- 统计卡片 -->
      <div class="stat-row">
        <div class="stat-card" @click="openDrill('', '全部问题单')">
          <div class="stat-num">{{ data.count }}</div><div class="stat-label">合计</div>
        </div>
        <div class="stat-card sev" @click="openDrill('严重', '严重缺陷')">
          <div class="stat-num">{{ sev('严重') }}</div><div class="stat-label">严重</div>
        </div>
        <div class="stat-card nor" @click="openDrill('一般', '一般缺陷')">
          <div class="stat-num">{{ sev('一般') }}</div><div class="stat-label">一般</div>
        </div>
        <div class="stat-card tip" @click="openDrill('提示', '提示缺陷')">
          <div class="stat-num">{{ sev('提示') }}</div><div class="stat-label">提示</div>
        </div>
      </div>

      <el-card shadow="never" class="main-card">
        <el-tabs v-model="tab">
          <el-tab-pane label="统计" name="stats">
            <div class="dim-grid">
              <div class="dim-block">
                <div class="dim-title">按小组</div>
                <div v-if="!byGroup.length" class="muted">暂无</div>
                <div v-for="it in byGroup" :key="it.name" class="dim-row" @click="openDrill('', `小组：${it.name}`, 'group', it.name)">
                  <span class="dim-name" :title="it.name">{{ it.name }}</span>
                  <div class="dim-bar-wrap"><div class="dim-bar" :style="{ width: barW(it.count, byGroup) }"></div></div>
                  <span class="dim-count">{{ it.count }}</span>
                </div>
              </div>
              <div class="dim-block">
                <div class="dim-title">按分类</div>
                <div v-if="!byCustomer.length" class="muted">暂无</div>
                <div v-for="it in byCustomer" :key="it.name" class="dim-row" @click="openDrill('', `分类：${it.name}`, 'category', it.name)">
                  <span class="dim-name" :title="it.name">{{ it.name }}</span>
                  <div class="dim-bar-wrap"><div class="dim-bar cat" :style="{ width: barW(it.count, byCustomer) }"></div></div>
                  <span class="dim-count">{{ it.count }}</span>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="原始数据" name="raw">
            <div class="raw-bar">
              <el-input v-model="search" :prefix-icon="Search" clearable placeholder="搜索标题/编号/责任人/小组" style="width: 320px" />
              <span class="muted">共 {{ filtered.length }} 条</span>
            </div>
            <IssueRawTable :data="filtered" max-height="540" />
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </template>

    <el-drawer v-model="drillVisible" :title="drillTitle" size="72%" direction="rtl">
      <div class="muted" style="margin-bottom: 8px">共 {{ drillRows.length }} 条</div>
      <IssueRawTable :data="drillRows" max-height="calc(100vh - 150px)" />
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, ref, watch } from 'vue'
import { ElMessage, ElTable, ElTableColumn, ElTag } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import { issueApi } from '../api'

const props = defineProps({
  project: { type: String, required: true },
})

// 复用的问题单表格（与本地报表风格一致）
const IssueRawTable = defineComponent({
  props: { data: Array, maxHeight: [String, Number] },
  setup(p) {
    const sevType = (s) => (s === '严重' ? 'danger' : s === '一般' ? 'warning' : 'info')
    return () => h(ElTable, {
      data: p.data || [], border: true, stripe: true, size: 'small', maxHeight: p.maxHeight,
    }, {
      default: () => [
        h(ElTableColumn, { prop: 'version', label: '版本信息', width: 170, showOverflowTooltip: true }),
        h(ElTableColumn, { prop: 'issue_id', label: '缺陷业务编号', width: 200 }),
        h(ElTableColumn, { prop: 'title', label: '标题', minWidth: 260, showOverflowTooltip: true }),
        h(ElTableColumn, { prop: 'owner', label: '当前责任人', width: 110 }),
        h(ElTableColumn, { prop: 'group', label: '当前责任人所属小组', width: 160 }),
        h(ElTableColumn, { prop: 'category', label: '分类', width: 100 }),
        h(ElTableColumn, { prop: 'progress', label: '进展', width: 100 }),
        h(ElTableColumn, { prop: 'severity', label: '严重程度', width: 90, align: 'center' }, {
          default: ({ row }) => h(ElTag, { type: sevType(row.severity), size: 'small' }, () => row.severity || '—'),
        }),
      ],
    })
  },
})

const loading = ref(false)
const data = ref(null)
const tab = ref('stats')
const search = ref('')

const errorMsg = computed(() => data.value?.error || '')
const raw = computed(() => data.value?.raw || [])

function sev(s) {
  return data.value?.by_severity?.[s] || 0
}
function dictToSorted(d) {
  return Object.entries(d || {})
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
}
const byGroup = computed(() => dictToSorted(data.value?.by_group))
const byCustomer = computed(() => dictToSorted(data.value?.by_customer))
function barW(count, items) {
  const max = Math.max(1, ...items.map((i) => i.count))
  return `${Math.round((count / max) * 100)}%`
}

const filtered = computed(() => {
  const kw = search.value.trim().toLowerCase()
  if (!kw) return raw.value
  return raw.value.filter((r) =>
    [r.title, r.issue_id, r.owner, r.group].some((v) => (v || '').toLowerCase().includes(kw)),
  )
})

// 钻取
const drillVisible = ref(false)
const drillTitle = ref('')
const drillRows = ref([])
function openDrill(severity, title, field, value) {
  drillTitle.value = title
  drillRows.value = raw.value.filter((r) => {
    if (severity && r.severity !== severity) return false
    if (field && r[field] !== value) return false
    return true
  })
  drillVisible.value = true
}

async function load() {
  loading.value = true
  try {
    const { data: d } = await issueApi.apiData(props.project)
    data.value = d
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加载失败')
    data.value = { configured: true, error: e.response?.data?.detail || '请求失败', raw: [] }
  } finally {
    loading.value = false
  }
}

watch(() => props.project, load)
onMounted(load)
</script>

<style scoped>
.api-panel { min-height: 200px; }
.api-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.muted { color: #909399; font-size: 13px; }

.stat-row { display: flex; gap: 12px; margin-bottom: 12px; }
.stat-card {
  flex: 1; border-radius: 8px; padding: 14px 18px; cursor: pointer;
  background: #ecf2fc; border: 1px solid #d6e3f8; transition: all 0.15s;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(64,115,186,0.18); }
.stat-card.sev { background: #fef0f0; border-color: #fbc4c4; }
.stat-card.nor { background: #fdf6ec; border-color: #f5dab1; }
.stat-card.tip { background: #f4f4f5; border-color: #e0e0e3; }
.stat-num { font-size: 26px; font-weight: 700; color: #1f2329; line-height: 1.1; }
.stat-label { font-size: 13px; color: #606266; margin-top: 4px; }

.dim-grid { display: flex; gap: 24px; }
.dim-block { flex: 1; }
.dim-title { font-weight: 600; margin-bottom: 10px; }
.dim-row { display: flex; align-items: center; gap: 10px; cursor: pointer; padding: 2px 0; }
.dim-row:hover .dim-name { color: #409EFF; }
.dim-name { flex: 0 0 120px; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dim-bar-wrap { flex: 1 1 auto; background: #f0f2f5; border-radius: 4px; height: 14px; overflow: hidden; }
.dim-bar { height: 100%; background: #409EFF; border-radius: 4px; min-width: 2px; transition: width 0.3s; }
.dim-bar.cat { background: #67C23A; }
.dim-count { flex: 0 0 auto; font-size: 13px; color: #1f2329; font-weight: 600; min-width: 24px; text-align: right; }

.main-card { margin-top: 4px; }
.raw-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
</style>
