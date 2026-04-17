<template>
  <div ref="anchorRef" class="dropdown-cell" @mouseenter="hovered = true" @mouseleave="hovered = false">
    <span class="value-text">{{ displayText }}</span>
    <span v-if="hovered || active" class="arrow" @click.stop="togglePopup">▼</span>

    <Teleport to="body">
      <div
        v-if="popupVisible"
        ref="popupRef"
        class="dropdown-popup"
        :style="popupStyle"
      >
        <div
          v-for="item in filteredOptions"
          :key="item.value"
          class="popup-option"
          @click="selectOption(item)"
        >
          {{ toChildLabel(item.label) }}
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import type { DropdownOption, DropdownSchema } from './dropdownSchema'

const props = defineProps<{
  schema: DropdownSchema
  modelValue: string
  active: boolean
  parentValue?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const hovered = ref(false)
const popupVisible = ref(false)
const anchorRef = ref<HTMLElement | null>(null)
const popupRef = ref<HTMLElement | null>(null)
const popupStyle = ref<Record<string, string>>({})

const toChildLabel = (rawLabel: string) => {
  const [child] = rawLabel.split('|')
  return child.trim()
}

const displayText = computed(() => props.modelValue || toChildLabel(defaultOption.value?.label || ''))

const defaultOption = computed(() => props.schema.options.find((item) => item.isDefault))

const filteredOptions = computed(() => {
  const parentKey = (props.parentValue || '').trim()

  // 级联筛选算法：label 使用 child|parent 约定；
  // 若配置了 linkChildName，则仅展示 parent 段与父级值一致的项。
  if (!props.schema.linkChildName.trim()) {
    return props.schema.options
  }

  return props.schema.options.filter((item) => {
    const parts = item.label.split('|').map((seg) => seg.trim())
    if (parts.length < 2) {
      return parentKey.length === 0
    }
    return parts[1] === parentKey
  })
})

const updatePopupPosition = () => {
  const anchor = anchorRef.value
  if (!anchor) {
    return
  }
  const rect = anchor.getBoundingClientRect()
  popupStyle.value = {
    position: 'fixed',
    left: `${rect.left}px`,
    top: `${rect.bottom + 2}px`,
    width: `${Math.max(rect.width, props.schema.width)}px`,
    zIndex: '3000'
  }
}

const togglePopup = async () => {
  popupVisible.value = !popupVisible.value
  if (popupVisible.value) {
    await nextTick()
    updatePopupPosition()
  }
}

const closePopup = () => {
  popupVisible.value = false
}

const onDocumentClick = (event: MouseEvent) => {
  const target = event.target as Node
  if (anchorRef.value?.contains(target) || popupRef.value?.contains(target)) {
    return
  }
  closePopup()
}

const selectOption = (item: DropdownOption) => {
  emit('update:modelValue', toChildLabel(item.label))
  closePopup()
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  window.addEventListener('resize', updatePopupPosition)
  window.addEventListener('scroll', updatePopupPosition, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  window.removeEventListener('resize', updatePopupPosition)
  window.removeEventListener('scroll', updatePopupPosition, true)
})
</script>

<style scoped>
.dropdown-cell {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 6px;
  box-sizing: border-box;
}

.value-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #303133;
}

.arrow {
  color: #9aa3b2;
  font-size: 12px;
  cursor: pointer;
  margin-left: 6px;
}

.dropdown-popup {
  border: 1px solid #d9e0ef;
  border-radius: 4px;
  background: #fff;
  box-shadow: 0 8px 20px rgba(31, 45, 61, 0.12);
  max-height: 220px;
  overflow: auto;
}

.popup-option {
  padding: 8px 10px;
  cursor: pointer;
  border-bottom: 1px solid #f1f4fa;
}

.popup-option:hover {
  background: #edf4ff;
  color: #2f74d8;
}
</style>
