<template>
  <div class="app-container">
    <!-- 1. 顶部搜索与操作栏 -->
    <div class="filter-container">
      <el-form :inline="true" :model="queryParams" class="demo-form-inline">
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
          <el-select v-model="queryParams.canteen" placeholder="请选择" style="width: 150px">
            <el-option label="全部" value="" />
            <el-option label="武岗一中一食堂" value="武岗一中一食堂" />
            <el-option label="武岗实验中学一食堂" value="武岗实验中学一食堂" />
            <el-option label="城东机关幼儿园食堂" value="城东机关幼儿园食堂" />
          </el-select>
        </el-form-item>
        <el-form-item label="台账">
          <el-select v-model="queryParams.ledgerType" placeholder="请选择" style="width: 150px">
            <el-option label="全部" value="" />
            <el-option label="留样台账" value="留样台账" />
            <el-option label="紫外线消毒台账" value="紫外线消毒台账" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input v-model="queryParams.keyword" placeholder="请输入关键字" style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 2. 表格区域 -->
    <el-table
      :data="messages"
      v-loading="loading"
      style="width: 100%"
      :header-cell-style="{ background: '#F5F7FA', color: '#606266' }"
    >
      <el-table-column prop="canteen" label="提交食堂" align="center" width="180" />
      <el-table-column prop="device" label="设备" align="center" />
      <el-table-column prop="data" label="设备数据" align="center" />
      <el-table-column prop="linked" label="是否已关联电子台账" align="center">
        <template #default="scope">
          <el-tag :type="scope.row.linked === '是' ? 'success' : 'info'" effect="plain">
            {{ scope.row.linked }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="date" label="提交日期" align="center" />
      <el-table-column prop="status" label="状态" align="center">
        <template #default="scope">
          <span :style="{ color: scope.row.status === '在线' ? '#67C23A' : '#F56C6C' }">
            {{ scope.row.status }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" width="150">
        <template #default="scope">
          <el-button link type="primary" @click="viewMsg(scope.$index, scope.row)">查看</el-button>
          <el-button link type="primary" @click="handleDownload(scope.row)">下载</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 3. 分页区域 -->
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

    <!-- 4. 查看详情弹窗 -->
    <el-dialog v-model="showView" title="消息详情" width="500px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="提交食堂">{{ currentMsg.canteen }}</el-descriptions-item>
        <el-descriptions-item label="设备">{{ currentMsg.device }}</el-descriptions-item>
        <el-descriptions-item label="设备数据">{{ currentMsg.data }}</el-descriptions-item>
        <el-descriptions-item label="关联台账">{{ currentMsg.linked }}</el-descriptions-item>
        <el-descriptions-item label="提交日期">{{ currentMsg.date }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ currentMsg.status }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showView = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { getLedgerInstances, type LedgerInstanceRecord } from '@/api/ledger'

interface DeviceMessageRow {
  id: string
  canteen: string
  device: string
  data: string
  linked: '是' | '否'
  date: string
  status: '在线' | '离线'
  rawStatus: string
}

// 查询参数
const queryParams = reactive({
  dateRange: [] as string[],
  canteen: '',
  ledgerType: '',
  keyword: ''
})

const loading = ref(false)

// 接口异常时的回退数据
const fallbackMessages: DeviceMessageRow[] = [
  { canteen: '武岗一中一食堂', device: 'AI 留样秤', data: '留样消息记录', linked: '是', date: '2020-05-24', status: '在线' },
  { canteen: '武岗实验中学一食堂', device: '智能消毒柜', data: '紫外线消毒消息记录', linked: '是', date: '2020-05-24', status: '在线' },
  { canteen: '城东机关幼儿园食堂', device: 'AI 留样秤', data: '留样消息记录', linked: '是', date: '2020-05-24', status: '在线' },
  { canteen: '武岗一中一食堂', device: 'AI 留样秤', data: '留样消息记录', linked: '是', date: '2020-05-24', status: '在线' },
  { canteen: '武岗一中一食堂', device: 'AI 留样秤', data: '留样消息记录', linked: '是', date: '2020-05-24', status: '在线' },
  { canteen: '武岗一中一食堂', device: 'AI 留样秤', data: '留样消息记录', linked: '是', date: '2020-04-15', status: '在线' },
  { canteen: '武岗一中一食堂', device: 'AI 留样秤', data: '留样消息记录', linked: '是', date: '2020-04-24', status: '在线' },
  { canteen: '武岗一中一食堂', device: 'AI 留样秤', data: '留样消息记录', linked: '是', date: '2020-04-24', status: '在线' },
  { canteen: '武岗一中一食堂', device: 'AI 留样秤', data: '留样消息记录', linked: '是', date: '2020-04-24', status: '在线' },
  { canteen: '武岗一中一食堂', device: 'AI 留样秤', data: '留样消息记录', linked: '是', date: '2020-04-24', status: '在线' }
].map((item, index) => ({
  id: `fallback-${index + 1}`,
  rawStatus: 'completed',
  ...item
}))

const messages = ref<DeviceMessageRow[]>([])

// 分页
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 详情弹窗
const showView = ref(false)
const currentMsg = ref<DeviceMessageRow | Record<string, never>>({})

const mapDeviceName = (templateTitle?: string): string => {
  if (!templateTitle) return '智能设备'
  if (templateTitle.includes('留样')) return 'AI 留样秤'
  if (templateTitle.includes('紫外线') || templateTitle.includes('消毒')) return '智能消毒柜'
  if (templateTitle.includes('体温') || templateTitle.includes('晨检')) return '手部晨检仪'
  return '智能设备'
}

const mapOnlineStatus = (ledgerStatus: string): '在线' | '离线' => {
  const onlineSet = new Set(['signed', 'archived', 'approved', 'completed'])
  return onlineSet.has(ledgerStatus.toLowerCase()) ? '在线' : '离线'
}

const mapLedgerRow = (item: LedgerInstanceRecord): DeviceMessageRow => {
  const titleText = item.template_title || '台账'
  const createdDate = (item.created_at || '').slice(0, 10)
  const statusText = (item.status || '').toString()

  return {
    id: String(item.id),
    canteen: '设备食堂',
    device: mapDeviceName(titleText),
    data: `${titleText.replace('台账', '') || titleText}消息记录`,
    linked: '是',
    date: createdDate || '-',
    status: mapOnlineStatus(statusText),
    rawStatus: statusText
  }
}

const fetchMessages = async () => {
  loading.value = true
  try {
    const result = await getLedgerInstances({
      page: page.value,
      size: pageSize.value
    })

    const sourceList = Array.isArray(result?.records) ? result.records : []
    let mapped = sourceList.map(mapLedgerRow)

    // 前端过滤（API 不支持这些参数）
    const keyword = queryParams.keyword.trim()
    const [startDate, endDate] = queryParams.dateRange || []
    if (keyword) {
      mapped = mapped.filter((item) => item.device.includes(keyword) || item.data.includes(keyword))
    }
    if (queryParams.canteen) {
      mapped = mapped.filter((item) => item.canteen === queryParams.canteen)
    }
    if (startDate && endDate) {
      mapped = mapped.filter((item) => {
        const d = new Date(item.date)
        return d >= new Date(startDate) && d <= new Date(endDate)
      })
    }

    messages.value = mapped
    total.value = typeof result?.total === 'number' ? result.total : mapped.length
  } catch {
    const keyword = queryParams.keyword.trim()
    let filtered = fallbackMessages.filter((msg) => {
      const matchKeyword = !keyword || msg.device.includes(keyword) || msg.data.includes(keyword)
      const matchCanteen = !queryParams.canteen || msg.canteen === queryParams.canteen
      const matchLedger = !queryParams.ledgerType || msg.data.includes(queryParams.ledgerType.replace('台账', ''))
      return matchKeyword && matchCanteen && matchLedger
    })

    if (queryParams.dateRange?.length === 2) {
      const [startDate, endDate] = queryParams.dateRange
      filtered = filtered.filter((msg) => {
        const d = new Date(msg.date)
        return d >= new Date(startDate) && d <= new Date(endDate)
      })
    }

    const start = (page.value - 1) * pageSize.value
    const end = start + pageSize.value
    messages.value = filtered.slice(start, end)
    total.value = filtered.length
    ElMessage.warning('台账接口暂不可用，当前展示示例数据')
  } finally {
    loading.value = false
  }
}

// 方法
const handleSearch = async () => {
  page.value = 1
  await fetchMessages()
  ElMessage.success('查询成功')
}

const viewMsg = (_index: number, row: DeviceMessageRow) => {
  currentMsg.value = row
  showView.value = true
}

const handleDownload = (row: DeviceMessageRow) => {
  ElMessage.success(`开始下载 ${row.device} 的数据记录`)
}

const handleCurrentChange = async (val: number) => {
  page.value = val
  await fetchMessages()
}

const handleSizeChange = async (val: number) => {
  pageSize.value = val
  page.value = 1
  await fetchMessages()
}

onMounted(() => {
  fetchMessages()
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
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>