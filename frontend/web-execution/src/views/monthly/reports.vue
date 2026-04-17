<template>
  <div class="app-container">
    <div class="content-card">
      <div class="header">
        <div class="title">月调度报告记录</div>
      </div>

      <!-- 搜索区域 -->
      <div class="search-section">
        <div class="search-box">
          <el-input
            v-model="searchQuery"
            placeholder="请输入要查询的流水号或工作名称/文号"
            class="search-input"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          />
          <el-button type="primary" class="search-btn" @click="handleSearch">精确查询</el-button>
        </div>
      </div>

      <!-- 表格 -->
      <div class="table-container">
        <el-table
          :data="pagedData"
          v-loading="loading"
          style="width: 100%"
          @selection-change="handleSelectionChange"
          header-row-class-name="table-header-row"
          :cell-style="{ padding: '18px 0' }"
        >
          <el-table-column type="selection" width="55" align="center" />
          <el-table-column prop="id" label="#" width="80" align="center" />
          <el-table-column prop="name" label="报告名称" min-width="120" />
          <el-table-column prop="reporter" label="报告人" min-width="120" align="center" />
          <el-table-column label="系统报告" min-width="120" align="center">
            <template #default="scope">
              <el-button link type="primary" class="view-link" @click="viewSystemReport(scope.row)">查看</el-button>
            </template>
          </el-table-column>
          <el-table-column prop="time" label="报告时间" min-width="200" align="center" />
          <el-table-column label="线下报告" min-width="120" align="center">
            <template #default="scope">
              <el-button link type="primary" class="view-link" @click="viewOfflineReport(scope.row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getMonthlyReports } from '@/api/inspection'

interface MonthlyReportRow {
  id: number
  name: string
  reporter: string
  time: string
}

// 搜索
const searchQuery = ref('')
const handleSearch = () => {
  currentPage.value = 1
}

const loading = ref(false)
const total = ref(0)

const tableData = ref<MonthlyReportRow[]>([])

const pad = (n: number) => String(n).padStart(2, '0')

const formatDateTime = (raw?: string): string => {
  if (!raw) return '-'
  const dt = new Date(raw)
  if (Number.isNaN(dt.getTime())) return raw
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}:${pad(dt.getSeconds())}`
}

const loadReports = async () => {
  loading.value = true
  try {
    const result = await getMonthlyReports({ page: currentPage.value, page_size: pageSize.value })
    const records = Array.isArray(result?.list) ? result.list : []
    tableData.value = records.map((item) => ({
      id: item.id,
      name: item.title || '-',
      reporter: item.reporter_name || '-',
      time: formatDateTime(item.report_time ?? undefined)
    }))
    total.value = Number(result?.total || tableData.value.length)
  } catch {
    tableData.value = []
    total.value = 0
    ElMessage.warning('月调度报告接口暂不可用，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 过滤逻辑
const filteredData = computed(() => {
  if (!searchQuery.value) return tableData.value
  const query = searchQuery.value.toLowerCase()
  return tableData.value.filter(item => 
    item.name.toLowerCase().includes(query) ||
    item.reporter.toLowerCase().includes(query) ||
    String(item.id).includes(query)
  )
})

// 分页逻辑
const currentPage = ref(1)
const pageSize = ref(10)

const pagedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredData.value.slice(start, end)
})

const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
  loadReports()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  loadReports()
}

// 表格选择
const multipleSelection = ref([])
const handleSelectionChange = (val: any) => {
  multipleSelection.value = val
}

const viewSystemReport = (_row: MonthlyReportRow) => {
  ElMessage.info('系统报告功能开发中')
}

const viewOfflineReport = (row: MonthlyReportRow) => {
  ElMessage.info(`线下报告查看：#${row.id}`)
}

onMounted(() => {
  loadReports()
})
</script>

<style scoped>
.app-container {
  padding: 20px;
  background-color: #f0f2f5;
  min-height: 100vh;
}

.content-card {
  background-color: #fff;
  border-radius: 4px;
  padding: 24px;
  min-height: 600px;
}

.header {
  margin-bottom: 24px;
}

.title {
  font-size: 18px;
  color: #333;
  font-weight: normal; /* Match screenshot which looks regular/medium */
}

.search-section {
  margin-bottom: 20px;
  background-color: #fcfcfc; /* Light bg for search area if needed, but screenshot shows white */
  background-color: #fff;
  border-bottom: 1px solid #ebeef5; /* Optional separator */
  padding-bottom: 20px;
}

.search-box {
  display: flex;
  align-items: center;
}

.search-input {
  width: 300px;
  margin-right: 10px;
}

.search-btn {
  background-color: #409eff;
  border-color: #409eff;
  padding: 8px 20px;
  font-size: 14px;
  border-radius: 2px; /* Screenshot buttons look slightly squared */
}

.table-container {
  margin-bottom: 20px;
}

:deep(.el-table__row) {
  height: 58px;
}

:deep(.table-header-row th) {
  background-color: #f5f7fa !important;
  color: #606266;
  font-weight: bold;
}

.view-link {
  font-size: 14px;
  font-weight: normal;
}

.pagination-container {
  display: flex;
  justify-content: flex-end; /* Screenshot usually aligns right, or center */
  justify-content: center; /* Keeping center as per previous code, or right is standard */
  margin-top: 30px;
}
</style>
