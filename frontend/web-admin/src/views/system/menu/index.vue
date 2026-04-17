<template>
  <div class="menu-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <span class="title">菜单管理</span>
      <el-button type="primary" @click="handleAdd()">新增菜单</el-button>
    </div>

    <!-- 菜单表格 -->
    <el-table
      :data="filteredMenuData"
      v-loading="loading"
      style="width: 100%"
      row-key="id"
    >
      <el-table-column width="50" align="center">
        <template #default="scope">
          <div 
            v-if="scope.row.level === 0"
            class="expand-icon"
            :class="{ 'disabled': !scope.row.hasChildren }"
            @click="scope.row.hasChildren && toggleExpand(scope.row)"
          >
            {{ scope.row.expanded ? '-' : '+' }}
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="菜单名称" min-width="150">
        <template #default="scope">
          <span :style="{ paddingLeft: (scope.row.level || 0) * 20 + 'px' }">
            {{ scope.row.name }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="component" label="组件" min-width="100" />
      <el-table-column prop="path" label="路径" min-width="200" align="center">
        <template #default="scope">
          /{{ scope.row.path }}
        </template>
      </el-table-column>
      <el-table-column prop="sort" label="排序" min-width="100" align="center" />
      <el-table-column label="操作" min-width="150" align="center" fixed="right">
        <template #default="scope">
          <el-button link type="primary" @click="handleEdit(scope.row)">编辑</el-button>
          <el-button 
            v-if="scope.row.level === 0"
            link 
            type="primary" 
            @click="handleAdd(scope.row)"
          >
            添加子菜单
          </el-button>
          <el-button link type="danger" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-if="total > pageSize"
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next, total"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
      align-center
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px" hide-required-asterisk>
        <el-form-item label="菜单名称:" prop="name">
          <el-input v-model="formData.name" placeholder="请输入菜单名称" />
        </el-form-item>
        <el-form-item label="菜单路径:" prop="path">
          <el-input v-model="formData.path" placeholder="请输入菜单路径" />
        </el-form-item>
        <el-form-item label="前端组件:" prop="component">
          <el-input v-model="formData.component" placeholder="请输入前端组件路径" />
        </el-form-item>
        <el-form-item label="排序:" prop="sort">
          <el-input-number v-model="formData.sort" :min="0" :max="9999" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { getMenuList, createMenu, updateMenu, deleteMenu } from '@/api/menu'
import type { MenuItem } from '@/api/menu'

// 菜单接口定义
interface Menu extends MenuItem {
  expanded?: boolean
  level?: number
  hasChildren?: boolean
}

// 加载状态
const loading = ref(false)
const submitLoading = ref(false)

// 菜单数据
const menuData = ref<Menu[]>([])

// 分页
const currentPage = ref(1)
const pageSize = ref(8)
const total = ref(0)

// 展开状态Map
const expandedKeys = ref<Set<number>>(new Set())

// 扁平化并过滤菜单数据
const filteredMenuData = computed(() => {
  const flattenMenu = (menus: Menu[], level = 0): Menu[] => {
    const result: Menu[] = []
    menus.forEach(menu => {
      // 创建菜单副本，移除children避免Element Plus自动识别树形结构
      const { children, ...menuWithoutChildren } = menu
      const menuWithLevel = { 
        ...menuWithoutChildren, 
        level, 
        expanded: expandedKeys.value.has(menu.id),
        hasChildren: !!(children && children.length > 0)
      }
      result.push(menuWithLevel)
      if (children && menuWithLevel.expanded) {
        result.push(...flattenMenu(children, level + 1))
      }
    })
    return result
  }
  const start = (currentPage.value - 1) * pageSize.value
  const pagedRoots = menuData.value.slice(start, start + pageSize.value)
  return flattenMenu(pagedRoots)
})

// 切换展开状态
const toggleExpand = (row: Menu) => {
  if (expandedKeys.value.has(row.id)) {
    expandedKeys.value.delete(row.id)
  } else {
    expandedKeys.value.add(row.id)
  }
}

// 对话框控制
const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const currentParentRow = ref<Menu | null>(null)

// 对话框标题
const dialogTitle = computed(() => {
  if (dialogType.value === 'add') {
    return currentParentRow.value ? '新增子菜单' : '新增菜单'
  }
  return '编辑菜单'
})

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const formData = reactive<Partial<Menu>>({ parent_id: undefined, name: '', path: '', component: '', sort: 0, hidden: false })

// 表单验证规则
const rules: FormRules = {
  name: [{ required: true, message: '请输入菜单名称', trigger: 'blur' }],
  path: [{ required: true, message: '请输入路由路径', trigger: 'blur' }],
  component: [{ required: true, message: '请输入组件路径', trigger: 'blur' }],
  sort: [{ required: true, message: '请输入排序', trigger: 'blur' }]
}

// 加载菜单数据
const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getMenuList()
    menuData.value = res.data?.records || []
    total.value = menuData.value.length
    currentPage.value = 1
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

// 分页处理（客户端分页，切页无需重新请求）
const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
}

