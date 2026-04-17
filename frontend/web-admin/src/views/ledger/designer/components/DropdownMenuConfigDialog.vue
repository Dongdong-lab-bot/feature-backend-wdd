<template>
  <el-dialog
    v-model="dialogVisible"
    title="下拉菜单"
    width="720px"
    align-center
    destroy-on-close
  >
    <el-form :model="localSchema" label-position="top" class="config-form">
      <el-row :gutter="12">
        <el-col :span="24">
          <el-form-item label="控件名称" required>
            <el-input v-model="localSchema.controlName" placeholder="例如：是否合格" />
          </el-form-item>
        </el-col>

        <el-col :span="24">
          <el-form-item label="关联子菜单名称">
            <el-input v-model="localSchema.linkChildName" placeholder="填写父级字段名（可选）" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="控件宽度(PX)">
            <el-input-number v-model="localSchema.width" :min="120" :max="1200" style="width: 100%" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="控件高度(行)">
            <el-input-number v-model="localSchema.height" :min="1" :max="20" style="width: 100%" />
          </el-form-item>
        </el-col>

        <el-col :span="24">
          <el-form-item label="映射变量" required>
            <el-input v-model="localSchema.field" placeholder="例如：check_result" />
          </el-form-item>
        </el-col>

        <el-col :span="24">
          <el-form-item label="下拉菜单项">
            <div class="dropdown-options-layout">
              <div class="dropdown-options-left">
                <div class="option-input-row">
                  <el-input v-model="optionDraft.label" placeholder="选项名称，如 南京|江苏" />
                  <el-input v-model="optionDraft.value" placeholder="选项值，如 nanjing" />
                  <el-button @click="addOption">新增</el-button>
                  <el-button @click="updateOption">修改</el-button>
                  <el-button @click="removeOption">删除</el-button>
                </div>

                <div class="options-list-wrap">
                  <div
                    v-for="(item, index) in localSchema.options"
                    :key="`option-${index}`"
                    class="option-item"
                    :class="{ active: selectedIndex === index }"
                    @click="selectOption(index)"
                  >
                    <span>{{ item.label }}（{{ item.value }}）</span>
                    <el-tag v-if="item.isDefault" size="small" type="success">默认</el-tag>
                  </div>
                </div>
              </div>

              <div class="dropdown-options-right">
                <el-button @click="setDefaultOption">设为默认值</el-button>
                <el-button @click="moveOptionUp">上移</el-button>
                <el-button @click="moveOptionDown">下移</el-button>
              </div>
            </div>
          </el-form-item>
        </el-col>
      </el-row>

      <div class="tip-box">
        若选项标签包含 "|"（如 "南京|江苏"），表示该选项属于父级"江苏"。渲染时将按父级值进行筛选。
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
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { DEFAULT_DROPDOWN_SCHEMA, type DropdownSchema } from './dropdownSchema'

const props = defineProps<{
  visible: boolean
  modelValue: DropdownSchema
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'update:modelValue', value: DropdownSchema): void
  (e: 'confirm', value: DropdownSchema): void
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (value: boolean) => emit('update:visible', value)
})

const localSchema = reactive<DropdownSchema>({
  ...DEFAULT_DROPDOWN_SCHEMA,
  options: DEFAULT_DROPDOWN_SCHEMA.options.map((item) => ({ ...item }))
})

const selectedIndex = ref(-1)

const optionDraft = reactive({
  label: '',
  value: ''
})

watch(
  () => props.modelValue,
  (value) => {
    localSchema.controlName = value.controlName
    localSchema.linkChildName = value.linkChildName
    localSchema.width = value.width
    localSchema.height = value.height
    localSchema.field = value.field
    localSchema.options = value.options.map((item) => ({ ...item }))
    selectedIndex.value = -1
    optionDraft.label = ''
    optionDraft.value = ''
  },
  { immediate: true, deep: true }
)

