<template>
  <div class="app-container">
    <div class="header">
      <div class="title">周排查记录</div>
      <div class="filters">
        <div class="filter-item">
          <span class="label">起止日期</span>
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="-"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </div>
        <div class="filter-item">
          <span class="label">状态</span>
          <el-select v-model="filters.status" placeholder="请选择" style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="待整改" value="PENDING" />
            <el-option label="待审核" value="SUBMITTED" />
            <el-option label="已完成" value="COMPLETED" />
          </el-select>
        </div>
        <div class="filter-item">
          <span class="label">搜索</span>
          <el-input v-model="filters.keyword" placeholder="请输入关键词" style="width: 200px" />
        </div>
      </div>
    </div>

    <div class="table-container">
      <el-table :data="filteredData" v-loading="loading" style="width: 100%" header-cell-class-name="table-header">
        <el-table-column prop="canteen" label="提交食堂" min-width="100" show-overflow-tooltip />
        <el-table-column prop="submitter" label="提交人" min-width="100" align="center" />
        <el-table-column prop="form" label="提交表格" min-width="100" show-overflow-tooltip />
        <el-table-column prop="score" label="检查分数" min-width="100" align="center" />
        <el-table-column prop="redLine" label="红线问题数" min-width="110" align="center" />
        <el-table-column prop="yellowLine" label="黄线问题数" min-width="115" align="center" />
        <el-table-column prop="date" label="提交日期" min-width="120" align="center" />
        <el-table-column prop="status" label="状态" min-width="120" align="center">
          <template #default="{ row }">
            <span :class="getStatusClass(row.status)">{{ row.status }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="center">
          <template #default="scope">
            <el-button link type="primary" class="action-btn" @click="viewDetail(scope.row)">查看</el-button>
            <el-button link type="primary" class="action-btn" style="margin-left: 16px">取消</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { getWeeklyInspectionTasks, WeeklyTaskItem } from '@/api/inspection'
import { useUserStore } from '@/store/user'

interface WeeklyRecord {
  id: number
  canteen: string
  submitter: string
  form: string
  score: number
  redLine: number
  yellowLine: number
  date: string
  status: '待整改' | '待审核' | '已完成'
  rawStatus: string
}

const router = useRouter()
const userStore = useUserStore()
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const loading = ref(false)

const filters = reactive({
  dateRange: [] as string[],
  status: '',
  keyword: ''
})

const data = ref<WeeklyRecord[]>([])

const statusLabelMap: Record<string, string> = {
  PENDING: '待整改',
  SUBMITTED: '待审核',
  REJECTED: '待整改',
  RECTIFIED: '待审核',
  COMPLETED: '已完成',
}

const toWeeklyRecord = (item: WeeklyTaskItem): WeeklyRecord => {
  return {
    id: item.task_id,
    canteen: item.canteen_name || '-',
    submitter: item.executor_name || '-',
    form: item.template_name || '周排查检查表',
    score: item.total_score ?? 0,
    redLine: item.red_line_count ?? item.red_line_issues ?? 0,
    yellowLine: item.yellow_line_count ?? 0,
      date: (item.submission_date || item.business_date || '').slice(0, 10) || '-',
    status: (statusLabelMap[item.status] || '待整改') as WeeklyRecord['status'],
    rawStatus: String(item.status || '').toLowerCase()
  }
}

const loadWeeklyRecords = async () => {
  loading.value = true
  try {
    const date = filters.dateRange.length > 0 ? filters.dateRange[0] : undefined
    const result = await getWeeklyInspectionTasks({
      page: currentPage.value,
      page_size: pageSize.value,
      status: filters.status || undefined,
      start_date: date,
      canteen_id: userStore.userInfo?.orgId || undefined
    })
    const records = Array.isArray(result?.list) ? result.list : []
    data.value = records.map(toWeeklyRecord)
    total.value = Number(result?.total || 0)
  } catch {
    data.value = []
    total.value = 0
    ElMessage.warning('周排查接口暂不可用，请稍后重试')
  } finally {
    loading.value = false
  }
}

const filteredData = computed(() => {
  const pendingSet = new Set(['pending', 'rejected'])
  const auditSet = new Set(['submitted', 'rectified'])
  return data.value.filter(item => {
    if (filters.keyword) {
      const kw = filters.keyword.toLowerCase()
      const match = item.canteen.toLowerCase().includes(kw) ||
                    item.submitter.toLowerCase().includes(kw) ||
                    item.form.toLowerCase().includes(kw)
      if (!match) return false
    }
    if (filters.status) {
      if (filters.status === 'PENDING' && !pendingSet.has(item.rawStatus)) return false
      else if (filters.status === 'SUBMITTED' && !auditSet.has(item.rawStatus)) return false
      else if (filters.status === 'COMPLETED' && item.rawStatus !== 'completed') return false
    }
    if (filters.dateRange && filters.dateRange.length === 2) {
      const itemDate = new Date(item.date).getTime()
      const startDate = new Date(filters.dateRange[0]).getTime()
      const endDate = new Date(filters.dateRange[1]).getTime()
      if (itemDate < startDate || itemDate > endDate) return false
    }
    return true
  })
})

const getStatusClass = (status: string) => {
  if (status === '待整改') return 'status-pending'
  if (status === '待审核') return 'status-submitted'
  if (status === '已完成') return 'status-done'
  return 'status-pending'
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadWeeklyRecords()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadWeeklyRecords()
}

const viewDetail = (row: WeeklyRecord) => {
  router.push({ path: '/weekly/details', query: { id: String(row.id) } })
}

onMounted(() => {
  loadWeeklyRecords()
})
</script>

<style scoped>
.app-container {
  padding: 20px;
  background-color: #fff;
  height: 100%;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.title {
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.filters {
  display: flex;
  align-items: center;
  gap: 20px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.label {
  font-size: 14px;
  color: #333;
}

.table-container {
  background: #fff;
}

:deep(.table-header) {
  background-color: #f5f7fa !important;
  color: #333;
  font-weight: 500;
}

.action-btn {
  font-size: 14px;
}

.status-pending {
  color: #f56c6c;
}

.status-submitted {
  color: #e6a23c;
}

.status-done {
  color: #67c23a;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
