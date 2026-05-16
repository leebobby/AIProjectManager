<template>
  <div class="roadmap-card">
    <div class="roadmap-header">
      <div class="roadmap-title">{{ project.name }}</div>
      <div class="roadmap-meta">
        <span v-if="project.year">{{ project.year }} 年</span>
        <span v-if="rangeText">{{ rangeText }}</span>
        <span class="tag" :class="{ alt: project.granularity === 'month' }">
          {{ project.granularity === 'month' ? '月度精度' : '季度精度' }}
        </span>
      </div>
    </div>
    <div v-if="project.description" class="roadmap-desc">{{ project.description }}</div>

    <div v-if="!hasContent" class="empty-hint">
      暂无阶段和里程碑数据
    </div>

    <div v-else class="roadmap-scroll">
      <div class="roadmap-canvas" :style="{ height: canvasHeight + 'px' }">
        <svg :viewBox="`0 0 ${WIDTH} ${canvasHeight}`" xmlns="http://www.w3.org/2000/svg">
          <line :x1="40" :y1="AXIS_Y" :x2="WIDTH - 30" :y2="AXIS_Y" stroke="#cbd5e0" stroke-width="2" />
          <polygon
            :points="`${WIDTH - 35},${AXIS_Y - 8} ${WIDTH - 18},${AXIS_Y} ${WIDTH - 35},${AXIS_Y + 8}`"
            fill="#cbd5e0"
          />

          <g v-for="(p, idx) in phasePositions" :key="'phase-' + idx">
            <line :x1="p.x" :y1="AXIS_Y" :x2="p.x" :y2="ANCHOR_Y" :stroke="p.color" stroke-width="1.5" />
            <circle :cx="p.x" :cy="ANCHOR_Y" r="22" :fill="p.color" />
            <text
              :x="p.x"
              :y="ANCHOR_Y + 5"
              text-anchor="middle"
              fill="#fff"
              :font-size="p.label.length > 2 ? 11 : 14"
              font-weight="600"
            >
              {{ p.label }}
            </text>
          </g>

          <g stroke="#cbd5e0" stroke-dasharray="3,3">
            <line
              v-for="m in monthList"
              :key="'ml-' + m"
              :x1="xOfMonth(m)"
              :y1="AXIS_Y"
              :x2="xOfMonth(m)"
              :y2="AXIS_Y + 55"
            />
          </g>
          <g fill="#fff" stroke="#cbd5e0" stroke-width="2">
            <circle
              v-for="m in monthList"
              :key="'mc-' + m"
              :cx="xOfMonth(m)"
              :cy="AXIS_Y"
              r="5"
            />
          </g>
        </svg>

        <div
          v-for="(p, idx) in phasePositions"
          :key="'pb-' + idx"
          class="phase-block"
          :style="{ left: (p.x + 30) + 'px', top: (ANCHOR_Y - 15) + 'px' }"
        >
          <div class="phase-title" :style="{ color: p.color }">{{ p.name }}</div>
          <div v-if="p.goalLines.length" class="phase-row"><span class="k">目标：</span></div>
          <div v-for="(line, i) in p.goalLines" :key="'g-' + i" class="phase-row">{{ line }}</div>
          <div v-if="p.core_products" class="phase-row gap">
            <span class="k">核心产品：</span>{{ p.core_products }}
          </div>
          <template v-if="p.scenarioLines.length">
            <div class="phase-row gap"><span class="k">主要应用场景：</span></div>
            <div v-for="(line, i) in p.scenarioLines" :key="'s-' + i" class="phase-row">{{ line }}</div>
          </template>
        </div>

        <div
          v-for="(ms, idx) in milestonePositions"
          :key="'ms-' + idx"
          class="milestone-block"
          :style="{ left: ms.x + 'px', top: (AXIS_Y + 65) + 'px' }"
        >
          <div class="month-label">{{ ms.month }}月</div>
          <div v-if="ms.title" class="product">{{ ms.title }}</div>
          <div v-else class="product empty">·</div>
          <div v-if="ms.descLines.length" class="desc">
            <div v-for="(line, i) in ms.descLines" :key="'d-' + i">{{ line }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  project: { type: Object, required: true },
})

const WIDTH = 1200
const PAD_L = 60
const PAD_R = 60
const AXIS_Y = 290
const ANCHOR_Y = 200

const monthRange = computed(() => {
  const phases = props.project.phases || []
  const milestones = props.project.milestones || []
  const all = []
  for (const p of phases) {
    if (p.start_month) all.push(p.start_month)
    if (p.end_month) all.push(p.end_month)
  }
  for (const m of milestones) {
    if (m.month) all.push(m.month)
  }
  if (all.length === 0) return { min: 1, max: 12 }
  return { min: Math.min(...all), max: Math.max(...all) }
})

const monthList = computed(() => {
  const { min, max } = monthRange.value
  const out = []
  for (let m = min; m <= max; m++) out.push(m)
  return out
})