// 新增菜单
const handleAdd = (row?: Menu) => {
  dialogType.value = 'add'
  currentParentRow.value = row || null
  formData.parent_id = row ? (row.id as number) : undefined
  dialogVisible.value = true
}

// 编辑菜单
const handleEdit = (row: Menu) => {
  dialogType.value = 'edit'
  currentParentRow.value = null
  Object.assign(formData, { ...row })
  dialogVisible.value = true
}

// 删除菜单
const handleDelete = (row: Menu) => {
  ElMessageBox.confirm(
    `确定要删除菜单"${row.name}"吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteMenu(row.id as number)
      ElMessage.success('删除成功')
      loadData()
    } catch {
      ElMessage.error('删除失败')
    }
  }).catch(() => {
    // 用户取消
  })
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        const payload = {
          parent_id: formData.parent_id ?? undefined,
          name: formData.name!,
          path: formData.path || '',
          component: formData.component || '',
          sort: formData.sort ?? 0,
          hidden: formData.hidden ?? false,
        }
        if (dialogType.value === 'add') {
          await createMenu(payload)
        } else {
          await updateMenu(formData.id as number, payload)
        }
        ElMessage.success(dialogType.value === 'add' ? '新增成功' : '更新成功')
        dialogVisible.value = false
        loadData()
      } catch {
        ElMessage.error('操作失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(formData, { parent_id: undefined, name: '', path: '', component: '', sort: 0, hidden: false })
  currentParentRow.value = null
}

// 初始化
onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.menu-container {
  padding: 16px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .title {
      font-size: 16px;
      font-weight: 500;
      color: #303133;
    }
  }

  :deep(.el-table) {
    .el-table__row {
      height: 60px;
      
      .cell {
        padding: 12px 0;
      }
    }

    // 强制隐藏Element Plus默认的树形展开图标
    .el-table__expand-icon {
      display: none !important;
    }
  }

  .expand-icon {
    width: 18px;
    height: 18px;
    border: 1px solid #dcdfe6;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    user-select: none;
    font-size: 12px;
    font-weight: bold;
    color: #606266;
    transition: all 0.2s;
    border-radius: 2px;
    background: #fff;

    &:hover {
      border-color: #409eff;
      color: #409eff;
      background: #ecf5ff;
    }

    &.disabled {
      cursor: not-allowed;
      color: #c0c4cc;
      border-color: #e4e7ed;
      background: #f5f7fa;

      &:hover {
        border-color: #e4e7ed;
        color: #c0c4cc;
        background: #f5f7fa;
      }
    }
  }

  .pagination-wrapper {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }

  :deep(.el-dialog) {
    .el-dialog__body {
      padding: 20px 24px;
    }

    .el-form-item {
      margin-bottom: 20px;
    }

    .el-dialog__footer {
      padding: 12px 24px 20px;
      text-align: center;
    }
  }
}
</style>
