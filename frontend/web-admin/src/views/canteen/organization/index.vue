<template>
  <div class="org-page">
    <div class="page-title">食堂管理</div>

    <div class="content-card">
      <div class="left-tree">
        <el-button type="primary" class="add-btn" @click="openCreate">新增食堂</el-button>
        <el-tree
          :data="orgTree"
          node-key="id"
          :props="treeProps"
          default-expand-all
          :highlight-current="true"
          :expand-on-click-node="false"
          @node-click="handleTreeClick"
        />
      </div>

      <div class="right-table">
        <el-table v-loading="tableLoading" :data="filteredList" :cell-style="{ padding: '16px 0' }" style="width: 100%">
          <el-table-column prop="name" label="食堂名称" min-width="180" />
          <el-table-column prop="manager" label="食堂负责人" min-width="120" />
          <el-table-column prop="phone" label="联系方式" min-width="140" />
          <el-table-column label="营业执照" min-width="140" align="center">
            <template #default="scope">
              <img v-if="scope.row.licenseUrl" :src="scope.row.licenseUrl" class="license-thumb" alt="营业执照" />
              <span v-else>/</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" align="center">
            <template #default="scope">
              <el-button link type="primary" @click="openEdit(scope.row)">编辑</el-button>
              <el-button link type="danger" @click="removeItem(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '新增食堂' : '编辑食堂'" width="820px" align-center>
      <el-form ref="formRef" :model="formData" :rules="rules" label-position="top">
        <el-form-item label="食堂名称" prop="name">
          <el-input v-model="formData.name" maxlength="50" show-word-limit />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="食堂负责人" prop="manager">
              <el-input v-model="formData.manager" maxlength="20" show-word-limit />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系方式" prop="phone">
              <el-input v-model="formData.phone" maxlength="11" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="食堂位置定位" prop="address">
          <el-input v-model="formData.address" maxlength="200" show-word-limit />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="上传营业执照">
              <div class="license-upload">
                <img v-if="formData.licenseUrl" :src="formData.licenseUrl" class="license-preview" alt="营业执照" />
                <div v-else class="license-empty">暂无营业执照</div>
                <div class="upload-actions">
                  <el-upload
                    class="license-uploader"
                    :show-file-list="false"
                    accept="image/*"
                    :auto-upload="false"
                    :on-change="handleLicenseChange"
                  >
                    <el-button link type="primary">上传图片</el-button>
                  </el-upload>
                  <el-button link type="danger" @click="formData.licenseUrl = ''">删除</el-button>
                </div>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="营业执照有效期" prop="licenseStart">
              <div class="date-range-box">
                <span class="range-label">起</span>
                <el-date-picker v-model="formData.licenseStart" type="date" value-format="YYYY-MM-DD" style="width: 100%" @change="formRef?.validateField('licenseEnd')" />
              </div>
            </el-form-item>
            <el-form-item prop="licenseEnd">
              <div class="date-range-box">
                <span class="range-label">止</span>
                <el-date-picker v-model="formData.licenseEnd" type="date" value-format="YYYY-MM-DD" style="width: 100%" @change="formRef?.validateField('licenseStart')" />
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import type { UploadProps } from 'element-plus'
import {
  createCanteenOrg,
  deleteCanteenOrg,
  getAllDepts,
  getOrgTree,
  updateCanteenOrg,
  uploadLicenseImage
} from '@/api/canteen'

interface TreeNode {
  id: number
  label: string
  children?: TreeNode[]
}

interface CanteenItem {
  id: number
  orgId: number
  parentId: number | null
  name: string
  manager: string
  phone: string
  address: string
  licenseUrl: string
  licenseStart: string
  licenseEnd: string
}

interface CanteenExtraMeta {
  manager: string
  phone: string
  address: string
  licenseUrl: string
  licenseStart: string
  licenseEnd: string
}

const META_STORAGE_KEY = 'web_admin_canteen_meta_v1'

const treeProps = { label: 'label', children: 'children' }
const orgTree = ref<TreeNode[]>([])
const selectedOrgId = ref<number>(0)
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const tableLoading = ref(false)

const list = ref<CanteenItem[]>([])
const canteenMetaMap = ref<Record<number, CanteenExtraMeta>>({})

