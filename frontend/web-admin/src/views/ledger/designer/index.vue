<template>
  <div class="designer-page">
    <header class="designer-header">
      <div class="title-wrap">
        <span class="title-label">表单名称</span>
        <el-input v-model="formName" placeholder="请输入表单名称" class="name-input" />
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="handleSave">保存</el-button>
        <el-button @click="handlePreview">预览</el-button>
        <el-button @click="handleVersion">生成版本</el-button>
        <el-button @click="handleClose">关闭</el-button>
      </div>
    </header>

    <section class="designer-body">
      <aside class="toolbox">
        <div class="toolbox-title">标准控件</div>
        <ul class="tool-list">
          <li
            v-for="item in controls"
            :key="item"
            class="tool-item"
            @click="handleControlClick(item)"
          >
            {{ item }}
          </li>
        </ul>
      </aside>

      <main class="sheet-area">
        <div class="sheet-toolbar">
          <el-tooltip content="合并单元格" placement="top">
            <el-button circle class="icon-btn" @click="mergeSelectedCells">
              <span class="toolbar-icon">⊞</span>
            </el-button>
          </el-tooltip>
          <el-tooltip content="左对齐" placement="top">
            <el-button circle class="icon-btn" @click="applyTextAlign('left')">
              <span class="toolbar-icon">⫷</span>
            </el-button>
          </el-tooltip>
          <el-tooltip content="居中对齐" placement="top">
            <el-button circle class="icon-btn" @click="applyTextAlign('center')">
              <span class="toolbar-icon">≡</span>
            </el-button>
          </el-tooltip>
          <el-tooltip content="右对齐" placement="top">
            <el-button circle class="icon-btn" @click="applyTextAlign('right')">
              <span class="toolbar-icon">⫸</span>
            </el-button>
          </el-tooltip>
          <el-tooltip content="加粗" placement="top">
            <el-button circle class="icon-btn" @click="toggleBoldSelectedCells">
              <span class="toolbar-icon">B</span>
            </el-button>
          </el-tooltip>
          <span class="toolbar-divider"></span>
          <el-tooltip content="新增行" placement="top">
            <el-button circle class="icon-btn" @click="insertRowAtActive">
              <span class="toolbar-icon">＋R</span>
            </el-button>
          </el-tooltip>
          <el-tooltip content="删除行" placement="top">
            <el-button circle class="icon-btn" @click="deleteRowAtActive">
              <span class="toolbar-icon">－R</span>
            </el-button>
          </el-tooltip>
          <el-tooltip content="新增列" placement="top">
            <el-button circle class="icon-btn" @click="insertColumnAtActive">
              <span class="toolbar-icon">＋C</span>
            </el-button>
          </el-tooltip>
          <el-tooltip content="删除列" placement="top">
            <el-button circle class="icon-btn" @click="deleteColumnAtActive">
              <span class="toolbar-icon">－C</span>
            </el-button>
          </el-tooltip>
          <el-tooltip content="清空表格" placement="top">
            <el-button circle class="icon-btn" @click="clearSheet">
              <span class="toolbar-icon">⌫</span>
            </el-button>
          </el-tooltip>
          <span class="cell-indicator">当前单元格：{{ activeCellLabel }}</span>
        </div>

        <div class="sheet-wrap">
          <table class="sheet-table">
            <thead>
              <tr>
                <th class="corner"></th>
                <th v-for="col in colCount" :key="`head-${col}`">{{ toColName(col - 1) }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, rowIndex) in grid" :key="`row-${rowIndex}`">
                <th>{{ rowIndex + 1 }}</th>
                <template v-for="(_, colIndex) in row" :key="`cell-${rowIndex}-${colIndex}`">
                  <td
                    v-if="isCellVisible(rowIndex, colIndex)"
                    :rowspan="getCellSpan(rowIndex, colIndex).rowspan"
                    :colspan="getCellSpan(rowIndex, colIndex).colspan"
                    :class="{
                      active: rowIndex === activeRow && colIndex === activeCol,
                      selected: isCellSelected(rowIndex, colIndex)
                    }"
                    :style="getCellStyle(rowIndex, colIndex)"
                    @mousedown="startSelection(rowIndex, colIndex)"
                    @mouseenter="extendSelection(rowIndex, colIndex)"
                    @click="setActiveCell(rowIndex, colIndex)"
                  >
                    <DropdownCellRenderer
                      v-if="getCellType(rowIndex, colIndex) === 'dropdown'"
                      :schema="getDropdownSchema(rowIndex, colIndex)"
                      :model-value="grid[rowIndex][colIndex]"
                      :active="rowIndex === activeRow && colIndex === activeCol"
                      :parent-value="getDropdownParentValue(rowIndex, colIndex)"
                      @update:modelValue="setCellValue(rowIndex, colIndex, $event)"
                    />
                    <input
                      v-else
                      v-model="grid[rowIndex][colIndex]"
                      class="cell-input"
                      :style="getEditorStyle(rowIndex, colIndex)"
                      @focus="setActiveCell(rowIndex, colIndex)"
                    />
                  </td>
                </template>
              </tr>
            </tbody>
          </table>
        </div>
      </main>

      <aside class="preview-panel">
        <div class="preview-title">预览字段</div>
        <el-scrollbar>
          <div class="preview-item" v-for="(item, index) in previewFields" :key="`preview-${index}`">
            <span class="preview-index">{{ index + 1 }}.</span>
            <span class="preview-text">{{ item }}</span>
          </div>
        </el-scrollbar>

        <div class="runtime-preview">
          <div class="preview-title">多行输入渲染态</div>
          <div class="runtime-key">控件名称：{{ multiLineSchema.controlName || '未设置' }}</div>
          <div class="runtime-key">映射变量：{{ multiLineSchema.mappingVariable || '未设置' }}</div>
          <MultiLineFieldRenderer
            :schema="multiLineSchema"
            v-model="currentMultiLineValue"
          />
        </div>
      </aside>
    </section>

    <SingleLineInputConfigDialog
      v-model:visible="singleLineDialogVisible"
      v-model="inputSchema"
      @confirm="applySingleLineSchema"
    />

    <MultiLineInputConfigDialog
      v-model:visible="multiLineDialogVisible"
      v-model="multiLineSchema"
      @confirm="applyMultiLineSchema"
    />

    <DropdownMenuConfigDialog
      v-model:visible="dropdownDialogVisible"
      v-model="dropdownSchema"
      @confirm="applyDropdownSchema"
    />

    <el-dialog
      v-model="multiSelectDialogVisible"
      title="多选框"
      width="700px"
      align-center
      destroy-on-close
    >
      <el-form :model="multiSelectForm" label-position="top" class="config-form">
        <el-row :gutter="12">
          <el-col :span="24">
            <el-form-item label="控件名称" required>
              <el-input v-model="multiSelectForm.label" placeholder="例如：问题类型" />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="控件高度(行)">
              <el-input-number v-model="multiSelectForm.heightRows" :min="1" :max="20" style="width: 100%" />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="控件宽度(PX)">
              <el-input-number v-model="multiSelectForm.width" :min="120" :max="1200" style="width: 100%" />
            </el-form-item>
          </el-col>

          <el-col :span="24">
            <el-form-item label="映射变量">
              <el-select v-model="multiSelectForm.mappingMode" style="width: 100%">
                <el-option label="自动创建变量" value="auto" />
                <el-option label="手动输入变量" value="manual" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="24">
            <el-form-item label="多选框选项">
              <div class="dropdown-options-layout">
                <div class="dropdown-options-left">
                  <div class="option-input-row">
                    <el-input v-model="multiSelectOptionInput" placeholder="输入选项内容，如：环境卫生" />
                    <el-button @click="addMultiSelectOption">新增</el-button>
                    <el-button @click="updateMultiSelectOption">修改</el-button>
                    <el-button @click="removeMultiSelectOption">删除</el-button>
                  </div>

                  <div class="options-list-wrap">
                    <div
                      v-for="(item, index) in multiSelectForm.options"
                      :key="`multi-${index}`"
                      class="option-item"
                      :class="{ active: index === multiSelectSelectedIndex }"
                      @click="selectMultiSelectOption(index)"
                    >
                      <span>{{ item }}</span>
                      <el-tag v-if="multiSelectForm.defaultValues.includes(item)" size="small" type="success">默认</el-tag>
                    </div>
                  </div>
                </div>

                <div class="dropdown-options-right">
                  <el-button @click="moveMultiSelectOptionUp">上移</el-button>
                  <el-button @click="moveMultiSelectOptionDown">下移</el-button>
                </div>
              </div>
            </el-form-item>
          </el-col>

          <el-col :span="24">
            <el-form-item label="默认选中">
              <el-checkbox-group v-model="multiSelectForm.defaultValues">
                <el-checkbox v-for="item in multiSelectForm.options" :key="`default-${item}`" :label="item">{{ item }}</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="multiSelectDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmMultiSelectConfig">确认</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import SingleLineInputConfigDialog, { type InputSchema } from './components/SingleLineInputConfigDialog.vue'
