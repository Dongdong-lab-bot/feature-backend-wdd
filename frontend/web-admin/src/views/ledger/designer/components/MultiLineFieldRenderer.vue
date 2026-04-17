<template>
  <div class="multi-line-render" :style="containerStyle">
    <textarea
      v-if="!schema.richText"
      :value="modelValue"
      :placeholder="schema.controlName || '请输入内容'"
      :style="fieldStyle"
      class="plain-textarea"
      @input="handleTextareaInput"
    />

    <div v-else class="rich-editor">
      <div class="toolbar">
        <el-button size="small" @click="format('bold')">B</el-button>
        <el-button size="small" @click="format('italic')">I</el-button>
        <el-button size="small" @click="format('underline')">U</el-button>
        <el-button size="small" @click="format('insertUnorderedList')">• 列表</el-button>
      </div>
      <div
        ref="editorRef"
        class="editor-content"
        :style="fieldStyle"
        contenteditable="true"
        :data-placeholder="schema.controlName || '请输入内容'"
        @input="handleRichInput"
        v-html="modelValue"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { MultiLineInputSchema } from './multiLineSchema'

const props = defineProps<{
  schema: MultiLineInputSchema
  modelValue: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const editorRef = ref<HTMLDivElement | null>(null)

const containerStyle = computed(() => ({
  width: `${props.schema.widthPx}px`
}))

const fieldStyle = computed(() => ({
  width: `${props.schema.widthPx}px`,
  minHeight: `${props.schema.heightPx}px`,
  fontSize: `${props.schema.fontSizePx}px`,
  lineHeight: '1.6',
  boxSizing: 'border-box' as const
}))

const handleTextareaInput = (event: Event) => {
  const target = event.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
}

const handleRichInput = () => {
  emit('update:modelValue', editorRef.value?.innerHTML || '')
}

const format = (cmd: string) => {
  editorRef.value?.focus()
  document.execCommand(cmd)
  handleRichInput()
}
</script>

<style scoped>
.plain-textarea {
  resize: vertical;
  padding: 8px 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  color: #303133;
}

.rich-editor {
  width: 100%;
}

.toolbar {
  margin-bottom: 6px;
  display: flex;
  gap: 6px;
}

.editor-content {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 8px 10px;
  background: #fff;
  overflow: auto;
}

.editor-content:empty:before {
  content: attr(data-placeholder);
  color: #a8abb2;
}
</style>
