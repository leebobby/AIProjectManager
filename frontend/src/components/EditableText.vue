<template>
  <div class="editable-text">
    <div v-if="!editing" class="display" :class="{ readonly: !editable, empty: !value }" @click="onEnter">
      <span v-if="value" class="text">{{ value }}</span>
      <span v-else class="ph">{{ placeholder }}</span>
    </div>
    <div v-else class="edit">
      <el-input
        v-model="draft"
        type="textarea"
        :autosize="{ minRows: 2, maxRows: 10 }"
        :placeholder="placeholder"
        @keydown.ctrl.enter.prevent="save"
        @keydown.meta.enter.prevent="save"
      />
      <div class="actions">
        <el-button size="small" type="primary" @click="save">保存 (Ctrl+Enter)</el-button>
        <el-button size="small" @click="cancel">取消</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  value: { type: String, default: '' },
  editable: { type: Boolean, default: true },
  placeholder: { type: String, default: '点击编辑...' },
})
const emit = defineEmits(['save'])

const editing = ref(false)
const draft = ref('')

function onEnter() {
  if (!props.editable) return
  draft.value = props.value || ''
  editing.value = true
}

function save() {
  emit('save', draft.value)
  editing.value = false
}

function cancel() {
  editing.value = false
}
</script>

<style scoped>
.display {
  white-space: pre-wrap;
  word-break: break-word;
  cursor: text;
  padding: 8px 10px;
  border-radius: 4px;
  border: 1px dashed transparent;
  min-height: 48px;
  line-height: 1.6;
}
.display:hover:not(.readonly) {
  background: #f0f7ff;
  border-color: #c6e2ff;
}
.display.readonly {
  cursor: default;
}
.display .ph {
  color: #c0c4cc;
}
.actions {
  margin-top: 6px;
}
</style>
