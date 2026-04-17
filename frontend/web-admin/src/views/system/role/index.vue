<template>
  <div class="position-container">
    <div class="page-header">
      <span class="title">职务管理</span>
      <el-button type="primary" @click="handleAdd">新增职务</el-button>
    </div>

    <el-table :data="tableData" v-loading="loading" style="width: 100%" :cell-style="{ padding: '24px 0' }">
      <el-table-column prop="name" label="职务昵称" min-width="200" />
      <el-table-column prop="level" label="职级" min-width="150" />
      <el-table-column prop="permissions_desc" label="权限" min-width="300">
        <template #default="scope">
          <span v-if="scope.row.permissions && scope.row.permissions.length">
            {{ scope.row.permissions.join('、') }}
          </span>
          <span v-else-if="scope.row.permissions_desc">{{ scope.row.permissions_desc }}</span>
          <span v-else style="color:#c0c4cc">未设置</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" align="center" fixed="right">
        <template #default="scope">
          <el-button link type="primary" @click="handleEdit(scope.row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrapper">
      <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]" :total="total" layout="prev, pager, next"
        @size-change="handleSizeChange" @current-change="handleCurrentChange" />
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogType === 'add' ? '新增职务' : '编辑职务'"
      width="500px" @close="resetForm" align-center>
      <el-form ref="formRef" :model="formData" :rules="rules" label-position="top" hide-required-asterisk>
        <el-form-item label="职务名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入职务名称" />
        </el-form-item>
        <el-form-item label="职级" prop="job_level">
          <el-select v-model="formData.job_level" placeholder="请选择职级" style="width: 100%">
            <el-option label="员级" value="员级" />
            <el-option label="助级" value="助级" />
            <el-option label="中级" value="中级" />
            <el-option label="副高级" value="副高级" />
            <el-option label="正高级" value="正高级" />
          </el-select>
        </el-form-item>
        <el-form-item label="权限说明">
          <el-input v-model="formData.permissions_desc" placeholder="请输入权限说明（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { getRoleList, createRole, updateRole, deleteRole } from '@/api/role'

interface Role {
  id: string
  name: string
  role_type: string
  level?: string
  permissions?: string[]
  permissions_desc?: string
  created_at?: string
}

interface FormData {
  id?: string
  name: string
  job_level: string
  permissions_desc: string
}

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref<Role[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const formRef = ref<FormInstance>()
const formData = reactive<FormData>({ name: '', job_level: '', permissions_desc: '' })

const rules: FormRules = {
  name: [{ required: true, message: '请输入职务名称', trigger: 'blur' }],
  job_level: [{ required: true, message: '请选择职级', trigger: 'change' }]
}

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getRoleList({ page: currentPage.value, size: pageSize.value })
    tableData.value = res.data?.records || []
    total.value = res.data?.total || 0
  } catch { ElMessage.error('加载职务列表失败') } finally { loading.value = false }
}

const handleSizeChange = (val: number) => { pageSize.value = val; loadData() }
const handleCurrentChange = (val: number) => { currentPage.value = val; loadData() }
const handleAdd = () => { dialogType.value = 'add'; dialogVisible.value = true }

const handleEdit = (row: Role) => {
  dialogType.value = 'edit'
  Object.assign(formData, {
    id: row.id,
    name: row.name,
    job_level: row.level || '',
    permissions_desc: row.permissions_desc || ''
  })
  dialogVisible.value = true
}

const handleDelete = (row: Role) => {
  ElMessageBox.confirm(`确定要删除职务"${row.name}"吗？`, '提示',
    { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
  ).then(async () => {
    try { await deleteRole(row.id); ElMessage.success('删除成功'); loadData() }
    catch { ElMessage.error('删除失败') }
  }).catch(() => {})
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      const payload = {
        positionName: formData.name,
        jobLevel: formData.job_level,
        permissionsDesc: formData.permissions_desc
      }
      if (dialogType.value === 'add') await createRole(payload)
      else await updateRole(String(formData.id), payload)
      ElMessage.success(dialogType.value === 'add' ? '新增成功' : '编辑成功')
      dialogVisible.value = false
      loadData()
    } catch (err: any) { ElMessage.error(err?.data?.msg || '操作失败') }
    finally { submitLoading.value = false }
  })
}

const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(formData, { id: undefined, name: '', job_level: '', permissions_desc: '' })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.position-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header .title { font-size: 18px; font-weight: 600; color: #303133; }
.pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 20px; }
</style>