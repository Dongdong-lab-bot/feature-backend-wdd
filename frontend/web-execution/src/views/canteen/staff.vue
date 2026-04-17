<template>
  <div class="staff-container">
    <div class="page-header">
      <span class="title">用户管理</span>
      <el-button type="primary" @click="handleAdd">新增用户</el-button>
    </div>

    <el-table :data="tableData" v-loading="loading" style="width: 100%" :cell-style="{ padding: '20px 0' }">
      <el-table-column prop="username" label="用户账号" min-width="180" />
      <el-table-column prop="realName" label="用户昵称" min-width="120" />
      <el-table-column prop="gender" label="性别" min-width="80">
        <template #default="scope">
          <span :class="scope.row.gender === '女' ? 'gender-female' : 'gender-male'">{{ scope.row.gender }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="birthday" label="生日" min-width="120" />
      <el-table-column prop="mobile" label="手机号码" min-width="150" />
      <el-table-column prop="status" label="状态" min-width="160">
        <template #default="scope">
          <div class="status-wrap">
            <span :class="scope.row.status === 1 ? 'status-active' : 'status-disabled'">
              {{ scope.row.status === 1 ? '正常' : '禁用' }}
            </span>
            <el-switch
              v-model="scope.row.status"
              :active-value="1"
              :inactive-value="0"
              :disabled="!canUpdateStatus"
              @change="handleStatusChange(scope.row)"
            />
          </div>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="170" align="center" fixed="right">
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
      :title="dialogType === 'add' ? '新增' : '编辑'"
      width="620px"
      align-center
      @close="resetForm"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-position="top" hide-required-asterisk>
        <div class="form-grid">
          <el-form-item label="用户账号" prop="username">
            <el-input v-model="formData.username" :disabled="dialogType === 'edit'" placeholder="请输入用户账号" />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input v-model="formData.password" placeholder="请输入密码" show-password />
          </el-form-item>

          <el-form-item label="用户姓名" prop="realName">
            <el-input v-model="formData.realName" placeholder="请输入用户姓名" />
          </el-form-item>

          <el-form-item label="性别" prop="gender">
            <el-select v-model="formData.gender" placeholder="请选择" style="width: 100%">
              <el-option label="男" value="男" />
              <el-option label="女" value="女" />
            </el-select>
          </el-form-item>

          <el-form-item label="职务" prop="role">
            <el-select v-model="formData.role" placeholder="请选择" style="width: 100%">
              <el-option v-for="role in roleOptions" :key="role" :label="role" :value="role" />
            </el-select>
          </el-form-item>

          <el-form-item label="手机" prop="mobile">
            <el-input v-model="formData.mobile" placeholder="请输入手机号码" maxlength="11" />
          </el-form-item>
        </div>

        <div class="image-grid">
          <div class="image-item">
            <div class="image-title">人脸信息</div>
            <el-upload class="upload-box" action="#" :show-file-list="false" :auto-upload="false" @change="handleFaceImageChange">
              <img v-if="formData.faceImage" :src="formData.faceImage" alt="人脸信息" class="preview-image" />
              <div v-else class="upload-placeholder">
                <el-icon><Plus /></el-icon>
              </div>
            </el-upload>
            <div class="edit-link" @click="triggerImageUpload('face')">编辑</div>
          </div>

          <div class="image-item">
            <div class="image-title">健康证信息</div>
            <el-upload class="upload-box" action="#" :show-file-list="false" :auto-upload="false" @change="handleHealthImageChange">
              <img v-if="formData.healthImage" :src="formData.healthImage" alt="健康证信息" class="preview-image" />
              <div v-else class="upload-placeholder">
                <el-icon><Plus /></el-icon>
              </div>
            </el-upload>
            <div class="edit-link" @click="triggerImageUpload('health')">编辑</div>
          </div>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules, UploadFile } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import {
  createUser,
  deleteUser,
  getUserList,
  updateUser,
  updateUserStatus,
  type UserItem
} from '@/api/user'
import { uploadImage } from '@/api/employee'

interface StaffItem {
  id: number
  username: string
  realName: string
  gender: string
  birthday: string
  mobile: string
  roleId?: number
  role: string
  status: 1 | 0
  faceImage: string
  healthImage: string
}

interface StaffForm {
  id?: number
  username: string
  password: string
  realName: string
  gender: '男' | '女' | ''
  mobile: string
  role: string
  faceImage: string
  healthImage: string
}

const roleOptions = ['食堂安全员', '留样员', '员工']
const userStore = useUserStore()
const canUpdateStatus = userStore.hasPermission('user:status:update')

const loading = ref(false)
const submitLoading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const tableData = ref<StaffItem[]>([])

const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const formRef = ref<FormInstance>()

