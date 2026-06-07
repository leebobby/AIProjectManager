<template>
  <div class="vt-wrap">
    <div v-if="layout.empty" class="vt-empty">
      暂无可绘制的版本：大版本需至少有「版本范围开始」或迭代版本的「预计发布日期」才能定位到时间轴。
    </div>
    <template v-else>
      <svg
        class="vt-svg"
        :viewBox="`0 0 ${W} ${layout.height}`"
        :style="{ height: layout.height + 'px' }"
        preserveAspectRatio="xMinYMin meet"
      >
        <!-- 月份网格 -->
        <g class="vt-grid">
          <template v-for="t in layout.months" :key="t.x">
            <line :x1="t.x" :y1="layout.top - 6" :x2="t.x" :y2="layout.axisY" />
            <text :x="t.x" :y="layout.axisY + 16" text-anchor="middle">{{ t.label }}</text>
          </template>
        </g>

        <!-- 今天 -->
        <g v-if="layout.todayX != null" class="vt-today">
          <line :x1="layout.todayX" :y1="layout.top - 6" :x2="layout.todayX" :y2="layout.axisY" />
          <text :x="layout.todayX" :y="layout.top - 10" text-anchor="middle">今天</text>
        </g>

        <!-- 每个大版本：主线 or 支线 -->
        <g v-for="mv in layout.majors" :key="mv.id">
          <!-- 支线：从主线对应时间点拉枝 -->
          <path
            v-if="!mv.isMain"
            :d="mv.branchPath"
            class="vt-branch-link"
            :stroke="mv.color"
            fill="none"
          />
          <!-- 主线虚线延伸段（实际区间之外） -->
          <line
            v-if="mv.isMain && mv.preX != null"
            :x1="mv.preX" :y1="mv.y" :x2="mv.startX" :y2="mv.y"
            class="vt-main-dash" :stroke="mv.color"
          />
          <line
            v-if="mv.isMain && mv.postX != null"
            :x1="mv.endX" :y1="mv.y" :x2="mv.postX" :y2="mv.y"
            class="vt-main-dash" :stroke="mv.color"
          />
          <!-- 版本主体线段（实际区间） -->
          <line
            :x1="mv.startX" :y1="mv.y" :x2="mv.endX" :y2="mv.y"
            :stroke="mv.color" :stroke-width="mv.isMain ? 5 : 3" stroke-linecap="round"
          />
          <!-- 发布终点（实心=已实际发布） -->
          <circle
            :cx="mv.endX" :cy="mv.y" :r="mv.isMain ? 6 : 5"
            :fill="mv.released ? mv.color : '#fff'" :stroke="mv.color" stroke-width="2"
          >
            <title>{{ mv.version_no }} {{ mv.released ? '已发布 ' + mv.releaseLabel : '计划至 ' + mv.endLabel }}</title>
          </circle>

          <!-- 迭代版本节点 -->
          <g v-for="n in mv.nodes" :key="n.id">
            <circle :cx="n.x" :cy="mv.y" r="4" :fill="mv.color">
              <title>{{ n.version_no }} {{ n.title }} · {{ n.dateLabel }}</title>
            </circle>
            <text :x="n.x" :y="mv.y - 9" text-anchor="middle" class="vt-node-label">{{ n.version_no }}</text>
          </g>

          <!-- 大版本标签 -->
          <g>
            <rect
              :x="mv.labelX" :y="mv.y - 11" :width="mv.labelW" height="18" rx="9"
              :fill="mv.isMain ? mv.color : '#fff'" :stroke="mv.color"
            />
            <text
              :x="mv.labelX + mv.labelW / 2" :y="mv.y + 2" text-anchor="middle"
              class="vt-major-label" :fill="mv.isMain ? '#fff' : mv.color"
            >{{ mv.isMain ? '主线 ' : '' }}{{ mv.version_no }}</text>
            <title>{{ mv.version_no }} {{ mv.title }}</title>
          </g>
        </g>
      </svg>

      <div v-if="layout.skipped.length" class="vt-skipped">
        未上图（缺少日期）：{{ layout.skipped.join('、') }}
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  majors: { type: Array, default: () => [] },
})

const W = 960
const PALETTE = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#9B59B6', '#1ABC9C', '#909399']

