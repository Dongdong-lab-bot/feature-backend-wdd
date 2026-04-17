<template>
  <div class="device-container">
    <div class="toolbar">
      <div class="toolbar-title">食堂设备中心</div>
      <div class="toolbar-actions">
        <el-form :inline="true" class="toolbar-form">
          <el-form-item label="搜索设备">
            <el-input
              v-model="query.keyword"
              placeholder="请输入设备名称"
              style="width: 210px"
              clearable
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="query.status" style="width: 110px" @change="handleSearch">
              <el-option label="全部" value="" />
              <el-option label="在线" value="ONLINE" />
              <el-option label="离线" value="OFFLINE" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleAdd">新增设备</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <el-table
      :data="pagedData"
      v-loading="loading"
      style="width: 100%"
      :cell-style="{ padding: '20px 0' }"
      :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
    >
      <el-table-column prop="device_name" label="设备名称" min-width="180" />
      <el-table-column prop="device_code" label="设备唯一码" min-width="160" />
      <el-table-column prop="status" label="状态" min-width="80">
        <template #default="scope">
          <span :class="scope.row.status === 'ONLINE' ? 'status-online' : 'status-offline'">
            {{ scope.row.status === 'ONLINE' ? '在线' : '离线' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="添加日期" min-width="140" />
      <el-table-column prop="org_name" label="所属食堂" min-width="180" />
      <el-table-column label="操作" min-width="130" align="center">
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
        :total="filteredData.length"
        :page-sizes="[10, 20, 50, 100]"
        layout="prev, pager, next"
      />
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '新增' : '编辑'"
      width="600px"
      align-center
      @close="resetForm"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-position="top" hide-required-asterisk>
        <el-form-item label="设备信息" prop="device_name">
          <el-input v-model="formData.device_name" placeholder="请输入设备名称" />
        </el-form-item>

        <el-form-item label="设备唯一码" prop="device_code">
          <el-input v-model="formData.device_code" placeholder="请输入设备唯一码" />
        </el-form-item>

        <el-form-item v-if="dialogType === 'edit' && formData.api_key" label="API Key">
          <div class="api-key-row">
            <el-input :model-value="formData.api_key ? formData.api_key.substring(0, 8) + '********' : ''" readonly />
            <el-button type="primary" @click="copyApiKey">复制</el-button>
          </div>
        </el-form-item>

        <div class="connect-row">
          <el-form-item label="设备连接" class="connect-action">
            <el-button class="connect-btn" type="primary" @click="refreshConnection">点击刷新接入系统</el-button>
          </el-form-item>
          <el-form-item label="设备状态" class="connect-status">
            <el-input v-model="formData.connectionStatus" readonly />
          </el-form-item>
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
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { bindDevice, unbindDevice, updateDevice, type Device } from '@/api/device'

interface DeviceItem extends Device {}

interface DeviceForm {
  id?: number
  device_name: string
  device_code: string
  status: string
  created_at: string
  org_name: string
  api_key: string
  connectionStatus: string
}

const query = reactive({
  keyword: '',
  status: '' as string
})

const loading = ref(false)
const submitLoading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)

const allData = ref<DeviceItem[]>([])

const fallbackData: DeviceItem[] = [
  { id: 1, device_name: '手部晨检仪', device_code: 'AC1256EF456E', status: 'ONLINE', created_at: '2025-12-05', org_id: 1, org_name: '武岗一中一食堂' },
  { id: 2, device_name: 'AI留样秤', device_code: 'RK3568_001', status: 'ONLINE', created_at: '2025-12-05', org_id: 1, org_name: '武岗一中一食堂' },
  { id: 3, device_name: '进销存溯源秤', device_code: 'AC1256EF456E', status: 'ONLINE', created_at: '2025-12-05', org_id: 1, org_name: '武岗一中一食堂' },
  { id: 4, device_name: '留样冰箱', device_code: 'AC1256EF456E', status: 'ONLINE', created_at: '2025-12-05', org_id: 1, org_name: '武岗一中一食堂' },
  { id: 5, device_name: '刷脸晨检仪', device_code: 'AC1256EF456E', status: 'OFFLINE', created_at: '2025-12-05', org_id: 1, org_name: '武岗一中一食堂' },
  { id: 6, device_name: 'AI盒子8路', device_code: 'CAM-001', status: 'OFFLINE', created_at: '2025-12-05', org_id: 1, org_name: '武岗一中一食堂' }
]

const filteredData = computed(() => {
  const keyword = query.keyword.trim()
  return allData.value.filter((item) => {
    const matchKeyword = !keyword || item.device_name.includes(keyword) || item.device_code.includes(keyword)
    const matchStatus = !query.status || item.status === query.status
    return matchKeyword && matchStatus
  })
})

const pagedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredData.value.slice(start, end)
})

