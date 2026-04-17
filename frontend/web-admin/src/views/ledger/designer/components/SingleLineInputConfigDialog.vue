<template>
  <el-dialog
    v-model="dialogVisible"
    title="单行输入框"
    width="640px"
    align-center
    destroy-on-close
  >
    <el-form :model="localSchema" label-position="top" class="config-form">
      <el-row :gutter="12">
        <el-col :span="24">
          <el-form-item label="控件名称" required>
            <el-input v-model="localSchema.controlName" placeholder="例如：负责人" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="映射变量">
            <el-select v-model="localSchema.mappingMode" style="width: 100%">
              <el-option label="自动创建变量" value="auto" />
              <el-option label="手动输入变量" value="manual" />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col v-if="localSchema.mappingMode === 'manual'" :span="12">
          <el-form-item label="变量名">
            <el-input v-model="localSchema.mappingVariable" placeholder="例如：owner_name" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="对齐方式">
            <el-select v-model="localSchema.align" style="width: 100%">
              <el-option label="左对齐" value="left" />
              <el-option label="居中" value="center" />
              <el-option label="右对齐" value="right" />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="字体大小(PX)">
            <el-input-number v-model="localSchema.fontSizePx" :min="10" :max="30" style="width: 100%" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="最多字符数">
            <el-input-number v-model="localSchema.maxLength" :min="1" :max="500" style="width: 100%" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="输入框宽度(PX)">
            <el-input-number v-model="localSchema.widthPx" :min="60" :max="1000" style="width: 100%" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="输入框高度(PX)">
            <el-input-number v-model="localSchema.heightPx" :min="24" :max="300" style="width: 100%" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="数据类型">
            <el-select v-model="localSchema.dataType" style="width: 100%">
              <el-option label="文本" value="text" />
              <el-option label="数字" value="number" />
              <el-option label="邮箱" value="email" />
              <el-option label="电话" value="tel" />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="最小长度">
            <el-input-number v-model="localSchema.minLength" :min="0" :max="500" style="width: 100%" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="初始值">
            <el-input v-model="localSchema.defaultValue" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="隐藏">
            <el-checkbox v-model="localSchema.hidden">是否隐藏</el-checkbox>
          </el-form-item>
        </el-col>
      </el-row>

      <div class="preview-box">
        <div class="preview-title">渲染预览</div>
        <input
          :type="localSchema.dataType"
          :value="localSchema.defaultValue"
          :maxlength="localSchema.maxLength"
          :style="inputStyle"
          :placeholder="localSchema.controlName || '请输入内容'"
          disabled
        />
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

export interface InputSchema {
  controlName: string
  mappingMode: 'auto' | 'manual'
  mappingVariable: string
  align: 'left' | 'center' | 'right'
  fontSizePx: number
  maxLength: number
  widthPx: number
  heightPx: number
  dataType: 'text' | 'number' | 'email' | 'tel'
  minLength: number
  defaultValue: string
  hidden: boolean
}

const props = defineProps<{
  visible: boolean
  modelValue: InputSchema
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'update:modelValue', value: InputSchema): void
  (e: 'confirm', value: InputSchema): void
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (value: boolean) => emit('update:visible', value)
})

const localSchema = reactive<InputSchema>({
  controlName: '',
  mappingMode: 'auto',
  mappingVariable: '',
  align: 'left',
  fontSizePx: 16,
  maxLength: 50,
  widthPx: 180,
  heightPx: 34,
  dataType: 'text',
  minLength: 0,
  defaultValue: '',
  hidden: false
})

watch(
  () => props.modelValue,
  (value) => {
    Object.assign(localSchema, value)
  },
  { immediate: true, deep: true }
)

const inputStyle = computed(() => ({
  width: `${localSchema.widthPx}px`,
  height: `${localSchema.heightPx}px`,
  fontSize: `${localSchema.fontSizePx}px`,
  textAlign: localSchema.align,
  padding: '0 10px',
  border: '1px solid #dcdfe6',
  borderRadius: '4px',
  boxSizing: 'border-box' as const,
  backgroundColor: '#f5f7fa'
}))

const handleConfirm = () => {
  if (!localSchema.controlName.trim()) {
    ElMessage.warning('请先填写控件名称')
    return
  }

  if (localSchema.defaultValue.length < localSchema.minLength) {
    ElMessage.warning('初始值长度不能小于最小长度')
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

:deep(.config-form .el-form-item) {
  margin-bottom: 12px;
}
</style>