const rangeText = computed(() => {
  const { min, max } = monthRange.value
  if (props.project.phases?.length || props.project.milestones?.length) {
    return `${min} 月 — ${max} 月`
  }
  return ''
})

const hasContent = computed(
  () => (props.project.phases?.length || 0) + (props.project.milestones?.length || 0) > 0
)

function xOfMonth(month) {
  const { min, max } = monthRange.value
  const n = max - min + 1
  const slot = (WIDTH - PAD_L - PAD_R) / n
  return PAD_L + (month - min + 0.5) * slot
}

const phasePositions = computed(() => {
  const list = props.project.phases || []
  return list.map((p) => {
    const x = xOfMonth(p.start_month)
    const label = props.project.granularity === 'month'
      ? `${p.start_month}月`
      : `Q${Math.ceil(p.start_month / 3)}`
    return {
      x,
      label,
      name: p.name,
      color: p.color || '#409EFF',
      goalLines: (p.goal || '').split('\n').map((s) => s.trim()).filter(Boolean),
      core_products: p.core_products || '',
      scenarioLines: (p.scenarios || '').split('\n').map((s) => s.trim()).filter(Boolean),
    }
  })
})

const milestonePositions = computed(() => {
  const list = props.project.milestones || []
  return list.map((m) => ({
    x: xOfMonth(m.month),
    month: m.month,
    title: m.title || '',
    descLines: (m.description || '').split('\n').map((s) => s.trim()).filter(Boolean),
  }))
})

const canvasHeight = computed(() => {
  let maxPhaseLines = 0
  for (const p of phasePositions.value) {
    let lines = 1 // title
    if (p.goalLines.length) lines += 1 + p.goalLines.length
    if (p.core_products) lines += 1
    if (p.scenarioLines.length) lines += 1 + p.scenarioLines.length
    if (lines > maxPhaseLines) maxPhaseLines = lines
  }
  let maxMilestoneLines = 0
  for (const m of milestonePositions.value) {
    const lines = (m.title ? 1 : 0) + m.descLines.length + 1
    if (lines > maxMilestoneLines) maxMilestoneLines = lines
  }
  // 阶段块高度估算 + 里程碑块高度估算 + 边距
  const phaseSpace = Math.max(ANCHOR_Y, ANCHOR_Y - 15 + maxPhaseLines * 22)
  const milestoneSpace = AXIS_Y + 65 + Math.max(80, maxMilestoneLines * 20 + 60)
  return Math.max(phaseSpace + 80, milestoneSpace + 20)
})
</script>

<style scoped>
.roadmap-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  padding: 20px 24px 24px;
}

.roadmap-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 12px;
  margin-bottom: 14px;
}
.roadmap-title {
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}
.roadmap-title::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 16px;
  background: #409EFF;
  border-radius: 2px;
}
.roadmap-meta {
  font-size: 12px;
  color: #909399;
  display: flex;
  gap: 8px;
  align-items: center;
}
.roadmap-meta .tag {
  padding: 2px 8px;
  border-radius: 3px;
  background: #f0f7ff;
  color: #409EFF;
  font-size: 11px;
}
.roadmap-meta .tag.alt {
  background: #fef0e7;
  color: #e6a23c;
}

.roadmap-desc {
  font-size: 12px;
  color: #909399;
  margin-bottom: 16px;
  line-height: 1.7;
}

.empty-hint {
  text-align: center;
  color: #c0c4cc;
  padding: 40px 0;
  font-size: 13px;
}

.roadmap-scroll {
  overflow-x: auto;
}
.roadmap-canvas {
  position: relative;
  width: 1200px;
}
.roadmap-canvas svg {
  display: block;
  width: 100%;
  height: 100%;
}

.phase-block {
  position: absolute;
  width: 260px;
  pointer-events: none;
}
.phase-block .phase-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
}
.phase-block .phase-row {
  font-size: 12px;
  line-height: 1.7;
  color: #606266;
}
.phase-block .phase-row .k {
  color: #303133;
  font-weight: 500;
}
.phase-block .phase-row.gap {
  margin-top: 6px;
}

.milestone-block {
  position: absolute;
  width: 130px;
  transform: translateX(-50%);
  text-align: center;
  pointer-events: none;
}
.milestone-block .month-label {
  font-size: 14px;
  color: #303133;
  margin-bottom: 10px;
  font-weight: 500;
}
.milestone-block .product {
  display: inline-block;
  border: 1.5px solid #409EFF;
  color: #409EFF;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  background: #fff;
  min-width: 95px;
  margin-bottom: 8px;
}
.milestone-block .product.empty {
  visibility: hidden;
  margin-bottom: 0;
}
.milestone-block .desc {
  font-size: 11px;
  color: #909399;
  line-height: 1.6;
  padding: 0 4px;
}
</style>
