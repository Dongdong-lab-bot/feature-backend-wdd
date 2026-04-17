<template>
  <div class="app-container">
    <div class="filter-container">
      <div class="filter-left">
        <span class="page-title">视频集控记录</span>
      </div>
      <div class="filter-right">
        <div class="filter-item">
          <span class="label">起止日期</span>
          <el-date-picker
            v-model="dateRange"
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
          <el-select v-model="statusFilter" placeholder="请选择" clearable style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="待整改" value="待整改" />
            <el-option label="已改待审" value="已改待审" />
            <el-option label="整改成功" value="整改成功" />
          </el-select>
        </div>
        <div class="filter-item">
          <span class="label">搜索</span>
          <el-input
            v-model="searchText"
            placeholder="请输入关键字"
            style="width: 200px"
            :prefix-icon="Search"
          />
        </div>
      </div>
    </div>

    <div class="table-wrapper">
      <el-table
        :data="paginatedData"
        v-loading="loading"
        style="width: 100%"
        border
        stripe
        header-row-class-name="custom-table-header"
      >
        <el-table-column prop="canteen" label="提交食堂" min-width="150" align="center" />
        <el-table-column prop="submitter" label="提交人" min-width="100" align="center" />
        <el-table-column prop="tableType" label="提交表格" min-width="180" align="center" />
        <el-table-column prop="score" label="检查分数" min-width="100" align="center" />
        <el-table-column prop="issues" label="红线问题" min-width="100" align="center">
           <template #default="scope">
             <span>{{ scope.row.issues }}</span>
           </template>
        </el-table-column>
        <el-table-column prop="submitDate" label="提交日期" min-width="120" align="center" />
        <el-table-column prop="status" label="状态" min-width="100" align="center">
          <template #default="scope">
            <span>{{ scope.row.status }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="viewDetail(scope.row)">查看</el-button>
            <el-button link type="primary" class="cancel-btn">取消</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pagination-container">
      <el-button link type="primary" :disabled="currentPage === 1" @click="currentPage--">上一项</el-button>
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        layout="pager"
        :total="total"
        :pager-count="5"
        @current-change="handleCurrentChange"
      />
      <el-button link type="primary" :disabled="currentPage === totalPages" @click="currentPage++">下一项</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { getVideoInspectionTasks, type VideoTaskStatus } from '@/api/video-inspection'

const router = useRouter()

interface RecordItem {
  id: number
  canteen: string
  submitter: string
  tableType: string
  score: number
  issues: number
  submitDate: string
  status: string
}

// Mock Data tailored for Video Control Center
const loading = ref(false)
const total = ref(0)
const tableData = ref<RecordItem[]>([])

const fallbackData: RecordItem[] = [
  { id: 1, canteen: '武岗一中一食堂', submitter: '张三', tableType: '高中视频巡检检查表', score: 85, issues: 0, submitDate: '2026-02-14', status: '待整改' },
  { id: 2, canteen: '武岗一中一食堂', submitter: '李四', tableType: '高中视频巡检检查表', score: 89, issues: 0, submitDate: '2026-02-14', status: '已改待审' },
  { id: 3, canteen: '武岗一中一食堂', submitter: '王五', tableType: '高中视频巡检检查表', score: 73, issues: 1, submitDate: '2026-02-14', status: '整改成功' },
  { id: 4, canteen: '武岗一中一食堂', submitter: '张三', tableType: '高中视频巡检检查表', score: 76, issues: 1, submitDate: '2026-02-14', status: '待整改' },
  { id: 5, canteen: '武岗一中一食堂', submitter: '张三', tableType: '高中视频巡检检查表', score: 69, issues: 2, submitDate: '2026-02-14', status: '待整改' },
  { id: 6, canteen: '武岗一中一食堂', submitter: '张三', tableType: '高中视频巡检检查表', score: 84, issues: 1, submitDate: '2026-02-10', status: '待整改' },
  { id: 7, canteen: '武岗一中一食堂', submitter: '张三', tableType: '高中视频巡检检查表', score: 85, issues: 0, submitDate: '2026-02-10', status: '待整改' },
  { id: 8, canteen: '武岗一中一食堂', submitter: '张三', tableType: '高中视频巡检检查表', score: 88, issues: 0, submitDate: '2026-02-10', status: '待整改' },
  { id: 9, canteen: '武岗一中一食堂', submitter: '张三', tableType: '高中视频巡检检查表', score: 85, issues: 0, submitDate: '2026-02-10', status: '待整改' },
  { id: 10, canteen: '武岗一中一食堂', submitter: '张三', tableType: '高中视频巡检检查表', score: 88, issues: 0, submitDate: '2026-02-10', status: '待整改' }
]

// Filters
const dateRange = ref<string[]>([])
const statusFilter = ref('') // Default to show all
const searchText = ref('')

const apiToStatus: Record<VideoTaskStatus, string> = {
  PENDING: '待上报',
  SUBMITTED: '已上报',
  REJECTED: '待整改',
  RECTIFIED: '已改待审',
  COMPLETED: '整改成功'
}

const statusToApi: Record<string, VideoTaskStatus> = {
  待整改: 'REJECTED',
  已改待审: 'RECTIFIED',
  整改成功: 'COMPLETED'
}

const loadVideoRecords = async () => {
  loading.value = true
  try {
    const result = await getVideoInspectionTasks({
      page: currentPage.value,
      page_size: pageSize.value,
      status: statusFilter.value ? statusToApi[statusFilter.value] : undefined,
      start_date: dateRange.value.length === 2 ? dateRange.value[0] : undefined,
      end_date: dateRange.value.length === 2 ? dateRange.value[1] : undefined,
      keyword: searchText.value || undefined
    })
    const records = Array.isArray(result?.list) ? result.list : []
    tableData.value = records.map((item) => ({
      id: item.task_id,
      canteen: item.canteen_name || '-',
      submitter: item.submitter_name || '-',
      tableType: item.template_name || '视频巡检检查表',
      score: Number(item.total_score || 0),
      issues: Number(item.red_line_issues || 0),
      submitDate: item.submission_date || '-',
      status: apiToStatus[item.status] || item.status
    }))
    total.value = Number(result?.total || 0)
  } catch {
    tableData.value = fallbackData
    total.value = fallbackData.length
    ElMessage.warning('视频巡检接口不可用，已展示示例数据')
  } finally {
    loading.value = false
  }
}

// Pagination
const currentPage = ref(1)
const pageSize = ref(10)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

const paginatedData = computed(() => tableData.value)

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  loadVideoRecords()
}

const viewDetail = (row: RecordItem) => {
  router.push({ path: '/video/details', query: { id: String(row.id) } })
}

watch([dateRange, statusFilter, searchText], () => {
  currentPage.value = 1
  loadVideoRecords()
})

onMounted(() => {
  loadVideoRecords()
})
</script>

<style scoped>
.app-container {
  padding: 20px;
  background-color: #fff;
  min-height: 100vh;
}

.filter-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.page-title {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.filter-right {
  display: flex;
  gap: 20px;
  align-items: center;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.table-wrapper {
  margin-bottom: 20px;
}

:deep(.custom-table-header) th {
  background-color: #f0f2f5 !important;
  color: #333;
  font-weight: 600;
}

.cancel-btn {
  margin-left: 12px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 20px;
  gap: 10px;
}
</style>
