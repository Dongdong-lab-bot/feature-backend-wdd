<template>
  <div class="dept-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <span class="title">部门管理</span>
      <el-button type="primary" @click="handleAdd()">新增部门</el-button>
    </div>

    <!-- 部门表格 -->
    <el-table
      :data="filteredDeptData"
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
      <el-table-column prop="deptName" label="部门称号" min-width="150">
        <template #default="scope">
          <span :style="{ paddingLeft: (scope.row.level || 0) * 20 + 'px' }">
            {{ scope.row.deptName }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="人数" min-width="100" align="center">
        <template #default="scope">
          {{ scope.row.displayMemberCount }}
        </template>
      </el-table-column>
      <el-table-column prop="createTime" label="创建时间" min-width="200" align="center" />
      <el-table-column label="权限管理" min-width="100" align="center">
        <template #default="scope">
          <el-button link type="primary" @click="handleEdit(scope.row)">编辑</el-button>
        </template>
      </el-table-column>
      <el-table-column label="基本信息" min-width="150" align="center" fixed="right">
        <template #default="scope">
          <el-button link type="primary" @click="handleEdit(scope.row)">编辑</el-button>
          <el-button 
            v-if="scope.row.level === 0"
            link 
            type="primary" 
            @click="handleAdd(scope.row)"
          >
            添加子级
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
        <el-form-item label="部门名称:" prop="deptName">
          <el-input v-model="formData.deptName" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="部门类型:" prop="orgType">
          <el-select v-model="formData.orgType" placeholder="请选择部门类型" style="width: 100%">
            <el-option v-for="(label, value) in ORG_TYPE_LABELS" :key="value" :label="label" :value="value" />
          </el-select>
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
import { getDeptList, createDept, updateDept, deleteDept } from '@/api/dept'

// 部门接口定义
interface Dept {
  id: string
  parentId?: string | null
  deptName: string
  orgType: string
  createTime: string
  memberCount: number
  displayMemberCount?: number
  expanded?: boolean
  children?: Dept[]
  level?: number
  hasChildren?: boolean
}

// 加载状态
const loading = ref(false)
const submitLoading = ref(false)

// 部门数据
const deptData = ref<Dept[]>([])

const DUPLICATE_DEPT_MESSAGE = '同级部门名称已存在，请修改后重试'

// 分页
const currentPage = ref(1)
const pageSize = ref(8)
const total = ref(0)

// 展开状态Map
const expandedKeys = ref<Set<string>>(new Set())

// 扁平化并过滤部门数据
const calcDisplayMemberCount = (node: Dept): number => {
  if (!node.children || node.children.length === 0) {
    return node.memberCount
  }
  return node.children.reduce((sum, child) => sum + calcDisplayMemberCount(child), 0)
}

const filteredDeptData = computed(() => {
  const flattenDept = (depts: Dept[], level = 0): Dept[] => {
    const result: Dept[] = []
    depts.forEach(dept => {
      // 创建部门副本，移除children避免Element Plus自动识别树形结构
      const { children, ...deptWithoutChildren } = dept
      const deptWithLevel = { 
        ...deptWithoutChildren, 
        level, 
        expanded: expandedKeys.value.has(dept.id),
        hasChildren: !!(children && children.length > 0),
        displayMemberCount: calcDisplayMemberCount(dept)
      }
      result.push(deptWithLevel)
      if (children && deptWithLevel.expanded) {
        result.push(...flattenDept(children, level + 1))
      }
    })
    return result
  }
  const start = (currentPage.value - 1) * pageSize.value
  const pagedRoots = deptData.value.slice(start, start + pageSize.value)
  return flattenDept(pagedRoots)
})

// 切换展开状态
const toggleExpand = (row: Dept) => {
  if (expandedKeys.value.has(row.id)) {
    expandedKeys.value.delete(row.id)
  } else {
    expandedKeys.value.add(row.id)
  }
}

const normalizeName = (name?: string): string => {
  return (name || '').trim().toLowerCase()
}

const flattenAllDepts = (depts: Dept[]): Dept[] => {
  const result: Dept[] = []
  const walk = (items: Dept[]) => {
    items.forEach((item) => {
      result.push(item)
      if (item.children && item.children.length > 0) {
        walk(item.children)
      }
    })
  }
  walk(depts)
  return result
}

const hasSiblingDuplicateName = (payload: { id?: string; parentId?: string | null; deptName?: string }): boolean => {
  const targetName = normalizeName(payload.deptName)
  if (!targetName) {
    return false
  }

  const targetParentId = payload.parentId ?? null
  const allDepts = flattenAllDepts(deptData.value)
  return allDepts.some((dept) => {
    if (payload.id && String(dept.id) === String(payload.id)) {
      return false
    }
    return (dept.parentId ?? null) === targetParentId && normalizeName(dept.deptName) === targetName
  })
}

// 对话框控制
const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const currentParentRow = ref<Dept | null>(null)

// 对话框标题
const dialogTitle = computed(() => {
  if (dialogType.value === 'add') {
    return currentParentRow.value ? '新增子部门' : '新增部门'
  }
  return '编辑部门'
})

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const formData = reactive<Partial<Dept> & { orgType?: string }>({
  parentId: undefined,
  deptName: '',
  orgType: 'AREA'
})

const ORG_TYPE_LABELS: Record<string, string> = {
  AREA: '行政区域',
  SCHOOL: '学校',
  CANTEEN: '食堂'
}

// 表单验证规则
const rules: FormRules = {
  deptName: [{ required: true, message: '请输入部门名称', trigger: 'blur' }],
  orgType: [{ required: true, message: '请选择部门类型', trigger: 'change' }]
}

// 加载部门数据（从后端获取扁平列表后构建树）
const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getDeptList({ page: 1, size: 200 })
    const records: any[] = res.data?.records || []
    // 转换字段名并构建树结构
    const nodes: Record<string, Dept> = {}
    records.forEach(r => {
      nodes[String(r.id)] = {
        id: String(r.id),
        parentId: r.parent_id != null ? String(r.parent_id) : null,
        deptName: r.name,
        orgType: r.org_type,
        memberCount: Number(r.member_count ?? 0),
        createTime: r.created_at ? r.created_at.slice(0, 10) : '',
        children: []
      }
    })
    const roots: Dept[] = []
    records.forEach(r => {
      const node = nodes[String(r.id)]
      if (r.parent_id && nodes[String(r.parent_id)]) {
        nodes[String(r.parent_id)].children!.push(node)
      } else {
        roots.push(node)
      }
    })
    deptData.value = roots
    total.value = roots.length
    currentPage.value = 1
  } catch {
    ElMessage.error('加载部门列表失败')
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

// 新增部门
const handleAdd = (row?: Dept) => {
  dialogType.value = 'add'
  currentParentRow.value = row || null
  if (row) {
    formData.parentId = row.id
  } else {
    formData.parentId = undefined
  }
  dialogVisible.value = true
}

// 编辑部门
const handleEdit = (row: Dept) => {
  dialogType.value = 'edit'
  currentParentRow.value = null
  Object.assign(formData, { ...row })
  dialogVisible.value = true
}

// 删除部门
const handleDelete = (row: Dept) => {
  ElMessageBox.confirm(
    `确定要删除部门"${row.deptName}"吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteDept(row.id)
      ElMessage.success('删除成功')
      loadData()
    } catch {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      const candidate = {
        id: dialogType.value === 'edit' ? String(formData.id) : undefined,
        parentId: (formData.parentId ?? null) as string | null,
        deptName: formData.deptName
      }

      if (hasSiblingDuplicateName(candidate)) {
        ElMessage.warning(DUPLICATE_DEPT_MESSAGE)
        return
      }

      submitLoading.value = true
      try {
        if (dialogType.value === 'add') {
          await createDept({
            deptName: formData.deptName!,
            parentId: formData.parentId ?? null,
            orgType: formData.orgType || 'AREA',
            memberCount: 0,
            status: 1
          })
        } else {
          await updateDept(String(formData.id), {
            deptName: formData.deptName!,
            parentId: formData.parentId ?? null,
            orgType: formData.orgType || 'AREA',
            memberCount: 0,
            status: 1
          })
        }
        ElMessage.success(dialogType.value === 'add' ? '新增成功' : '更新成功')
        dialogVisible.value = false
        loadData()
      } catch (err: any) {
        if (!err?.__shown) {
          const msg = err?.response?.data?.msg || err?.response?.data?.detail || err?.message || '操作失败'
          ElMessage.error(msg)
        }
      } finally {
        submitLoading.value = false
      }
    }
  })
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    parentId: undefined,
    deptName: '',
    orgType: 'AREA'
  })
  currentParentRow.value = null
}

// 初始化
onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.dept-container {
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