function ts(d) {
  if (!d) return null
  const t = new Date(d).getTime()
  return Number.isNaN(t) ? null : t
}
function dl(t) {
  if (t == null) return ''
  const d = new Date(t)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const layout = computed(() => {
  const padL = 40
  const padR = 28
  const top = 34
  const laneGap = 60

  // 1) 解析每个大版本的起止 + 迭代节点日期
  const raw = props.majors.map((m) => {
    const iters = (m.iteration_versions || [])
      .map((iv) => ({ id: iv.id, version_no: iv.version_no, title: iv.title || '', t: ts(iv.planned_date) }))
      .filter((iv) => iv.t != null)
      .sort((a, b) => a.t - b.t)
    const iterTs = iters.map((iv) => iv.t)
    const startT = ts(m.range_start) ?? (iterTs.length ? Math.min(...iterTs) : null)
    const relT = ts(m.actual_release_date)
    const endT = relT ?? ts(m.range_end) ?? (iterTs.length ? Math.max(...iterTs) : startT)
    return { m, iters, startT, endT, relT }
  })

  const placeable = raw.filter((r) => r.startT != null)
  const skipped = raw.filter((r) => r.startT == null).map((r) => r.m.version_no)
  if (!placeable.length) return { empty: true, skipped }

  // 2) 时间范围
  const allT = []
  placeable.forEach((r) => {
    allT.push(r.startT, r.endT ?? r.startT)
    r.iters.forEach((iv) => allT.push(iv.t))
  })
  let minT = Math.min(...allT)
  let maxT = Math.max(...allT)
  if (minT === maxT) { minT -= 15 * 864e5; maxT += 15 * 864e5 }
  const span = maxT - minT
  minT -= span * 0.04
  maxT += span * 0.04
  const xOf = (t) => padL + ((t - minT) / (maxT - minT)) * (W - padL - padR)

  // 3) 排序：最新（起始最晚）在最上 = 主线
  placeable.sort((a, b) => {
    if (b.startT !== a.startT) return b.startT - a.startT
    return String(b.m.version_no).localeCompare(String(a.m.version_no), 'zh-Hans-CN', { numeric: true })
  })

  const mainY = top + 12
  const majors = placeable.map((r, i) => {
    const color = PALETTE[i % PALETTE.length]
    const y = mainY + i * laneGap
    const startX = xOf(r.startT)
    const endX = xOf(r.endT ?? r.startT)
    const isMain = i === 0
    const labelText = (isMain ? '主线 ' : '') + (r.m.version_no || '')
    const labelW = Math.max(34, labelText.length * 8 + 14)
    // 标签放在起点左侧，避免越界则改放右侧
    let labelX = startX - labelW - 8
    if (labelX < 2) labelX = startX + 8
    const nodes = r.iters.map((iv) => ({
      id: iv.id, version_no: iv.version_no, title: iv.title,
      x: xOf(iv.t), dateLabel: dl(iv.t),
    }))
    const out = {
      id: r.m.id, version_no: r.m.version_no, title: r.m.title || '',
      color, y, startX, endX, isMain, nodes, labelX, labelW,
      released: r.relT != null, releaseLabel: dl(r.relT), endLabel: dl(r.endT),
    }
    if (isMain) {
      // 主线：实际区间外用虚线延伸到整条时间轴两端
      out.preX = startX > padL + 1 ? padL : null
      out.postX = endX < W - padR - 1 ? W - padR : null
    } else {
      // 支线：从主线（mainY）在起点处拉枝下来
      out.branchPath = `M ${startX},${mainY} C ${startX},${mainY + 22} ${startX + 18},${y - 22} ${startX + 18},${y}`
      out.startX = startX + 18
    }
    return out
  })

  // 4) 月份网格
  const months = []
  const d = new Date(minT); d.setDate(1); d.setHours(0, 0, 0, 0)
  while (d.getTime() <= maxT) {
    const t = d.getTime()
    if (t >= minT) {
      const m = d.getMonth() + 1
      months.push({ x: xOf(t), label: m === 1 ? `${d.getFullYear()}/1` : `${m}月` })
    }
    d.setMonth(d.getMonth() + 1)
  }

  const axisY = mainY + (majors.length - 1) * laneGap + 28
  const nowT = Date.now()
  const todayX = nowT >= minT && nowT <= maxT ? xOf(nowT) : null

  return { empty: false, skipped, majors, months, top, axisY, todayX, height: axisY + 24 }
})
</script>

<style scoped>
.vt-wrap {
  width: 100%;
  overflow-x: auto;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 6px 10px 2px;
  margin-bottom: 12px;
}
.vt-svg { width: 100%; min-width: 720px; display: block; }
.vt-empty { color: #909399; font-size: 13px; padding: 18px 8px; }
.vt-grid line { stroke: #f0f2f5; stroke-width: 1; }
.vt-grid text { fill: #c0c4cc; font-size: 11px; }
.vt-today line { stroke: #f56c6c; stroke-width: 1; stroke-dasharray: 3 3; }
.vt-today text { fill: #f56c6c; font-size: 10px; }
.vt-branch-link { stroke-width: 2; opacity: 0.7; }
.vt-main-dash { stroke-width: 2; stroke-dasharray: 4 4; opacity: 0.45; }
.vt-node-label { fill: #909399; font-size: 9px; }
.vt-major-label { font-size: 11px; font-weight: 600; }
</style>
