<template>
  <div class="position-container">
    <div class="page-header">
      <span class="title">职务管理</span>
      <el-button type="primary" @click="handleAdd">新增职务</el-button>
    </div>

    <el-table :data="tableData" v-loading="loading" style="width: 100%" :cell-style="{ padding: '24px 0' }">
      <el-table-column prop="name" label="职务昵称" min-width="220" />
      <el-table-column prop="level" label="职级" min-width="140" />
      <el-table-column prop="permission" label="权限" min-width="160" />
      <el-table-column label="操作" width="180" align="center" fixed="right">
        <template #default="scope">
          <el-button link type="primary" @click="handleEdit(scope.row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '新增职务' : '编辑职务'"
      width="600px"
      @close="resetForm"
      align-center
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-position="top" hide-required-asterisk>
        <el-form-item label="职务名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入职务名称" />
        </el-form-item>

        <el-form-item label="职级" prop="level">
          <el-select v-model="formData.level" placeholder="请选择职级" style="width: 100%" @change="handleLevelChange">
            <el-option v-for="option in levelOptions" :key="option.value" :label="option.label" :value="option.value" />
          </el-select>
        </el-form-item>

        <el-form-item label="权限说明">
          <el-input v-model="formData.permissions_desc" placeholder="根据职级自动带出，可查看不可编辑" disabled />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { getRoleList, createRole, updateRole, deleteRole, type RoleRecord } from '@/api/role'

interface PositionItem {
  id: number
  name: string
  level: string
  permission: string
}

interface PositionForm {
  id?: number
  name: string
  level: string
  permissions_desc: string
}

const levelPermissionMap: Record<string, string> = {
  '员级': '基础操作权限：可进行日常信息录入、查看台账记录',
  '助级': '操作权限：可进行日常信息录入、查看台账记录、提交巡检任务',
  '中级': '管理权限：可进行日常信息录入、查看台账记录、提交巡检任务、审核下级提交内容',
  '副高级': '高级管理权限：具备中级权限，可管理下属职务、查看全部数据、导出报表',
  '正高级': '全面管理权限：具备副高级权限，可进行系统配置、添加/删除账号、查看全部操作日志'
}

const levelOptions = [
  { value: '员级', label: '员级' },
  { value: '助级', label: '助级' },
  { value: '中级', label: '中级' },
  { value: '副高级', label: '副高级' },
  { value: '正高级', label: '正高级' }
]

const loading = ref(false)
const submitLoading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const allData = ref<PositionItem[]>([])

const tableData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return allData.value.slice(start, end)
})

const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const formRef = ref<FormInstance>()

const formData = reactive<PositionForm>({
  id: undefined,
  name: '',
  level: '',
  permissions_desc: ''
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入职务名称', trigger: 'blur' }],
  level: [{ required: true, message: '请选择职级', trigger: 'change' }]
}

watch(() => formData.level, (newLevel) => {
  formData.permissions_desc = levelPermissionMap[newLevel] || ''
})

const handleLevelChange = () => {
  formData.permissions_desc = levelPermissionMap[formData.level] || ''
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getRoleList({ page: currentPage.value, size: pageSize.value })
    allData.value = res.records.map((item: RoleRecord) => ({
      id: item.id,
      name: item.name,
      level: item.level || '',
      permission: item.permissions_desc || levelPermissionMap[item.level] || '-'
    }))
    total.value = res.total
  } catch {
    ElMessage.error('加载职务列表失败')
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadData()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadData()
}

const handleAdd = () => {
  dialogType.value = 'add'
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row: PositionItem) => {
  dialogType.value = 'edit'
  Object.assign(formData, {
    id: row.id,
    name: row.name,
    level: row.level,
    permissions_desc: row.permission
  })
  dialogVisible.value = true
}

const handleDelete = (row: PositionItem) => {
  ElMessageBox.confirm(`确定要删除职务"${row.name}"吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteRole(row.id)
      ElMessage.success('删除成功')
      loadData()
    } catch (err: any) {
      ElMessage.error(err?.message || '删除失败')
    }
  }).catch(() => {})
}

const handleSubmit = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    if (dialogType.value === 'add') {
      await createRole({
        name: formData.name,
        level: formData.level,
        permissions_desc: formData.permissions_desc
      })
      ElMessage.success('新增成功')
    } else if (formData.id) {
      await updateRole(formData.id, {
        name: formData.name,
        level: formData.level,
        permissions_desc: formData.permissions_desc
      })
      ElMessage.success('编辑成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (err: any) {
    ElMessage.error(err?.message || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    id: undefined,
    name: '',
    level: '',
    permissions_desc: ''
  })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.position-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header .title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
