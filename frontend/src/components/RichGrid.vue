<template>
  <div class="rich-grid">
    <!-- 编辑工具条 -->
    <div v-if="editable" class="rg-toolbar">
      <span class="rg-tip">{{ selDesc }}</span>
      <el-button-group>
        <el-button size="small" :disabled="!sel" @click="setAlign('left')">左对齐</el-button>
        <el-button size="small" :disabled="!sel" @click="setAlign('center')">居中</el-button>
      </el-button-group>
      <el-button-group>
        <el-button size="small" :disabled="!isBodySel" @click="setColor('')">
          <span class="swatch" style="background:#303133" /> 黑
        </el-button>
        <el-button size="small" :disabled="!isBodySel" @click="setColor('#C7000B')">
          <span class="swatch" style="background:#C7000B" /> 红
        </el-button>
        <el-button size="small" :disabled="!isBodySel" @click="setColor('#1565C0')">
          <span class="swatch" style="background:#1565C0" /> 蓝
        </el-button>
      </el-button-group>
      <el-button size="small" :disabled="!isHeaderSel" @click="mergeHeader">合并表头→</el-button>
      <el-button size="small" :disabled="!canSplit" @click="splitHeader">拆分表头</el-button>
      <div class="spacer" />
      <el-button size="small" @click="addCol">+列</el-button>
      <el-button size="small" @click="addRow">+行</el-button>
    </div>

    <table class="rg-table">
      <thead>
        <tr>
          <th
            v-for="(h, hi) in model.headers"
            :key="'h' + hi"
            :colspan="h.colspan || 1"
            :class="{ selected: isSel('header', hi) }"
            :style="{ textAlign: h.align || 'center' }"
            @click="editable && selectCell('header', 0, hi)"
          >
            <input
              v-if="editable"
              v-model="h.text"
              class="rg-input bold"
              :style="{ textAlign: h.align || 'center' }"
              placeholder="表头"
              @input="emitUpdate"
            />
            <span v-else>{{ h.text }}</span>
            <button
              v-if="editable && model.headers.length > 1"
              class="rg-del col"
              type="button"
              title="删除该列组"
              @click.stop="removeHeader(hi)"
            >×</button>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, ri) in model.rows" :key="'r' + ri">
          <td
            v-for="(cell, ci) in row"
            :key="'c' + ri + '-' + ci"
            :class="{ selected: isSel('body', ri, ci) }"
            :style="{ textAlign: cell.align || 'left', color: cell.color || '#303133' }"
            @click="editable && selectCell('body', ri, ci)"
          >
            <input
              v-if="editable"
              v-model="cell.text"
              class="rg-input"
              :style="{ textAlign: cell.align || 'left', color: cell.color || '#303133' }"
              @input="emitUpdate"
            />
            <span v-else>{{ cell.text }}</span>
            <button
              v-if="editable && ci === row.length - 1 && model.rows.length > 1"
              class="rg-del row"
              type="button"
              title="删除此行"
              @click.stop="removeRow(ri)"
            >×</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
/**
 * 富表格编辑器：在 FormationGrid 基础上增加
 *  - 表头合并 / 拆分（colspan）
 *  - 单元格对齐（左 / 居中）
 *  - 正文单元格字体颜色（黑 / 红 / 蓝）
 *  - 删除行 / 删除列组
 *
 * 数据模型（v-model 双向绑定整个 grid 对象）：
 *   {
 *     title: string,
 *     headers: [{ text, colspan, align }],   // sum(colspan) === 正文列数
 *     rows: [ [{ text, align, color }, ...], ... ]
 *   }
 * 兼容旧格式：headers 为 string[]、rows 为 string[][]（由父级 normalize）。
 */
import { computed, ref } from 'vue'