const selectOption = (index: number) => {
  selectedIndex.value = index
  optionDraft.label = localSchema.options[index].label
  optionDraft.value = localSchema.options[index].value
}

const addOption = () => {
  const label = optionDraft.label.trim()
  const value = optionDraft.value.trim()
  if (!label || !value) {
    ElMessage.warning('请填写选项名称和选项值')
    return
  }

  localSchema.options.push({
    label,
    value,
    isDefault: false
  })

  optionDraft.label = ''
  optionDraft.value = ''
}

const updateOption = () => {
  if (selectedIndex.value < 0) {
    ElMessage.warning('请先选择需要修改的选项')
    return
  }

  const label = optionDraft.label.trim()
  const value = optionDraft.value.trim()
  if (!label || !value) {
    ElMessage.warning('请填写选项名称和选项值')
    return
  }

  const target = localSchema.options[selectedIndex.value]
  target.label = label
  target.value = value
}

const removeOption = () => {
  if (selectedIndex.value < 0) {
    ElMessage.warning('请先选择需要删除的选项')
    return
  }

  localSchema.options.splice(selectedIndex.value, 1)
  selectedIndex.value = -1
  optionDraft.label = ''
  optionDraft.value = ''
}

const setDefaultOption = () => {
  if (selectedIndex.value < 0) {
    ElMessage.warning('请先选择菜单项')
    return
  }

  localSchema.options.forEach((item, index) => {
    item.isDefault = index === selectedIndex.value
  })
}

const moveOptionUp = () => {
  const index = selectedIndex.value
  if (index <= 0) {
    return
  }
  const temp = localSchema.options[index - 1]
  localSchema.options[index - 1] = localSchema.options[index]
  localSchema.options[index] = temp
  selectedIndex.value = index - 1
}

const moveOptionDown = () => {
  const index = selectedIndex.value
  if (index < 0 || index >= localSchema.options.length - 1) {
    return
  }
  const temp = localSchema.options[index + 1]
  localSchema.options[index + 1] = localSchema.options[index]
  localSchema.options[index] = temp
  selectedIndex.value = index + 1
}

const handleConfirm = () => {
  if (!localSchema.controlName.trim()) {
    ElMessage.warning('请先填写控件名称')
    return
  }

  if (!localSchema.field.trim()) {
    ElMessage.warning('请先填写映射变量')
    return
  }

  if (!localSchema.options.length) {
    ElMessage.warning('请至少添加一个下拉项')
    return
  }

  if (!localSchema.options.some((item) => item.isDefault)) {
    localSchema.options[0].isDefault = true
  }

  const nextSchema: DropdownSchema = {
    controlName: localSchema.controlName,
    linkChildName: localSchema.linkChildName,
    width: localSchema.width,
    height: localSchema.height,
    field: localSchema.field,
    options: localSchema.options.map((item) => ({ ...item }))
  }

  emit('update:modelValue', nextSchema)
  emit('confirm', nextSchema)
  dialogVisible.value = false
}
</script>

<style scoped>
.dropdown-options-layout {
  display: grid;
  grid-template-columns: 1fr 130px;
  gap: 10px;
  width: 100%;
}

.option-input-row {
  display: grid;
  grid-template-columns: 1fr 1fr 72px 72px 72px;
  gap: 8px;
  margin-bottom: 10px;
}

.options-list-wrap {
  border: 1px solid #dfe4ef;
  background: #fff;
  min-height: 140px;
  max-height: 190px;
  overflow: auto;
}

.option-item {
  height: 34px;
  padding: 0 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #eef2f8;
  cursor: pointer;
}

.option-item.active {
  background: #edf4ff;
  color: #2f74d8;
}

.dropdown-options-right {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tip-box {
  margin-top: 8px;
  border: 1px dashed #f2b6b6;
  background: #fff5f5;
  color: #b54a4a;
  font-size: 12px;
  line-height: 1.6;
  padding: 10px 12px;
}

:deep(.config-form .el-form-item) {
  margin-bottom: 12px;
}
</style>
