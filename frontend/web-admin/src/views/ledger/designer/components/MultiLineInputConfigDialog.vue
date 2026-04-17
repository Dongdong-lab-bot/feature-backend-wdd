<template>
  <el-dialog
    v-model="dialogVisible"
    title="多行输入框"
    width="660px"
    align-center
    destroy-on-close
  >
    <el-form :model="localSchema" label-position="top" class="config-form">
      <el-row :gutter="12">
        <el-col :span="24">
          <el-form-item label="控件名称" required>
            <el-input v-model="localSchema.controlName" placeholder="例如：详细说明" />
          </el-form-item>
        </el-col>

        <el-col :span="24">
          <el-form-item label="映射变量" required>
            <el-input v-model="localSchema.mappingVariable" placeholder="例如：description" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="字体大小(PX)">
            <el-input-number v-model="localSchema.fontSizePx" :min="10" :max="40" style="width: 100%" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="富文本形式">
            <el-checkbox v-model="localSchema.richText">启用富文本</el-checkbox>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="控件宽度(PX)">
            <el-input-number v-model="localSchema.widthPx" :min="120" :max="1200" style="width: 100%" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="控件高度(PX)">
            <el-input-number v-model="localSchema.heightPx" :min="60" :max="1000" style="width: 100%" />
          </el-form-item>
        </el-col>

        <el-col :span="24">
          <el-form-item label="默认值">
            <el-input
              v-model="localSchema.defaultValue"
              type="textarea"
              :rows="4"
              placeholder="请输入初始内容"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <div class="preview-box">
        <div class="preview-title">预览输出</div>
        <textarea
          v-if="!localSchema.richText"
          :style="previewStyle"
          :value="localSchema.defaultValue"
          disabled
        ></textarea>
        <div v-else class="rich-preview" :style="previewStyle" v-html="localSchema.defaultValue || '<p>富文本预览区域</p>'"></div>
      </div>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirm">确认</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { type MultiLineInputSchema } from './multiLineSchema'

const props = defineProps<{
  visible: boolean
  modelValue: MultiLineInputSchema
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'update:modelValue', value: MultiLineInputSchema): void
  (e: 'confirm', value: MultiLineInputSchema): void
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (value: boolean) => emit('update:visible', value)
})

const localSchema = reactive<MultiLineInputSchema>({
  controlName: '',
  mappingVariable: '',
  fontSizePx: 16,
  richText: false,
  widthPx: 260,
  heightPx: 120,
  defaultValue: ''
})

watch(
  () => props.modelValue,
  (value) => {
    Object.assign(localSchema, value)
  },
  { immediate: true, deep: true }
)

const previewStyle = computed(() => ({
  width: `${localSchema.widthPx}px`,
  minHeight: `${localSchema.heightPx}px`,
  fontSize: `${localSchema.fontSizePx}px`,
  lineHeight: '1.6',
  border: '1px solid #dcdfe6',
  borderRadius: '4px',
  padding: '8px 10px',
  boxSizing: 'border-box' as const,
  backgroundColor: '#f5f7fa'
}))

const handleConfirm = () => {
  if (!localSchema.controlName.trim()) {
    ElMessage.warning('请先填写控件名称')
    return
  }

  if (!localSchema.mappingVariable.trim()) {
    ElMessage.warning('请先填写映射变量')
    return
  }

  const nextSchema = { ...localSchema }
  emit('update:modelValue', nextSchema)
  emit('confirm', nextSchema)
  dialogVisible.value = false
}
</script>

<style scoped>
.preview-box {
  margin-top: 8px;
  padding: 10px 12px;
  border: 1px dashed #d9dfea;
  border-radius: 6px;
  background: #fbfcff;
}

.preview-title {
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
}

.preview-box textarea {
  resize: vertical;
}

.rich-preview {
  overflow: auto;
  color: #303133;
}

:deep(.config-form .el-form-item) {
  margin-bottom: 12px;
}
</style>
