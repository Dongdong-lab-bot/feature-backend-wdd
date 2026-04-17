<template>
  <div class="user-container">
    <div class="page-header">
      <span class="title">用户管理</span>
      <el-button type="primary" @click="handleAdd">新增用户</el-button>
    </div>

    <el-table :data="tableData" v-loading="loading" style="width: 100%" :cell-style="{ padding: '24px 0' }">
      <el-table-column prop="username" label="用户账号" min-width="140" />
      <el-table-column prop="real_name" label="姓名" min-width="100" />
      <el-table-column label="用户类型" min-width="110">
        <template #default="scope">
          <el-tag :type="scope.row.role_type === 'EXECUTOR' ? 'success' : 'primary'" size="small">
            {{ scope.row.role_type === 'EXECUTOR' ? '食堂负责人' : '监管人员' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="mobile" label="手机号" min-width="130" />
      <el-table-column prop="org_name" label="部门/食堂" min-width="120">
        <template #default="scope">{{ scope.row.org_name || '-' }}</template>
      </el-table-column>
      <el-table-column prop="role_name" label="职务" min-width="100">
        <template #default="scope">{{ scope.row.role_name || '-' }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" min-width="80">
        <template #default="scope">
          <span :style="{ color: scope.row.status === 'ACTIVE' ? '#67C23A' : '#F56C6C' }">
            {{ scope.row.status === 'ACTIVE' ? '正常' : '禁用' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center" fixed="right">
        <template #default="scope">
          <el-button link type="primary" @click="handleEdit(scope.row)">编辑</el-button>
          <el-button link type="warning" @click="handleResetPwd(scope.row)">重置密码</el-button>
          <el-button link type="danger" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrapper">
      <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]" :total="total" layout="prev, pager, next"
        @size-change="handleSizeChange" @current-change="handleCurrentChange" />
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogType === 'add' ? '新增用户' : '编辑用户'"
      width="520px" @close="resetForm" align-center>
      <el-form ref="formRef" :model="formData" :rules="rules" label-position="top" hide-required-asterisk>

        <!-- 用户类型（新增时必选） -->
        <el-form-item label="用户类型" prop="role_type">
          <el-radio-group v-model="formData.role_type" :disabled="dialogType === 'edit'">
            <el-radio-button value="REGULATOR">监管人员</el-radio-button>
            <el-radio-button value="EXECUTOR">食堂负责人</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 账号（仅新增） -->
        <el-form-item label="用户账号" prop="username" v-if="dialogType === 'add'">
          <el-input v-model="formData.username" placeholder="请输入登录账号" />
        </el-form-item>

        <!-- 密码（仅新增） -->
        <el-form-item label="登录密码" prop="password" v-if="dialogType === 'add'">
          <el-input v-model="formData.password" type="password" show-password placeholder="6-64位密码" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword" v-if="dialogType === 'add'">
          <el-input v-model="formData.confirmPassword" type="password" show-password placeholder="再次输入密码" />
        </el-form-item>

        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="formData.real_name" placeholder="请输入真实姓名" />
        </el-form-item>

        <!-- 所属食堂（EXECUTOR） / 所属部门（REGULATOR） -->
        <el-form-item :label="formData.role_type === 'EXECUTOR' ? '所属食堂' : '所属部门'" prop="org_id">
          <el-select v-model="formData.org_id" :placeholder="formData.role_type === 'EXECUTOR' ? '请选择所属食堂' : '请选择所属部门'" style="width:100%" clearable>
            <el-option
              v-for="item in (formData.role_type === 'EXECUTOR' ? canteenList : deptList)"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="职务">
          <el-select v-model="formData.role_id" placeholder="请选择职务" style="width:100%" clearable>
            <el-option v-for="role in roleList" :key="role.id" :label="role.name" :value="role.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="手机" prop="mobile">
          <el-input v-model="formData.mobile" placeholder="请输入手机号码" />
        </el-form-item>

        <el-form-item label="性别">
          <el-select v-model="formData.gender" placeholder="请选择性别" style="width:100%" clearable>
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
          </el-select>
        </el-form-item>

      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="resetPwdVisible" title="重置密码" width="400px" align-center>
      <el-form label-position="top">
        <el-form-item label="新密码">
          <el-input v-model="newPassword" type="password" show-password placeholder="请输入新密码（6-64位）" />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="newPasswordConfirm" type="password" show-password placeholder="再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="resetPwdLoading" @click="confirmResetPwd">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { getUserList, createUser, updateUser, deleteUser, resetUserPassword, type AdminUser } from '@/api/user'
import { getAllDepts, type AdminDeptRecord } from '@/api/canteen'
import request from '@/utils/request'

interface RoleItem { id: number; name: string }

interface FormData {
  id?: number
  username: string
  real_name: string
  mobile: string
  gender: string
  org_id?: number
  role_id?: number
  role_type: 'REGULATOR' | 'EXECUTOR'
  password: string
  confirmPassword: string
}

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref<AdminUser[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const allDeptList = ref<AdminDeptRecord[]>([])
const roleList = ref<RoleItem[]>([])

// 所有部门（非食堂）
const deptList = computed(() => allDeptList.value.filter(d => d.org_type !== 'CANTEEN'))
// 食堂列表
const canteenList = computed(() => allDeptList.value.filter(d => d.org_type === 'CANTEEN'))

const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const formRef = ref<FormInstance>()

const formData = reactive<FormData>({
  username: '',
  real_name: '',
  mobile: '',
  gender: '',
  org_id: undefined,
  role_id: undefined,
  role_type: 'REGULATOR',
  password: '',
  confirmPassword: '',
})

// 重置密码相关
const resetPwdVisible = ref(false)
const resetPwdLoading = ref(false)
const newPassword = ref('')
const newPasswordConfirm = ref('')
const resetPwdUserId = ref<number>(0)
const resetPwdUserName = ref('')

const rules = computed<FormRules>(() => ({
  role_type: [{ required: true, message: '请选择用户类型', trigger: 'change' }],
  username: dialogType.value === 'add' ? [{ required: true, message: '请输入用户账号', trigger: 'blur' }] : [],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  mobile: [
    { required: true, message: '请输入手机号码', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号码格式不正确', trigger: 'blur' },
  ],
  org_id: formData.role_type === 'EXECUTOR' ? [{ required: true, message: '请选择所属食堂', trigger: 'change' }] : [],
  password: dialogType.value === 'add' ? [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 64, message: '密码长度须6-64位', trigger: 'blur' },
  ] : [],
  confirmPassword: dialogType.value === 'add' ? [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (_rule: any, value: string, callback: (e?: Error) => void) => {
        if (value !== formData.password) callback(new Error('两次密码不一致'))
        else callback()
      },
      trigger: 'blur',
    },
  ] : [],
}))

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getUserList({ page: currentPage.value, size: pageSize.value })
    tableData.value = res.data?.records || []
    total.value = res.data?.total || 0
  } catch {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const loadAllDepts = async () => {
  try {
    const res: any = await getAllDepts()
    allDeptList.value = res.data?.records || []
  } catch { /* ignore */ }
}

const loadRoleList = async () => {
  try {
    const res: any = await request({ url: '/admin/roles', method: 'get', params: { page: 1, size: 200 } })
    roleList.value = (res.data?.records || []).map((r: any) => ({ id: r.id, name: r.name }))
  } catch { /* ignore */ }
}

const handleSizeChange = (val: number) => { pageSize.value = val; loadData() }
const handleCurrentChange = (val: number) => { currentPage.value = val; loadData() }

const handleAdd = () => {
  dialogType.value = 'add'
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row: AdminUser) => {
  dialogType.value = 'edit'
  Object.assign(formData, {
    id: row.id,
    username: row.username || '',
    real_name: row.real_name || '',
    mobile: row.mobile || '',
    gender: row.gender || '',
    org_id: row.org_id,
    role_id: row.role_id,
    role_type: (row.role_type as 'REGULATOR' | 'EXECUTOR') || 'REGULATOR',
    password: '',
    confirmPassword: '',
  })
  dialogVisible.value = true
}

const handleResetPwd = (row: AdminUser) => {
  resetPwdUserId.value = row.id!
  resetPwdUserName.value = row.real_name || row.username || ''
  newPassword.value = ''
  newPasswordConfirm.value = ''
  resetPwdVisible.value = true
}

const confirmResetPwd = async () => {
  if (newPassword.value.length < 6 || newPassword.value.length > 64) {
    ElMessage.warning('密码长度须6-64位')
    return
  }
  if (newPassword.value !== newPasswordConfirm.value) {
    ElMessage.warning('两次密码不一致')
    return
  }
  resetPwdLoading.value = true
  try {
    await resetUserPassword(resetPwdUserId.value, newPassword.value)
    ElMessage.success(`已重置「${resetPwdUserName.value}」的密码`)
    resetPwdVisible.value = false
  } catch (err: any) {
    ElMessage.error(err?.data?.msg || '重置密码失败')
  } finally {
    resetPwdLoading.value = false
  }
}

const handleDelete = (row: AdminUser) => {
  ElMessageBox.confirm(
    `确定要删除用户「${row.real_name || row.username}」吗？`,
    '提示',
    { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
  ).then(async () => {
    try {
      await deleteUser(row.id!)
      ElMessage.success('删除成功')
      loadData()
    } catch {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (dialogType.value === 'add') {
        await createUser({
          username: formData.username,
          real_name: formData.real_name,
          mobile: formData.mobile,
          gender: formData.gender,
          org_id: formData.org_id,
          role_id: formData.role_id,
          password: formData.password,
          role_type: formData.role_type,
        })
      } else {
        await updateUser(formData.id!, {
          real_name: formData.real_name,
          mobile: formData.mobile,
          gender: formData.gender,
          org_id: formData.org_id,
          role_id: formData.role_id,
          status: (formData as any).status,
        })
      }
      ElMessage.success(dialogType.value === 'add' ? '新增成功' : '编辑成功')
      dialogVisible.value = false
      loadData()
    } catch (err: any) {
      const msg = err?.data?.msg || (dialogType.value === 'add' ? '新增失败' : '编辑失败')
      ElMessage.error(msg)
    } finally {
      submitLoading.value = false
    }
  })
}

const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    id: undefined,
    username: '',
    real_name: '',
    mobile: '',
    gender: '',
    org_id: undefined,
    role_id: undefined,
    role_type: 'REGULATOR',
    password: '',
    confirmPassword: '',
  })
}

onMounted(() => {
  loadData()
  loadAllDepts()
  loadRoleList()
})
</script>

<style scoped>
.user-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header .title { font-size: 18px; font-weight: 600; color: #303133; }
.pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 20px; }
</style>