const formData = reactive<CanteenItem>({
  id: 0,
  orgId: 0,
  parentId: null,
  name: '',
  manager: '',
  phone: '',
  address: '',
  licenseUrl: '',
  licenseStart: '',
  licenseEnd: ''
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入食堂名称', trigger: 'blur' },
    { min: 2, max: 50, message: '食堂名称长度为 2~50 个字符', trigger: 'blur' }
  ],
  manager: [
    { required: true, message: '请输入食堂负责人', trigger: 'blur' },
    { min: 2, max: 20, message: '负责人姓名长度为 2~20 个字符', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入联系方式', trigger: 'blur' },
    {
      pattern: /^1[3-9]\d{9}$/,
      message: '请输入正确的手机号格式（11位，1开头）',
      trigger: 'blur'
    }
  ],
  address: [
    {
      validator: (_rule: any, value: string, callback: any) => {
        if (!value) {
          callback()
        } else if (value.length < 5 || value.length > 200) {
          callback(new Error('位置信息长度为 5~200 个字符'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  licenseStart: [
    {
      validator: (_rule: unknown, _val: string, callback: (err?: Error) => void) => {
        if (formData.licenseEnd && !formData.licenseStart) {
          callback(new Error('已填写截止日期，请同时填写起始日期'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  licenseEnd: [
    {
      validator: (_rule: unknown, _val: string, callback: (err?: Error) => void) => {
        if (formData.licenseStart && !formData.licenseEnd) {
          callback(new Error('已填写起始日期，请同时填写截止日期'))
        } else if (formData.licenseStart && formData.licenseEnd && formData.licenseEnd < formData.licenseStart) {
          callback(new Error('截止日期不能早于起始日期'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

const allOrgIds = computed(() => {
  const ids: number[] = []
  const walk = (nodes: TreeNode[]) => {
    nodes.forEach((node) => {
      ids.push(node.id)
      if (node.children) walk(node.children)
    })
  }
  walk(orgTree.value)
  return new Set(ids)
})

const descendantIdMap = computed(() => {
  const map = new Map<number, Set<number>>()
  const walk = (node: TreeNode): Set<number> => {
    const collected = new Set<number>([node.id])
    node.children?.forEach((child) => {
      const childSet = walk(child)
      childSet.forEach((id) => collected.add(id))
    })
    map.set(node.id, collected)
    return collected
  }
  orgTree.value.forEach((root) => walk(root))
  return map
})

const filteredList = computed(() => {
  if (selectedOrgId.value === 0) return list.value
  if (!allOrgIds.value.has(selectedOrgId.value)) return list.value
  const ids = descendantIdMap.value.get(selectedOrgId.value)
  if (!ids) return list.value
  return list.value.filter((item) => ids.has(item.orgId) || ids.has(item.parentId || -1))
})

const apiBase = computed(() => String(import.meta.env.VITE_APP_BASE_API || '').replace(/\/$/, ''))

const toAbsoluteUrl = (url: string) => {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) return url
  return `${apiBase.value}${url}`
}

const loadMetaMap = () => {
  const raw = localStorage.getItem(META_STORAGE_KEY)
  if (!raw) {
    canteenMetaMap.value = {}
    return
  }
  try {
    const parsed = JSON.parse(raw)
    canteenMetaMap.value = parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    canteenMetaMap.value = {}
  }
}

const saveMetaMap = () => {
  localStorage.setItem(META_STORAGE_KEY, JSON.stringify(canteenMetaMap.value))
}

const syncListFromBackend = (records: any[]) => {
  list.value = records
    .filter((item) => item.org_type === 'CANTEEN')
    .map((item) => {
      const meta = canteenMetaMap.value[item.id] || {
        manager: '',
        phone: '',
        address: '',
        licenseUrl: '',
        licenseStart: '',
        licenseEnd: ''
      }
      return {
        id: item.id,
        orgId: item.id,
        parentId: item.parent_id ?? null,
        name: item.name,
        manager: meta.manager,
        phone: meta.phone,
        address: meta.address,
        licenseUrl: meta.licenseUrl,
        licenseStart: meta.licenseStart,
        licenseEnd: meta.licenseEnd
      } as CanteenItem
    })
}

const loadPageData = async () => {
  tableLoading.value = true
  try {
    loadMetaMap()
    const [treeRes, deptRes]: any[] = await Promise.all([getOrgTree(), getAllDepts()])
    const rawTree = treeRes?.data?.tree || treeRes?.tree || []
    const toTree = (nodes: any[]): TreeNode[] => {
      return (nodes || []).map((node: any) => ({
        id: node.id,
        label: node.name,
        children: toTree(node.children || [])
      }))
    }
    orgTree.value = toTree(rawTree)

    const records = deptRes?.data?.records || []
    syncListFromBackend(records)
  } finally {
    tableLoading.value = false
  }
}

const resetForm = () => {
  formRef.value?.clearValidate()
  Object.assign(formData, {
    id: 0,
    orgId: selectedOrgId.value,
    parentId: selectedOrgId.value || null,
    name: '',
    manager: '',
    phone: '',
    address: '',
    licenseUrl: '',
    licenseStart: '',
    licenseEnd: ''
  })
}

const handleTreeClick = (node: TreeNode) => {
  selectedOrgId.value = node.id
}

const openCreate = () => {
  dialogMode.value = 'create'
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

const openEdit = (row: CanteenItem) => {
  dialogMode.value = 'edit'
  editingId.value = row.id
  Object.assign(formData, row)
  dialogVisible.value = true
}

const removeItem = (id: number) => {
  ElMessageBox.confirm('确认删除该食堂吗？', '提示', {
    type: 'warning',
    confirmButtonText: '确定',
    cancelButtonText: '取消'
  }).then(async () => {
    await deleteCanteenOrg(id)
    delete canteenMetaMap.value[id]
    saveMetaMap()
    await loadPageData()
    ElMessage.success('删除成功')
  }).catch(() => {})
}

const handleLicenseChange: UploadProps['onChange'] = async (uploadFile) => {
  const file = uploadFile.raw
  if (!file) return
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请上传图片格式文件')
    return
  }
  const res: any = await uploadLicenseImage(file, `${formData.name || '食堂'}营业执照`)
  const url = res?.data?.url || ''
  if (!url) {
    ElMessage.error('上传成功但未返回图片地址')
    return
  }
  formData.licenseUrl = toAbsoluteUrl(url)
  ElMessage.success('上传成功')
}

const submitForm = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  if (dialogMode.value === 'create') {
    const parentId = selectedOrgId.value || null
    const res: any = await createCanteenOrg({ name: formData.name, parent_id: parentId })
    const createdId = Number(res?.data?.id)
    if (createdId) {
      canteenMetaMap.value[createdId] = {
        manager: formData.manager,
        phone: formData.phone,
        address: formData.address,
        licenseUrl: formData.licenseUrl,
        licenseStart: formData.licenseStart,
        licenseEnd: formData.licenseEnd
      }
      saveMetaMap()
    }
    await loadPageData()
    ElMessage.success('新增成功')
  } else if (editingId.value) {
    await updateCanteenOrg(editingId.value, {
      name: formData.name,
      parent_id: formData.parentId
    })
    canteenMetaMap.value[editingId.value] = {
      manager: formData.manager,
      phone: formData.phone,
      address: formData.address,
      licenseUrl: formData.licenseUrl,
      licenseStart: formData.licenseStart,
      licenseEnd: formData.licenseEnd
    }
    saveMetaMap()
    await loadPageData()
    ElMessage.success('编辑成功')
  }

  dialogVisible.value = false
}

onMounted(() => {
  loadPageData()
})
</script>

<style scoped>
.org-page {
  padding: 16px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 14px;
}

.content-card {
  background: #fff;
  border: 1px solid #ebeef5;
  display: grid;
  grid-template-columns: 240px 1fr;
  min-height: 640px;
}

.left-tree {
  background: #4f8fe9;
  padding: 12px;
  color: #fff;
}

.add-btn {
  width: 100%;
  margin-bottom: 12px;
}

.left-tree :deep(.el-tree) {
  background: transparent;
  color: #fff;
}

.left-tree :deep(.el-tree-node__label) {
  color: #fff;
}

.left-tree :deep(.el-tree-node__content:hover),
.left-tree :deep(.el-tree-node:focus > .el-tree-node__content) {
  background: rgba(255, 255, 255, 0.18);
}

.left-tree :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: rgba(255, 255, 255, 0.28);
}

.left-tree :deep(.el-tree-node__expand-icon) {
  color: #fff;
}

.left-tree :deep(.el-tree-node__expand-icon.is-leaf) {
  color: rgba(255, 255, 255, 0.7);
}

.right-table {
  padding: 12px 14px;
}

.license-thumb {
  width: 62px;
  height: 42px;
  object-fit: cover;
  border: 1px solid #dcdfe6;
}

.license-upload {
  border: 1px solid #ebeef5;
  padding: 12px;
  width: 100%;
}

.license-preview {
  width: 210px;
  height: 130px;
  object-fit: cover;
  border: 1px solid #dcdfe6;
}

.license-empty {
  width: 210px;
  height: 130px;
  border: 1px dashed #dcdfe6;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.upload-actions {
  margin-top: 8px;
}

.date-range-box {
  display: grid;
  grid-template-columns: 24px 1fr;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.range-label {
  color: #606266;
}
</style>