const formData = reactive<StaffForm>({
  id: undefined,
  username: '',
  password: '',
  realName: '',
  gender: '',
  mobile: '',
  role: '',
  faceImage: '',
  healthImage: ''
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  realName: [{ required: true, message: '请输入用户姓名', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  role: [{ required: true, message: '请选择职务', trigger: 'change' }],
  mobile: [
    { required: true, message: '请输入手机号码', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号码格式不正确', trigger: 'blur' }
  ]
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getUserList({
      page: currentPage.value,
      size: pageSize.value
    })

    tableData.value = res.records.map((item: UserItem) => ({
      id: item.id,
      username: item.username,
      realName: item.realName,
      gender: item.gender || '-',
      birthday: item.birthday || '-',
      mobile: item.mobile,
      roleId: item.roleId,
      role: item.roleName,
      status: item.status,
      faceImage: item.faceImage || '',
      healthImage: item.healthImage || ''
    }))
    total.value = res.total
  } catch {
    ElMessage.error('加载员工列表失败')
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

const handleEdit = (row: StaffItem) => {
  // [Fix] 员工管理界面允许编辑所有员工，移除"仅能编辑本人"的错误限制
  dialogType.value = 'edit'
  Object.assign(formData, {
    id: row.id,
    username: row.username,
    password: '',
    realName: row.realName,
    gender: row.gender === '女' ? '女' : '男',
    mobile: row.mobile,
    role: row.role,
    faceImage: row.faceImage,
    healthImage: row.healthImage
  })
  dialogVisible.value = true
}

const handleDelete = (row: StaffItem) => {
  ElMessageBox.confirm(`确定要删除用户\"${row.realName}\"吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    return deleteUser(row.id)
  }).then(() => {
    ElMessage.success('删除成功')
    loadData()
  }).catch((err: any) => {
    const msg = err?.message || '删除失败'
    ElMessage.warning(msg)
  })
}

const handleStatusChange = async (row: StaffItem) => {
  if (!canUpdateStatus) {
    ElMessage.warning('当前账号没有状态变更权限')
    row.status = row.status === 1 ? 0 : 1
    return
  }

  const prev = row.status === 1 ? 0 : 1
  try {
    await updateUserStatus(row.id, row.status)
    ElMessage.success(row.status === 1 ? '已启用' : '已禁用')
  } catch {
    row.status = prev as 1 | 0
  }
}

const handleImageChange = async (uploadFile: UploadFile, type: 'face' | 'health') => {
  const raw = uploadFile.raw
  if (!raw) return

  if (!raw.type.startsWith('image/')) {
    ElMessage.error('请上传图片格式文件')
    return
  }

  try {
    const res = await uploadImage(raw, type === 'face' ? '人脸照片' : '健康证照片')
    if (type === 'face') {
      formData.faceImage = res.url
    } else {
      formData.healthImage = res.url
    }
    ElMessage.success('图片上传成功')
  } catch {
    ElMessage.error('图片上传失败')
  }
}

const handleFaceImageChange = (uploadFile: UploadFile) => {
  handleImageChange(uploadFile, 'face')
}

const handleHealthImageChange = (uploadFile: UploadFile) => {
  handleImageChange(uploadFile, 'health')
}

const triggerImageUpload = (_type: 'face' | 'health') => {
  // Keep text action to align with the design; upload is triggered by clicking preview box.
}

const handleSubmit = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    if (dialogType.value === 'add') {
      await createUser({
        username: formData.username,
        password: formData.password,
        realName: formData.realName,
        gender: formData.gender,
        mobile: formData.mobile,
        face_image_url: formData.faceImage,
        health_image_url: formData.healthImage
      })
      ElMessage.success('新增成功')
    } else if (formData.id) {
      await updateUser({
        realName: formData.realName,
        gender: formData.gender,
        mobile: formData.mobile,
        face_image_url: formData.faceImage,
        health_image_url: formData.healthImage
      })
      ElMessage.success('编辑成功')
    }

    dialogVisible.value = false
    loadData()
  } catch (err: any) {
    const status = err?.response?.status
    if (status === 403) {
      ElMessage.error('无权限执行该操作，请重新登录后重试')
    } else {
      const msg = err?.response?.data?.msg || err?.message || '保存失败'
      ElMessage.error(msg)
    }
  } finally {
    submitLoading.value = false
  }
}

const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    id: undefined,
    username: '',
    password: '',
    realName: '',
    gender: '',
    mobile: '',
    role: '',
    faceImage: '',
    healthImage: ''
  })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.staff-container {
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

.status-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-active {
  color: #67c23a;
}

.status-disabled {
  color: #f56c6c;
}

.gender-male {
  color: #409eff;
}

.gender-female {
  color: #f56c6c;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 24px;
}

.image-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 8px;
}

.image-title {
  font-size: 14px;
  color: #303133;
  margin-bottom: 8px;
}

.upload-box {
  width: 140px;
}

.preview-image,
.upload-placeholder {
  width: 130px;
  height: 88px;
  border: 1px solid #dcdfe6;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}

.preview-image {
  object-fit: cover;
}

.edit-link {
  margin-top: 8px;
  color: #409eff;
  cursor: pointer;
  width: 130px;
  text-align: center;
}
</style>