import MultiLineInputConfigDialog from './components/MultiLineInputConfigDialog.vue'
import type { MultiLineInputSchema } from './components/multiLineSchema'
import MultiLineFieldRenderer from './components/MultiLineFieldRenderer.vue'
import DropdownMenuConfigDialog from './components/DropdownMenuConfigDialog.vue'
import DropdownCellRenderer from './components/DropdownCellRenderer.vue'
import { DEFAULT_DROPDOWN_SCHEMA, type DropdownSchema } from './components/dropdownSchema'

const route = useRoute()
const router = useRouter()

const formName = ref(String(route.query.name || '紫外线消毒记录表'))

const controls = [
  '单行输入框',
  '多行输入框',
  '下拉菜单',
  '多选框',
  '单选框',
  '列表控件',
  '宏控件',
  '日历控件',
  '计算控件',
  '部门人员控件',
  '签章控件',
  '数据选择控件',
  '表单数据控件',
  '进度条控件',
  '图片上传控件',
  '附件上传控件'
]

const singleLineDialogVisible = ref(false)
const multiLineDialogVisible = ref(false)
const dropdownDialogVisible = ref(false)
const multiSelectDialogVisible = ref(false)

const inputSchema = reactive<InputSchema>({
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

const multiLineSchema = reactive<MultiLineInputSchema>({
  controlName: '',
  mappingVariable: '',
  fontSizePx: 16,
  richText: false,
  widthPx: 260,
  heightPx: 120,
  defaultValue: ''
})

const formValueMap = reactive<Record<string, string>>({})
const multiLinePlacement = reactive({
  row: 0,
  col: 0,
  lineCount: 0
})

const currentMultiLineValue = computed<string>({
  get: () => {
    const key = multiLineSchema.mappingVariable.trim()
    if (!key) {
      return ''
    }
    return formValueMap[key] ?? ''
  },
  set: (value: string) => {
    const key = multiLineSchema.mappingVariable.trim()
    if (!key) {
      return
    }
    formValueMap[key] = value
  }
})

const dropdownSchema = reactive<DropdownSchema>({
  controlName: DEFAULT_DROPDOWN_SCHEMA.controlName,
  linkChildName: DEFAULT_DROPDOWN_SCHEMA.linkChildName,
  width: DEFAULT_DROPDOWN_SCHEMA.width,
  height: DEFAULT_DROPDOWN_SCHEMA.height,
  field: DEFAULT_DROPDOWN_SCHEMA.field,
  options: DEFAULT_DROPDOWN_SCHEMA.options.map((item) => ({ ...item }))
})

type CellControl = {
  type: 'dropdown'
  schema: DropdownSchema
}

type CellStyle = {
  textAlign?: 'left' | 'center' | 'right'
  fontWeight?: 'normal' | 'bold'
}

type MergeMeta = {
  row: number
  col: number
  rowspan: number
  colspan: number
}

const cellControlMap = reactive<Record<string, CellControl>>({})
const cellStyleMap = reactive<Record<string, CellStyle>>({})
const mergeMap = reactive<Record<string, MergeMeta>>({})

const multiSelectForm = reactive({
  label: '',
  heightRows: 1,
  width: 240,
  mappingMode: 'auto',
  options: ['选项A', '选项B'] as string[],
  defaultValues: [] as string[]
})

const multiSelectOptionInput = ref('')
const multiSelectSelectedIndex = ref(-1)

const rowCount = ref(20)
const colCount = ref(10)

const createGrid = (rows: number, cols: number) =>
  Array.from({ length: rows }, () => Array.from({ length: cols }, () => ''))

const grid = ref<string[][]>(createGrid(rowCount.value, colCount.value))

const activeRow = ref(0)
const activeCol = ref(0)
const isSelecting = ref(false)
const selectionStart = ref<{ row: number; col: number } | null>(null)
const selectionEnd = ref<{ row: number; col: number } | null>(null)

const toColName = (index: number): string => {
  let n = index
  let name = ''
  while (n >= 0) {
    name = String.fromCharCode((n % 26) + 65) + name
    n = Math.floor(n / 26) - 1
  }
  return name
}

const activeCellLabel = computed(() => `${toColName(activeCol.value)}${activeRow.value + 1}`)

const selectedRange = computed(() => {
  const start = selectionStart.value || { row: activeRow.value, col: activeCol.value }
  const end = selectionEnd.value || start
  return {
    minRow: Math.min(start.row, end.row),
    maxRow: Math.max(start.row, end.row),
    minCol: Math.min(start.col, end.col),
    maxCol: Math.max(start.col, end.col)
  }
})

const selectedCells = computed(() => {
  const cells: Array<{ row: number; col: number }> = []
  for (let row = selectedRange.value.minRow; row <= selectedRange.value.maxRow; row += 1) {
    for (let col = selectedRange.value.minCol; col <= selectedRange.value.maxCol; col += 1) {
      cells.push({ row, col })
    }
  }
  return cells
})

const previewFields = computed(() => {
  const firstRow = grid.value[0] || []
  return firstRow.filter((item) => item.trim().length > 0)
})

const setActiveCell = (row: number, col: number) => {
  activeRow.value = row
  activeCol.value = col
}

const buildCellKey = (row: number, col: number): string => `${row}:${col}`

const setCellValue = (row: number, col: number, value: string) => {
  grid.value[row][col] = value
}

const getCellStyle = (row: number, col: number) => {
  const style = cellStyleMap[buildCellKey(row, col)]
  return {
    textAlign: style?.textAlign || 'left',
    fontWeight: style?.fontWeight || 'normal'
  }
}

const getEditorStyle = (row: number, col: number) => {
  const style = cellStyleMap[buildCellKey(row, col)]
  return {
    textAlign: style?.textAlign || 'left',
    fontWeight: style?.fontWeight || 'normal'
  }
}

const getCellSpan = (row: number, col: number): { rowspan: number; colspan: number } => {
  const meta = mergeMap[buildCellKey(row, col)]
  if (!meta) {
    return { rowspan: 1, colspan: 1 }
  }
  return { rowspan: meta.rowspan, colspan: meta.colspan }
}

const isCellVisible = (row: number, col: number): boolean => {
  for (const key of Object.keys(mergeMap)) {
    const merge = mergeMap[key]
    const inRange =
      row >= merge.row &&
      row < merge.row + merge.rowspan &&
      col >= merge.col &&
      col < merge.col + merge.colspan

    if (inRange) {
      return merge.row === row && merge.col === col
    }
  }
  return true
}

const getCellType = (row: number, col: number): 'text' | 'dropdown' => {
  const cell = cellControlMap[buildCellKey(row, col)]
  return cell?.type || 'text'
}

const getDropdownSchema = (row: number, col: number): DropdownSchema => {
  const cell = cellControlMap[buildCellKey(row, col)]
  return cell?.schema || dropdownSchema
}

const getDropdownParentValue = (row: number, col: number): string => {
  const schema = getDropdownSchema(row, col)
  const parentField = schema.linkChildName.trim()
  if (!parentField) {
    return ''
  }

  // 级联查找：优先同一行，其次全表；匹配父字段名(field)。
  const keys = Object.keys(cellControlMap)
  const sameRow = keys
    .map((key) => ({ key, ...parseCellKey(key) }))
    .filter((item) => item.row === row)

  for (const item of sameRow) {
    const control = cellControlMap[item.key]
    if (control.type === 'dropdown' && control.schema.field === parentField) {
      return grid.value[item.row][item.col] || ''
    }
  }

  for (const key of keys) {
    const parsed = parseCellKey(key)
    const control = cellControlMap[key]
    if (control.type === 'dropdown' && control.schema.field === parentField) {
      return grid.value[parsed.row][parsed.col] || ''
    }
  }

  return ''
}

const parseCellKey = (key: string): { row: number; col: number } => {
  const [row, col] = key.split(':')
  return { row: Number(row), col: Number(col) }
}

const startSelection = (row: number, col: number) => {
  isSelecting.value = true
  selectionStart.value = { row, col }
  selectionEnd.value = { row, col }
  setActiveCell(row, col)
}

const extendSelection = (row: number, col: number) => {
  if (!isSelecting.value || !selectionStart.value) {
    return
  }
  selectionEnd.value = { row, col }
}

const stopSelection = () => {
  isSelecting.value = false
}

const isCellSelected = (row: number, col: number): boolean => {
  if (!selectionStart.value || !selectionEnd.value) {
    return false
  }
  const minRow = Math.min(selectionStart.value.row, selectionEnd.value.row)
  const maxRow = Math.max(selectionStart.value.row, selectionEnd.value.row)
  const minCol = Math.min(selectionStart.value.col, selectionEnd.value.col)
  const maxCol = Math.max(selectionStart.value.col, selectionEnd.value.col)
  return row >= minRow && row <= maxRow && col >= minCol && col <= maxCol
}

const remapRecord = <T,>(
  source: Record<string, T>,
  mapper: (row: number, col: number, value: T) => { row: number; col: number } | null
) => {
  const next: Record<string, T> = {}
  Object.keys(source).forEach((key) => {
    const { row, col } = parseCellKey(key)
    const mapped = mapper(row, col, source[key])
    if (!mapped) {
      return
    }
    next[buildCellKey(mapped.row, mapped.col)] = source[key]
  })
  Object.keys(source).forEach((key) => {
    delete source[key]
  })
  Object.assign(source, next)
}

const remapMerges = (
  mapper: (merge: MergeMeta) => MergeMeta | null
) => {
  const next: Record<string, MergeMeta> = {}
  Object.keys(mergeMap).forEach((key) => {
    const mapped = mapper(mergeMap[key])
    if (!mapped) {
      return
    }
    next[buildCellKey(mapped.row, mapped.col)] = mapped
  })
  Object.keys(mergeMap).forEach((key) => {
    delete mergeMap[key]
  })
  Object.assign(mergeMap, next)
}

const insertRowAtActive = () => {
  const index = Math.max(0, Math.min(activeRow.value, grid.value.length))
  grid.value.splice(index, 0, Array.from({ length: colCount.value }, () => ''))
  rowCount.value += 1

  remapRecord(cellStyleMap, (row, col) => ({ row: row >= index ? row + 1 : row, col }))
  remapRecord(cellControlMap, (row, col) => ({ row: row >= index ? row + 1 : row, col }))
  remapMerges((merge) => {
    if (index > merge.row && index < merge.row + merge.rowspan) {
      return { ...merge, rowspan: merge.rowspan + 1 }
    }
    return {
      ...merge,
      row: merge.row >= index ? merge.row + 1 : merge.row
    }
  })
}

const deleteRowAtActive = () => {
  if (grid.value.length <= 1) {
    ElMessage.warning('至少保留一行')
    return
  }
  const index = Math.max(0, Math.min(activeRow.value, grid.value.length - 1))
  grid.value.splice(index, 1)
  rowCount.value -= 1
  activeRow.value = Math.max(0, activeRow.value - (activeRow.value >= index ? 1 : 0))

  remapRecord(cellStyleMap, (row, col) => {
    if (row === index) return null
    return { row: row > index ? row - 1 : row, col }
  })
  remapRecord(cellControlMap, (row, col) => {
    if (row === index) return null
    return { row: row > index ? row - 1 : row, col }
  })
  remapMerges((merge) => {
    const covered = index >= merge.row && index < merge.row + merge.rowspan
    if (!covered) {
      return {
        ...merge,
        row: merge.row > index ? merge.row - 1 : merge.row
      }
    }
    if (merge.rowspan <= 1) {
      return null
    }
    const nextRow = merge.row > index ? merge.row - 1 : merge.row
    return { ...merge, row: nextRow, rowspan: merge.rowspan - 1 }
  })
}

const insertColumnAtActive = () => {
  const index = Math.max(0, Math.min(activeCol.value, colCount.value))
  grid.value.forEach((row) => row.splice(index, 0, ''))
  colCount.value += 1

  remapRecord(cellStyleMap, (row, col) => ({ row, col: col >= index ? col + 1 : col }))
  remapRecord(cellControlMap, (row, col) => ({ row, col: col >= index ? col + 1 : col }))
  remapMerges((merge) => {
    if (index > merge.col && index < merge.col + merge.colspan) {
      return { ...merge, colspan: merge.colspan + 1 }
    }
    return {
      ...merge,
      col: merge.col >= index ? merge.col + 1 : merge.col
    }
  })
}

const deleteColumnAtActive = () => {
  if (colCount.value <= 1) {
    ElMessage.warning('至少保留一列')
    return
  }
  const index = Math.max(0, Math.min(activeCol.value, colCount.value - 1))
  grid.value.forEach((row) => row.splice(index, 1))
  colCount.value -= 1
  activeCol.value = Math.max(0, activeCol.value - (activeCol.value >= index ? 1 : 0))

  remapRecord(cellStyleMap, (row, col) => {
    if (col === index) return null
    return { row, col: col > index ? col - 1 : col }
  })
  remapRecord(cellControlMap, (row, col) => {
    if (col === index) return null
    return { row, col: col > index ? col - 1 : col }
  })
  remapMerges((merge) => {
    const covered = index >= merge.col && index < merge.col + merge.colspan
    if (!covered) {
      return {
        ...merge,
        col: merge.col > index ? merge.col - 1 : merge.col
      }
    }
    if (merge.colspan <= 1) {
      return null
    }
    const nextCol = merge.col > index ? merge.col - 1 : merge.col
    return { ...merge, col: nextCol, colspan: merge.colspan - 1 }
  })
}

const applyStyleToSelection = (updater: (origin: CellStyle) => CellStyle) => {
  selectedCells.value.forEach(({ row, col }) => {
    if (!isCellVisible(row, col)) {
      return
    }
    const key = buildCellKey(row, col)
    const next = updater({ ...(cellStyleMap[key] || {}) })
    cellStyleMap[key] = next
  })
}

const applyTextAlign = (align: 'left' | 'center' | 'right') => {
  applyStyleToSelection((origin) => ({
    ...origin,
    textAlign: align
  }))
}

const toggleBoldSelectedCells = () => {
  const hasNormal = selectedCells.value.some(({ row, col }) => {
    const style = cellStyleMap[buildCellKey(row, col)]
    return style?.fontWeight !== 'bold'
  })

  applyStyleToSelection((origin) => ({
    ...origin,
    fontWeight: hasNormal ? 'bold' : 'normal'
  }))
}

const mergeSelectedCells = () => {
  const { minRow, maxRow, minCol, maxCol } = selectedRange.value
  if (minRow === maxRow && minCol === maxCol) {
    ElMessage.warning('请至少选择 2 个单元格进行合并')
    return
  }

  const rowspan = maxRow - minRow + 1
  const colspan = maxCol - minCol + 1

  // 清理与当前区域相交的旧合并，避免覆盖冲突。
  Object.keys(mergeMap).forEach((key) => {
    const merge = mergeMap[key]
    const intersects = !(
      merge.row + merge.rowspan - 1 < minRow ||
      merge.row > maxRow ||
      merge.col + merge.colspan - 1 < minCol ||
      merge.col > maxCol
    )
    if (intersects) {
      delete mergeMap[key]
    }
  })

  mergeMap[buildCellKey(minRow, minCol)] = {
    row: minRow,
    col: minCol,
    rowspan,
    colspan
  }

  setActiveCell(minRow, minCol)
}

const clearSheet = async () => {
  await ElMessageBox.confirm('确认清空当前表格内容？', '提示', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: 'warning'
  })
  grid.value = createGrid(rowCount.value, colCount.value)
  Object.keys(cellStyleMap).forEach((key) => delete cellStyleMap[key])
  Object.keys(mergeMap).forEach((key) => delete mergeMap[key])
}

const handleSave = () => {
  ElMessage.success(`已保存：${formName.value}`)
}

const handlePreview = () => {
  ElMessage.info('预览功能下一步接入真实模板渲染')
}

const handleVersion = () => {
  ElMessage.success('版本已生成（演示）')
}

const handleClose = () => {
  router.push('/ledger/templates')
}

const handleControlClick = (control: string) => {
  if (control === '单行输入框') {
    singleLineDialogVisible.value = true
    return
  }

  if (control === '多行输入框') {
    multiLineDialogVisible.value = true
    return
  }

  if (control === '下拉菜单') {
    dropdownDialogVisible.value = true
    return
  }

  if (control === '多选框') {
    multiSelectDialogVisible.value = true
    multiSelectSelectedIndex.value = -1
    multiSelectOptionInput.value = ''
    return
  }

  ElMessage.info(`${control} 正在开发中，下一步继续接入`)
}

const applySingleLineSchema = (schema: {
  controlName: string
  defaultValue: string
}) => {
  grid.value[0][activeCol.value] = schema.controlName.trim()

  if (schema.defaultValue.trim()) {
    grid.value[1][activeCol.value] = schema.defaultValue.trim()
  }

  ElMessage.success(`已添加控件：${schema.controlName}`)
}

const applyMultiLineSchema = (schema: MultiLineInputSchema) => {
  Object.assign(multiLineSchema, schema)
  multiLinePlacement.row = activeRow.value
  multiLinePlacement.col = activeCol.value

  const key = schema.mappingVariable.trim()
  if (key) {
    formValueMap[key] = schema.defaultValue || formValueMap[key] || ''
  }

  // On confirm, always flush multiline content to grid immediately.
  fillMultiLineCells(schema.defaultValue || '')

  ElMessage.success(`已添加控件：${schema.controlName}`)
}

const ensureRowCapacity = (targetRowIndex: number) => {
  while (grid.value.length <= targetRowIndex) {
    grid.value.push(Array.from({ length: colCount.value }, () => ''))
    rowCount.value += 1
  }
}

const clearMultiLineCells = () => {
  if (multiLinePlacement.lineCount <= 0) {
    return
  }
  for (let i = 0; i < multiLinePlacement.lineCount; i += 1) {
    const rowIndex = multiLinePlacement.row + i
    if (rowIndex < grid.value.length && multiLinePlacement.col < grid.value[rowIndex].length) {
      grid.value[rowIndex][multiLinePlacement.col] = ''
    }
  }
  multiLinePlacement.lineCount = 0
}

const fillMultiLineCells = (value: string) => {
  clearMultiLineCells()

  if (!value) {
    return
  }

  const lines = value.split(/\r?\n/)
  lines.forEach((line, index) => {
    const rowIndex = multiLinePlacement.row + index
    ensureRowCapacity(rowIndex)
    grid.value[rowIndex][multiLinePlacement.col] = line
  })

  multiLinePlacement.lineCount = lines.length
}

watch(
  () => currentMultiLineValue.value,
  (value) => {
    fillMultiLineCells(value)
  },
  { immediate: true }
)

const applyDropdownSchema = (schema: DropdownSchema) => {
  const key = buildCellKey(activeRow.value, activeCol.value)
  cellControlMap[key] = {
    type: 'dropdown',
    schema: {
      ...schema,
      options: schema.options.map((item) => ({ ...item }))
    }
  }

  const defaultOption = schema.options.find((item) => item.isDefault) || schema.options[0]
  grid.value[activeRow.value][activeCol.value] = defaultOption ? defaultOption.label.split('|')[0].trim() : ''

  ElMessage.success(`已添加控件：${schema.controlName}`)
}

const selectMultiSelectOption = (index: number) => {
  multiSelectSelectedIndex.value = index
  multiSelectOptionInput.value = multiSelectForm.options[index] || ''
}

const addMultiSelectOption = () => {
  const value = multiSelectOptionInput.value.trim()
  if (!value) {
    ElMessage.warning('请输入选项内容')
    return
  }
  multiSelectForm.options.push(value)
  multiSelectOptionInput.value = ''
}

const updateMultiSelectOption = () => {
  const value = multiSelectOptionInput.value.trim()
  if (multiSelectSelectedIndex.value < 0) {
    ElMessage.warning('请先选择需要修改的选项')
    return
  }
  if (!value) {
    ElMessage.warning('请输入选项内容')
    return
  }
  const old = multiSelectForm.options[multiSelectSelectedIndex.value]
  multiSelectForm.options[multiSelectSelectedIndex.value] = value
  multiSelectForm.defaultValues = multiSelectForm.defaultValues.map((item) => (item === old ? value : item))
}

const removeMultiSelectOption = () => {
  if (multiSelectSelectedIndex.value < 0) {
    ElMessage.warning('请先选择需要删除的选项')
    return
  }
  const removed = multiSelectForm.options.splice(multiSelectSelectedIndex.value, 1)[0]
  multiSelectForm.defaultValues = multiSelectForm.defaultValues.filter((item) => item !== removed)
  multiSelectSelectedIndex.value = -1
  multiSelectOptionInput.value = ''
}

const moveMultiSelectOptionUp = () => {
  const index = multiSelectSelectedIndex.value
  if (index <= 0) {
    return
  }
  const temp = multiSelectForm.options[index - 1]
  multiSelectForm.options[index - 1] = multiSelectForm.options[index]
  multiSelectForm.options[index] = temp
  multiSelectSelectedIndex.value = index - 1
}

const moveMultiSelectOptionDown = () => {
  const index = multiSelectSelectedIndex.value
  if (index < 0 || index >= multiSelectForm.options.length - 1) {
    return
  }
  const temp = multiSelectForm.options[index + 1]
  multiSelectForm.options[index + 1] = multiSelectForm.options[index]
  multiSelectForm.options[index] = temp
  multiSelectSelectedIndex.value = index + 1
}

const confirmMultiSelectConfig = () => {
  if (!multiSelectForm.label.trim()) {
    ElMessage.warning('请先填写控件名称')
    return
  }
  if (!multiSelectForm.options.length) {
    ElMessage.warning('请至少添加一个选项')
    return
  }

  grid.value[0][activeCol.value] = multiSelectForm.label.trim()
  grid.value[1][activeCol.value] = multiSelectForm.defaultValues.join('、')

  multiSelectDialogVisible.value = false
  ElMessage.success(`已添加控件：${multiSelectForm.label}`)
}

onMounted(() => {
  window.addEventListener('mouseup', stopSelection)
})

onBeforeUnmount(() => {
  window.removeEventListener('mouseup', stopSelection)
})
</script>

<style scoped>
.designer-page {
  min-height: calc(100vh - 84px);
  background: #f2f4f8;
}

.designer-header {
  height: 58px;
  padding: 0 16px;
  border-bottom: 1px solid #d8deea;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #ffffff;
}

.title-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-label {
  font-size: 14px;
  color: #303133;
  font-weight: 600;
}

.name-input {
  width: 260px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.designer-body {
  display: grid;
  grid-template-columns: 180px 1fr 260px;
  min-height: calc(100vh - 142px);
}

.toolbox {
  background: #f8f9fc;
  border-right: 1px solid #d8deea;
  padding: 12px;
}

.toolbox-title,
.preview-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
}

.tool-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.tool-item {
  font-size: 13px;
  color: #606266;
  padding: 10px 10px;
  margin-bottom: 8px;
  border: 1px solid #e2e6f0;
  border-radius: 6px;
  line-height: 1.4;
  cursor: pointer;
  background: #ffffff;
  transition: all 0.2s ease;
}

.tool-item:hover {
  color: #2f74d8;
  border-color: #b9cdf3;
  box-shadow: 0 2px 8px rgba(47, 116, 216, 0.12);
}

.sheet-area {
  padding: 10px;
  overflow: auto;
}

.sheet-toolbar {
  height: 40px;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.icon-btn {
  width: 28px;
  height: 28px;
  padding: 0;
}

.toolbar-icon {
  font-size: 11px;
  font-weight: 600;
  color: #4b5568;
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  background: #d8deea;
  margin: 0 4px;
}

.cell-indicator {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}

.sheet-wrap {
  border: 1px solid #ccd4e0;
  background: #fff;
  overflow: auto;
}

.sheet-table {
  border-collapse: collapse;
  min-width: 920px;
  user-select: none;
}

.sheet-table th,
.sheet-table td {
  border: 1px solid #d9dde8;
  width: 110px;
  height: 34px;
  padding: 0;
}

.sheet-table th {
  background: #f6f8fc;
  font-size: 12px;
  color: #606266;
  font-weight: 600;
  text-align: center;
}

.corner {
  width: 44px;
}

.sheet-table tbody th {
  width: 44px;
}

.cell-input {
  width: 100%;
  height: 100%;
  border: none;
  outline: none;
  padding: 0 8px;
  font-size: 12px;
  background: transparent;
}

td.active {
  box-shadow: inset 0 0 0 2px #3a7bd5;
}

td.selected {
  background: #eaf2ff;
}

.preview-panel {
  border-left: 1px solid #d8deea;
  background: #f8f9fc;
  padding: 12px;
}

.preview-item {
  padding: 8px 0;
  border-bottom: 1px dashed #d9dde8;
  font-size: 13px;
}

.preview-index {
  color: #3a7bd5;
  margin-right: 6px;
}

.preview-text {
  color: #303133;
}

.runtime-preview {
  margin-top: 12px;
  border-top: 1px dashed #d7dceb;
  padding-top: 10px;
}

.runtime-key {
  font-size: 12px;
  color: #7b869c;
  margin-bottom: 8px;
}

.dropdown-tip {
  border: 1px dashed #f2b6b6;
  background: #fff5f5;
  color: #b54a4a;
  font-size: 12px;
  line-height: 1.6;
  padding: 10px 12px;
}

.dropdown-options-layout {
  display: grid;
  grid-template-columns: 1fr 130px;
  gap: 10px;
  width: 100%;
}

.dropdown-options-left {
  min-width: 0;
}

.option-input-row {
  display: grid;
  grid-template-columns: 1fr 72px 72px 72px;
  gap: 8px;
  margin-bottom: 10px;
}

.options-list-wrap {
  border: 1px solid #dfe4ef;
  background: #fff;
  min-height: 140px;
  max-height: 180px;
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

:deep(.config-form .el-form-item) {
  margin-bottom: 12px;
}

@media (max-width: 1200px) {
  .designer-body {
    grid-template-columns: 160px 1fr;
  }

  .preview-panel {
    display: none;
  }
}
</style>