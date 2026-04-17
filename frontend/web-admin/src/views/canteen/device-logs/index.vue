<template>
  <div class="app-container">
    <div class="filter-container">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="起止日期">
          <el-date-picker
            v-model="queryParams.dateRange"
            type="daterange"
            range-separator="-"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 240px"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="食堂">
          <el-select v-model="queryParams.canteenId" placeholder="请选择" style="width: 160px">
            <el-option label="全部" value="" />
            <el-option v-for="item in canteenOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="台账">
          <el-select v-model="queryParams.ledgerType" placeholder="请选择" style="width: 160px">
            <el-option label="全部" value="" />
            <el-option label="留样台账" value="留样台账" />
            <el-option label="晨检台账" value="晨检台账" />
            <el-option label="溯源台账" value="溯源台账" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input v-model="queryParams.keyword" placeholder="请输入关键字" style="width: 220px" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-table
      v-loading="loading"
      :data="messages"
      style="width: 100%"
      :header-cell-style="{ background: '#F5F7FA', color: '#606266' }"
    >
        <el-table-column prop="submitCanteen" label="提交食堂" min-width="170" />
        <el-table-column prop="deviceName" label="设备" min-width="110" />
        <el-table-column prop="deviceData" label="设备数据" min-width="140" />
        <el-table-column label="是否已关联电子台账" min-width="140">
          <template #default="scope">
            <el-tag :type="scope.row.isLinked ? 'success' : 'info'" effect="plain">
              {{ scope.row.isLinked ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="submitDate" label="提交日期" min-width="120" />
        <el-table-column label="状态" min-width="90">
          <template #default="scope">
            <span :class="scope.row.status === '在线' ? 'text-online' : 'text-offline'">{{ scope.row.status }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center">
          <template #default="scope">
            <template v-if="scope.row.isLinked">
              <el-button link type="primary" @click="handleView(scope.row)">查看</el-button>
              <el-button link type="primary" @click="handleDownload(scope.row)">下载</el-button>
            </template>
            <template v-else>
              <el-button link type="primary" @click="handleEdit(scope.row)">编辑</el-button>
              <el-button link type="primary" @click="handleCancel(scope.row)">取消</el-button>
            </template>
          </template>
        </el-table-column>
    </el-table>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 30, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <el-dialog v-model="showView" title="消息详情" width="500px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="提交食堂">{{ currentMsg.submitCanteen }}</el-descriptions-item>
        <el-descriptions-item label="设备">{{ currentMsg.deviceName }}</el-descriptions-item>
        <el-descriptions-item label="设备数据">{{ currentMsg.deviceData }}</el-descriptions-item>
        <el-descriptions-item label="关联台账">{{ currentMsg.isLinked ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="提交日期">{{ currentMsg.submitDate }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ currentMsg.status }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="showView = false">关闭</el-button>
      </template>
    </el-dialog>
      </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { getAllDepts, getLedgerInstanceList } from '@/api/canteen'

interface CanteenOption {
  id: number
  name: string
}

interface DeviceMessageItem {
  id: number
  submitCanteen: string
  canteenId: string
  deviceName: string
  deviceData: string
  ledgerType: string
  isLinked: boolean
  submitDate: string
  status: '在线' | '离线'
}

const loading = ref(false)
const canteenOptions = ref<CanteenOption[]>([])
const messages = ref<DeviceMessageItem[]>([])
const showView = ref(false)
const currentMsg = ref<DeviceMessageItem>({
  id: 0,
  submitCanteen: '',
  canteenId: '',
  deviceName: '',
  deviceData: '',
  ledgerType: '',
  isLinked: false,
  submitDate: '',
  status: '在线'
})

const queryParams = reactive({
  dateRange: [] as string[],
  canteenId: '',
  ledgerType: '',
  keyword: ''
})

const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const devicePool = ['AI留样秤', '智能晨检仪', '进销存溯源秤', '留样冰箱', 'AI盒子8路']
const dataPool = ['留样消息记录', '晨检消息记录', '溯源消息记录']

const inRange = (date: string, start: string, end: string) => {
  if (!date || !start || !end) return true
  return date >= start && date <= end
}

const allMappedRows = ref<DeviceMessageItem[]>([])

const loadCanteens = async () => {
  try {
    const res: any = await getAllDepts()
    const rows = res?.data?.records || []
    canteenOptions.value = rows
      .filter((item: any) => item.org_type === 'CANTEEN')
      .map((item: any) => ({ id: item.id, name: item.name }))
  } catch {
    canteenOptions.value = []
  }
}

const resolveCanteenName = (id: number) => {
  return canteenOptions.value.find((item) => item.id === id)?.name || `食堂${id || '-'}`
}

const loadMessages = async () => {
  loading.value = true
  try {
    const res: any = await getLedgerInstanceList({ page: 1, size: 300 })
    const rows = res?.data?.records || []
    const mapped = rows.map((row: any, idx: number) => {
      const canteenId = Number(row.canteen_id || 0)
      return {
        id: row.id,
        submitCanteen: resolveCanteenName(canteenId),
        canteenId: String(canteenId),
        deviceName: devicePool[idx % devicePool.length],
        deviceData: dataPool[idx % dataPool.length],
        ledgerType: dataPool[idx % dataPool.length].replace('消息记录', '台账'),
        isLinked: idx % 4 !== 0,
        submitDate: String(row.created_at || '').slice(0, 10) || '2020-05-24',
        status: idx % 5 === 0 ? '离线' : '在线'
      }
    })
    allMappedRows.value = mapped
    applyFiltersAndPagination()
  } catch {
    allMappedRows.value = []
    applyFiltersAndPagination()
  } finally {
    loading.value = false
  }
}

const applyFiltersAndPagination = () => {
  const [startDate, endDate] = queryParams.dateRange || []
  let filtered = allMappedRows.value.filter((item) => {
    const matchCanteen = !queryParams.canteenId || item.canteenId === queryParams.canteenId
    const matchLedger = !queryParams.ledgerType || item.ledgerType === queryParams.ledgerType
    const matchDate = !startDate || !endDate || inRange(item.submitDate, startDate, endDate)
    const keyword = queryParams.keyword.trim()
    const matchKeyword =
      !keyword ||
      item.submitCanteen.includes(keyword) ||
      item.deviceName.includes(keyword) ||
      item.deviceData.includes(keyword)
    return matchCanteen && matchLedger && matchDate && matchKeyword
  })

  total.value = filtered.length
  const start = (page.value - 1) * pageSize.value
  const end = start + pageSize.value
  messages.value = filtered.slice(start, end)
}

const handleSearch = () => {
  page.value = 1
  applyFiltersAndPagination()
  ElMessage.success('查询成功')
}

const handleView = (row: DeviceMessageItem) => {
  currentMsg.value = row
  showView.value = true
}

const handleDownload = (row: DeviceMessageItem) => {
  const content = `记录ID,提交食堂,设备,设备数据,提交日期\n${row.id},${row.submitCanteen},${row.deviceName},${row.deviceData},${row.submitDate}`
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `设备消息记录_${row.id}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

const handleEdit = (row: DeviceMessageItem) => {
  ElMessage.info(`编辑记录 #${row.id}`)
}

const handleCancel = (row: DeviceMessageItem) => {
  ElMessage.warning(`已取消记录 #${row.id}`)
}

const handleCurrentChange = (value: number) => {
  page.value = value
  applyFiltersAndPagination()
}

const handleSizeChange = (value: number) => {
  pageSize.value = value
  page.value = 1
  applyFiltersAndPagination()
}

onMounted(async () => {
  await loadCanteens()
  await loadMessages()
})
</script>

<style scoped>
.app-container {
  padding: 20px;
  background-color: #fff;
  min-height: calc(100vh - 84px);
}

.filter-container {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.text-online {
  color: #3f8cff;
}

.text-offline {
  color: #ff4d4f;
}
</style>