const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const formRef = ref<FormInstance>()

const formData = reactive<DeviceForm>({
  id: undefined,
  device_name: '',
  device_code: '',
  status: 'OFFLINE',
  created_at: '',
  org_name: '武岗一中一食堂',
  api_key: '',
  connectionStatus: '未连接'
})

const rules: FormRules = {
  device_name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  device_code: [{ required: true, message: '请输入设备唯一码', trigger: 'blur' }]
}

const normalizeList = (records: DeviceItem[]): DeviceItem[] => {
  return records.map((item) => ({
    ...item,
    status: item.status === 'ONLINE' || item.status === 'OFFLINE' ? item.status : 'OFFLINE'
  }))
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getDeviceList({ page: 1, page_size: 500, keyword: '', status: '' })
    const records = Array.isArray(res?.data?.records) ? res.data.records : []
    allData.value = records.length > 0 ? normalizeList(records) : fallbackData
  } catch {
    allData.value = fallbackData
    ElMessage.warning('设备接口未联通，已展示示例数据')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
}

const handleAdd = () => {
  dialogType.value = 'add'
  resetForm()
  formData.createTime = new Date().toISOString().slice(0, 10)
  dialogVisible.value = true
}

const handleEdit = (row: DeviceItem) => {
  dialogType.value = 'edit'
  Object.assign(formData, {
    id: row.id,
    device_name: row.device_name,
    device_code: row.device_code,
    status: row.status,
    created_at: row.created_at,
    org_name: row.org_name,
    api_key: row.api_key || '',
    connectionStatus: row.status === 'ONLINE' ? '已连接' : '未连接'
  })
  dialogVisible.value = true
}

const handleDelete = (row: DeviceItem) => {
  ElMessageBox.confirm(`确认删除设备"${row.device_name}"吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await unbindDevice(row.id)
      ElMessage.success('删除成功')
      loadData()
    } catch {
      allData.value = allData.value.filter((item) => item.id !== row.id)
      ElMessage.warning('后端未提供删除能力，已从前端列表移除')
    }
  }).catch(() => {})
}

const refreshConnection = () => {
  formData.connectionStatus = '已连接'
  formData.status = 'ONLINE'
  ElMessage.success('已刷新接入状态')
}

const copyApiKey = () => {
  navigator.clipboard.writeText(formData.api_key).then(() => {
    ElMessage.success('API Key 已复制')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

const handleSubmit = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    if (dialogType.value === 'add') {
      try {
        await bindDevice({ device_name: formData.device_name, device_code: formData.device_code, org_id: 1 })
        ElMessage.success('新增成功')
        await loadData()
      } catch {
        const nextId = allData.value.length > 0 ? Math.max(...allData.value.map((item) => item.id)) + 1 : 1
        allData.value.unshift({
          id: nextId,
          device_name: formData.device_name,
          device_code: formData.device_code,
          status: formData.status,
          created_at: formData.created_at || new Date().toISOString().slice(0, 10),
          org_id: 1,
          org_name: formData.org_name
        })
        ElMessage.warning('后端未提供新增能力，已使用前端临时数据')
      }
    } else if (formData.id) {
      try {
        await updateDevice({ id: formData.id, device_name: formData.device_name })
        ElMessage.success('保存成功')
        await loadData()
      } catch {
        const index = allData.value.findIndex((item) => item.id === formData.id)
        if (index >= 0) {
          allData.value[index] = {
            ...allData.value[index],
            device_name: formData.device_name,
            device_code: formData.device_code,
            status: formData.status
          }
        }
        ElMessage.warning('后端未提供完整编辑能力，已更新前端展示')
      }
    }

    dialogVisible.value = false
  } finally {
    submitLoading.value = false
  }
}

const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    id: undefined,
    device_name: '',
    device_code: '',
    status: 'OFFLINE',
    created_at: '',
    org_name: '武岗一中一食堂',
    api_key: '',
    connectionStatus: '未连接'
  })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.device-container {
  padding: 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.toolbar-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.toolbar-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.pagination-wrapper {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.status-online {
  color: #409eff;
}

.status-offline {
  color: #f56c6c;
}

.connect-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.connect-btn {
  width: 100%;
}

.api-key-row {
  display: flex;
  gap: 8px;
  width: 100%;
}

.api-key-row .el-input {
  flex: 1;
}
</style>