const props = defineProps({
  modelValue: { type: Object, required: true },
  editable: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

// 直接引用 props.modelValue（保持对父级替换的响应式）
const model = computed(() => props.modelValue)

const sel = ref(null) // { type:'header'|'body', r, c }

const isBodySel = computed(() => sel.value?.type === 'body')
const isHeaderSel = computed(() => sel.value?.type === 'header')
const canSplit = computed(
  () => isHeaderSel.value && (model.value.headers[sel.value.c]?.colspan || 1) > 1,
)
const selDesc = computed(() => {
  if (!sel.value) return '点击单元格后可设置对齐 / 颜色 / 合并表头'
  return sel.value.type === 'header' ? '已选中表头' : '已选中正文单元格'
})

function emitUpdate() {
  emit('update:modelValue', model.value)
}

function selectCell(type, r, c) {
  sel.value = { type, r, c }
}
function isSel(type, r, c = 0) {
  const s = sel.value
  if (!s || s.type !== type) return false
  return type === 'header' ? s.c === c : s.r === r && s.c === c
}

function bodyColCount() {
  return model.value.headers.reduce((n, h) => n + (h.colspan || 1), 0)
}

function setAlign(align) {
  const s = sel.value
  if (!s) return
  if (s.type === 'header') model.value.headers[s.c].align = align
  else model.value.rows[s.r][s.c].align = align
  emitUpdate()
}
function setColor(color) {
  const s = sel.value
  if (!s || s.type !== 'body') return
  model.value.rows[s.r][s.c].color = color
  emitUpdate()
}

function mergeHeader() {
  const s = sel.value
  if (!s || s.type !== 'header') return
  const hs = model.value.headers
  if (s.c >= hs.length - 1) return // 已是最后一个
  hs[s.c].colspan = (hs[s.c].colspan || 1) + (hs[s.c + 1].colspan || 1)
  hs.splice(s.c + 1, 1)
  emitUpdate()
}
function splitHeader() {
  const s = sel.value
  if (!s || s.type !== 'header') return
  const hs = model.value.headers
  const span = hs[s.c].colspan || 1
  if (span <= 1) return
  hs[s.c].colspan = 1
  const extra = []
  for (let i = 1; i < span; i++) extra.push({ text: '', colspan: 1, align: 'center' })
  hs.splice(s.c + 1, 0, ...extra)
  emitUpdate()
}

function addCol() {
  model.value.headers.push({ text: `列${model.value.headers.length + 1}`, colspan: 1, align: 'center' })
  model.value.rows.forEach(r => r.push({ text: '', align: 'left', color: '' }))
  emitUpdate()
}
function removeHeader(hi) {
  const hs = model.value.headers
  if (hs.length <= 1) return
  // 计算该表头组覆盖的正文列起始偏移
  let offset = 0
  for (let i = 0; i < hi; i++) offset += hs[i].colspan || 1
  const span = hs[hi].colspan || 1
  hs.splice(hi, 1)
  model.value.rows.forEach(r => r.splice(offset, span))
  if (sel.value?.type === 'header') sel.value = null
  emitUpdate()
}
function addRow() {
  const n = bodyColCount()
  model.value.rows.push(Array.from({ length: n }, () => ({ text: '', align: 'left', color: '' })))
  emitUpdate()
}
function removeRow(ri) {
  if (model.value.rows.length <= 1) return
  model.value.rows.splice(ri, 1)
  if (sel.value?.type === 'body') sel.value = null
  emitUpdate()
}
</script>

<style scoped>
.rich-grid { font-family: '微软雅黑', 'Microsoft YaHei', sans-serif; }
.rg-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 6px 8px;
  background: #fafbfc;
  border: 1px solid #ebeef5;
  border-bottom: none;
}
.rg-toolbar .spacer { flex: 1; }
.rg-tip { font-size: 12px; color: #909399; }
.swatch {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
  vertical-align: middle;
  margin-right: 2px;
}
.rg-table {
  border-collapse: collapse;
  width: 100%;
}
.rg-table th, .rg-table td {
  border: 1px solid #dcdfe6;
  padding: 4px 6px;
  min-width: 90px;
  height: 32px;
  position: relative;
  vertical-align: middle;
}
.rg-table th { background: #f5f7fa; font-weight: 600; }
.rg-table th.selected, .rg-table td.selected {
  outline: 2px solid #C7000B;
  outline-offset: -2px;
}
.rg-input {
  border: none;
  outline: none;
  width: 100%;
  background: transparent;
  font-size: 13px;
  font-family: inherit;
  color: inherit;
}
.rg-input.bold { font-weight: 600; }
.rg-del {
  position: absolute;
  border: none;
  background: transparent;
  color: #f56c6c;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
}
.rg-del.col { right: 2px; top: 2px; }
.rg-del.row { right: -22px; top: 50%; transform: translateY(-50%); }
.rg-del:hover { color: #c45656; }
</style>
