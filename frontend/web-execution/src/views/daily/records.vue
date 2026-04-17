<template>
  <div class="record-view">
    <header class="rv-header">
      <div class="title">日管控记录</div>
      <div class="controls">
        <div class="control-item">
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
        <div class="control-item">
          <span class="label">状态</span>
          <el-select v-model="filters.status" placeholder="全部状态" style="width: 120px">
            <el-option label="全部状态" value="" />
            <el-option label="待提交" value="待提交" />
            <el-option label="待审核" value="待审核" />
            <el-option label="待整改" value="待整改" />
            <el-option label="已整改" value="已整改" />
            <el-option label="已完成" value="已完成" />
          </el-select>
        </div>
        <div class="control-item">
          <span class="label">搜索</span>
          <el-input
            v-model="filters.keyword"
            placeholder="搜索提交食堂 / 提交人 / 表格"
            style="width: 220px"
          />
        </div>
      </div>
    </header>

    <div class="table-container">
      <el-table
        :data="pagedData"
        v-loading="loading"
        style="width: 100%"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }
      ">
        <el-table-column prop="canteen" label="提交食堂" min-width="100" show-overflow-tooltip />
        <el-table-column prop="submitter" label="提交人" min-width="120" />
        <el-table-column prop="form" label="提交表格" min-width="100" show-overflow-tooltip />
        <el-table-column prop="completed" label="日管控完成项" min-width="180" align="center" />
        <el-table-column prop="date" label="提交日期" min-width="120" align="center" />
        <el-table-column prop="status" label="状态" min-width="100" align="center">
          <template #default="scope">
            <span :class="getStatusClass(scope.row.status)">{{ scope.row.status }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="150" align="center">
          <template #default="scope">
            <el-button link type="primary" @click="view(scope.row)">查看</el-button>
            <el-button link type="primary" @click="cancel(scope.row)">取消</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <div class="empty">暂无记录</div>
        </template>
      </el-table>
    </div>

    <footer class="rv-footer">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        layout="prev, pager, next"
        :total="total"
      />
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { getDailyControlTasks } from '@/api/inspection'

interface DailyRecord {
  id: number
  canteen: string
  submitter: string
  form: string
  completed: string
  date: string
  status: '待提交' | '待审核' | '待整改' | '已整改' | '已完成' | string
}

const statusMap: Record<string, string> = {
  PENDING: '待提交',
  SUBMITTED: '待审核',
  REJECTED: '待整改',
  RECTIFIED: '已整改',
  COMPLETED: '已完成',
  SIGNED: '已完成',
  ARCHIVED: '已完成',
}

const loading = ref(false)
const data = ref<DailyRecord[]>([])
const router = useRouter()

const filters = reactive({
  keyword: '',
  status: '',
  dateRange: [] as string[]
})
const page = ref(1)
const pageSize = ref(10)

const statusToApi: { [key: string]: string } = {
  '待提交': 'PENDING',
  '待审核': 'SUBMITTED',
  '待整改': 'REJECTED',
  '已整改': 'RECTIFIED',
  '已完成': 'COMPLETED',
}

const loadRecords = async () => {
  loading.value = true
  try {
    const result = await getDailyControlTasks({
      page: 1,
      page_size: 100,
      status: filters.status ? statusToApi[filters.status] : undefined,
      start_date: filters.dateRange.length ? filters.dateRange[0] : undefined
    })

    const records = Array.isArray(result?.list) ? result.list : []
    data.value = records.map((item) => ({
      id: item.task_id,
      canteen: item.canteen_name || '-',
      submitter: item.submitter_name || '-',
      form: item.template_name || '日管控检查表',
      completed: item.completion_progress ?? '-',
      date: (item.submission_date || '').slice(0, 10) || '-',
      status: statusMap[item.status] || item.status_text || item.status || '-'
    }))
  } catch {
    data.value = []
    ElMessage.warning('日管控记录接口不可用，请稍后重试')
  } finally {
    loading.value = false
  }
}

const filtered = computed(() => {
  const kw = filters.keyword.trim().toLowerCase()
  return data.value.filter((r: DailyRecord) => {
    const matchKw = !kw || [r.canteen, r.submitter, r.form].join(' ').toLowerCase().includes(kw)
    const matchStatus = !filters.status || r.status === filters.status
    // 简单的日期范围过滤逻辑 (如果需要)
    let matchDate = true
    if (filters.dateRange && filters.dateRange.length === 2) {
       const d = new Date(r.date).getTime()
       const start = new Date(filters.dateRange[0]).getTime()
       const end = new Date(filters.dateRange[1]).getTime()
       matchDate = d >= start && d <= end
    }
    return matchKw && matchStatus && matchDate
  })
})

const total = computed(() => filtered.value.length)
const pagedData = computed(() => filtered.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value))

function view(row: DailyRecord) {
  router.push({ path: '/daily/details', query: { id: String(row.id) } })
}

function cancel(row: DailyRecord) {
  ElMessage.info(`取消操作：${row.id}`)
}

function getStatusClass(status: string) {
  if (status === '待提交') return 'status-pending'
  if (status === '待审核') return 'status-submitted'
  if (status === '待整改') return 'status-review'
  if (status === '已整改') return 'status-fixed'
  if (status === '已完成') return 'status-done'
  return 'status-pending'
}

onMounted(() => {
  loadRecords()
})
</script>

<style scoped>
.record-view {
  font-family: Inter, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #333;
  padding: 20px;
  background-color: #fff;
  min-height: 100%;
}

.rv-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  background: #fff;
  padding: 10px 0;
}

.rv-header .title {
  font-size: 16px;
  font-weight: bold;
  margin-right: auto;
}

.controls {
  display: flex;
  align-items: center;
  gap: 20px;
}

.control-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-item .label {
  font-size: 14px;
  color: #606266;
}

.table-container {
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.rv-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.empty {
  text-align: center;
  color: #909399;
  padding: 30px;
}

/* 简单的状态文本颜色示例 */
:deep(.el-button--primary.is-link) {
  color: #409eff;
}

.status-pending {
  color: #909399;
}

.status-submitted {
  color: #e6a23c;
}

.status-review {
  color: #f56c6c;
}

.status-fixed {
  color: #409eff;
}

.status-done {
  color: #67c23a;
}
</style>
