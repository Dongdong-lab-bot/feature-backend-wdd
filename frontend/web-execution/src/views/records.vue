<template>
  <div class="app-container">
    <div class="header-container">
      <div class="page-title">食安指数处理记录</div>
      <div class="filter-container">
        <div class="filter-item">
          <span class="filter-label">起止日期</span>
          <el-date-picker
            v-model="startDate"
            type="date"
            placeholder="开始日期"
            style="width: 140px"
            value-format="YYYY-MM-DD"
          />
          <span class="separator">-</span>
          <el-date-picker
            v-model="endDate"
            type="date"
            placeholder="结束日期"
            style="width: 140px"
            value-format="YYYY-MM-DD"
          />
        </div>
        
        <div class="filter-item">
          <span class="filter-label">食堂</span>
          <el-select v-model="selectedCanteen" placeholder="请选择食堂" style="width: 140px">
            <el-option label="武岗一中一食堂" value="武岗一中一食堂" />
            <el-option label="武岗一中二食堂" value="武岗一中二食堂" />
          </el-select>
        </div>

        <div class="filter-item">
          <span class="filter-label">搜索</span>
          <el-input
            v-model="searchText"
            placeholder=""
            style="width: 200px"
          />
        </div>
      </div>
    </div>

    <div class="table-container">
      <el-table :data="paginatedData" v-loading="loading" style="width: 100%" :header-cell-style="{ background: '#f5f7fa', color: '#606266' }">
        <el-table-column prop="cafeteria" label="提交食堂" min-width="160" />
        <el-table-column prop="submitter" label="提交人" min-width="100" />
        <el-table-column prop="problem" label="处理问题" min-width="180" />
        <el-table-column prop="handled" label="是否处理" min-width="100">
          <template #default="scope">
            {{ scope.row.handled ? '是' : '否' }}
          </template>
        </el-table-column>
        <el-table-column prop="date" label="提交日期" min-width="120" />
        <el-table-column prop="status" label="状态" min-width="120" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button link type="primary" size="small" @click="handleView(scope.row)">查看</el-button>
            
            <template v-if="scope.row.problem.includes('晨检')">
               <el-button link type="primary" size="small" @click="handleDownload(scope.row)">下载</el-button>
            </template>
            <template v-else>
               <el-button link type="primary" size="small" @click="handleCancel(scope.row)">取消</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        background
        prev-text="上一项"
        next-text="下一项"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getLedgerInstances } from '@/api/ledger'

// Filters
const startDate = ref('2026.1.12')
const endDate = ref('2026.2.23')
const selectedCanteen = ref('武岗一中一食堂')
const searchText = ref('')

// Pagination
const currentPage = ref(1)
const pageSize = ref(10)
const loading = ref(false)

// Mock Data
interface Record {
  id: number
  cafeteria: string
  submitter: string
  problem: string
  handled: boolean
  date: string
  status: string
}

const tableData = ref<Record[]>([])
const fallbackData: Record[] = [
  { id: 1, cafeteria: '武岗一中一食堂', submitter: '张三', problem: '晨检问题处理+3分', handled: true, date: '2020-05-24', status: '正常' },
  { id: 2, cafeteria: '武岗一中一食堂', submitter: '/', problem: '晨检问题处理+3分', handled: false, date: '2020-05-24', status: '超期自动修复' },
  { id: 3, cafeteria: '武岗一中一食堂', submitter: '王五', problem: '完成周排查整改+3分', handled: true, date: '2020-05-24', status: '正常' },
  { id: 4, cafeteria: '武岗一中一食堂', submitter: '张三', problem: '完成周排查整改+3分', handled: true, date: '2020-05-24', status: '正常' },
  { id: 5, cafeteria: '武岗一中一食堂', submitter: '张三', problem: '完成周排查整改+3分', handled: true, date: '2020-05-24', status: '正常' },
  { id: 6, cafeteria: '武岗一中一食堂', submitter: '张三', problem: '完成周排查整改+3分', handled: true, date: '2020-04-15', status: '正常' },
  { id: 7, cafeteria: '武岗一中一食堂', submitter: '张三', problem: '完成周排查整改+3分', handled: true, date: '2020-04-24', status: '正常' },
  { id: 8, cafeteria: '武岗一中一食堂', submitter: '张三', problem: '完成周排查整改+3分', handled: true, date: '2020-04-24', status: '正常' },
  { id: 9, cafeteria: '武岗一中一食堂', submitter: '张三', problem: '完成周排查整改+3分', handled: true, date: '2020-04-24', status: '正常' },
  { id: 10, cafeteria: '武岗一中一食堂', submitter: '张三', problem: '完成周排查整改+3分', handled: true, date: '2020-04-24', status: '正常' }
]

const loadScoreRecords = async () => {
  loading.value = true
  try {
    const result = await getLedgerInstances({ page: 1, size: 200 })
    const records = Array.isArray(result?.records) ? result.records : []
    tableData.value = records.map((item) => ({
      id: item.id,
      cafeteria: `食堂${item.canteen_id || '-'}`,
      submitter: '系统提交',
      problem: item.id % 2 === 0 ? '晨检问题处理+3分' : '完成周排查整改+3分',
      handled: item.status !== 'PENDING',
      date: (item.created_at || '').slice(0, 10) || '-',
      status: item.status === 'PENDING' ? '超期自动修复' : '正常'
    }))
  } catch {
    tableData.value = fallbackData
    ElMessage.warning('食安指数记录接口不可用，已展示示例数据')
  } finally {
    loading.value = false
  }
}

const filteredData = computed(() => {
  return tableData.value.filter(item => {
    const matchCanteen = !selectedCanteen.value || item.cafeteria.includes(selectedCanteen.value)
    const matchSearch = !searchText.value || 
      item.cafeteria.includes(searchText.value) || 
      (item.submitter && item.submitter.includes(searchText.value))
    
    return matchCanteen && matchSearch
  })
})

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredData.value.slice(start, end)
})

const total = computed(() => filteredData.value.length)

const handlePageChange = (page: number) => {
  currentPage.value = page
}

const handleView = (row: Record) => {
  console.log('View', row)
  // Implement view logic
}

const handleDownload = (row: Record) => {
  ElMessage.success(`开始下载 ${row.problem}`)
}

const handleCancel = (row: Record) => {
  ElMessage.warning(`取消 ${row.id}`)
}

onMounted(() => {
  loadScoreRecords()
})
</script>

<style scoped>
.app-container {
  padding: 20px;
  background-color: #fff;
  min-height: calc(100vh - 40px);
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.page-title {
  font-size: 18px;
  color: #333;
}

.filter-container {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.separator {
  color: #606266;
  margin: 0 4px;
}

.table-container {
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

:deep(.el-pagination.is-background .el-pager li:not(.is-disabled).is-active) {
  background-color: #409eff;
  color: #fff;
}

:deep(.el-pagination.is-background .btn-prev),
:deep(.el-pagination.is-background .btn-next) {
  padding: 0 10px;
}
</style>