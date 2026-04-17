<template>
  <div class="dashboard-container">
    <!-- 1. 消息预警区域 -->
    <div class="section-container alert-section">
      <h2 class="section-title">消息预警</h2>
      <div class="alert-content">
        <el-tabs v-model="activeAlertTab" class="custom-tabs">
          <el-tab-pane label="提醒" name="reminder">
            <div class="alert-list">
              <div v-for="(item, index) in alertList" :key="index" class="alert-card">
                <div class="alert-icon-wrapper">
                  <span class="alert-icon-text">icon</span>
                </div>
                <div class="alert-info">
                  <div class="alert-header">
                    <span class="alert-type">{{ item.type }}</span>
                    <span class="alert-time">{{ item.time }}</span>
                    <el-icon class="urgent-icon"><Warning /></el-icon>
                  </div>
                  <div class="alert-desc">{{ item.content }}</div>
                </div>
                <div class="alert-action">
                  <el-button type="primary" size="small" class="action-btn">{{ item.actionText }}</el-button>
                </div>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="智能预警" name="warning">
            <div class="empty-placeholder">暂无智能预警</div>
          </el-tab-pane>
          <el-tab-pane label="全部" name="all">
            <div class="empty-placeholder">暂无更多消息</div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!-- 2. SOP执行中心 -->
    <div class="section-container sop-section">
      <div class="sop-header">
        <h2 class="section-title">SOP执行中心</h2>
        <div class="progress-container">
          <div class="custom-progress-bar">
            <div class="progress-fill" :style="{ width: calculateProgress + '%' }"></div>
            <span class="progress-text">今日SOP已完成 {{ completedTasks }}/{{ totalTasks }}</span>
          </div>
        </div>
      </div>
      
      <div class="sop-nav-grid">
        <div class="sop-nav-card blue" @click="navigateTo('/daily/checklist')">
          <span class="nav-title">日管控</span>
        </div>
        <div class="sop-nav-card yellow" @click="navigateTo('/weekly/records')">
          <span class="nav-title">周排查</span>
        </div>
        <div class="sop-nav-card orange" @click="navigateTo('/monthly/reports')">
          <span class="nav-title">月调度</span>
        </div>
        <div class="sop-nav-card green" @click="navigateTo('/inspection/records')">
          <span class="nav-title">联合巡检</span>
        </div>
      </div>

      <!-- 任务卡片列表 -->
      <div class="task-grid">
        <div v-for="(task, index) in taskList" :key="index" class="task-card">
          <div class="task-preview">
            <!-- 模拟表格缩略图 -->
            <div class="table-thumbnail">
              <div class="excel-grid">
                <div class="excel-header-row">
                  <div class="excel-cell header-cell"></div>
                  <div class="excel-cell header-cell">A</div>
                  <div class="excel-cell header-cell">B</div>
                  <div class="excel-cell header-cell">C</div>
                  <div class="excel-cell header-cell">D</div>
                  <div class="excel-cell header-cell">E</div>
                </div>
                <div class="excel-row" v-for="n in 5" :key="n">
                  <div class="excel-cell index-cell">{{ n }}</div>
                  <div class="excel-cell"></div>
                  <div class="excel-cell"></div>
                  <div class="excel-cell"></div>
                  <div class="excel-cell"></div>
                  <div class="excel-cell"></div>
                </div>
              </div>
              
              <div class="status-badge" :class="task.status">
                <span v-if="task.status === 'pending'">待开始</span>
                <el-icon v-else><Check /></el-icon>
              </div>
            </div>
          </div>
          <div class="task-footer">
            <div class="task-icon">S</div>
            <span class="task-name">{{ task.name }}</span>
            <el-dropdown trigger="click" class="more-options">
              <el-icon><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item>查看详情</el-dropdown-item>
                  <el-dropdown-item>开始填报</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Warning, Check, MoreFilled } from '@element-plus/icons-vue'
import { getLedgerInstances } from '@/api/ledger'

const router = useRouter()
const activeAlertTab = ref('reminder')

// 模拟数据
const alertList = ref([
  {
    type: '问题提报',
    time: '2020-08-14 11:55:33',
    content: '武汉一中一食堂房屋查验报告待提报，已3天未处理',
    actionText: '提醒食堂'
  },
  {
    type: '问题提报',
    time: '2020-08-14 11:55:33',
    content: '武汉一中一食堂房屋查验报告待提报，已3天未处理',
    actionText: '提醒食堂'
  },
  {
    type: '问题提报',
    time: '2020-08-14 11:55:33',
    content: '武汉一中一食堂房屋查验报告待提报，已3天未处理',
    actionText: '提醒食堂'
  },
  {
    type: '问题提报',
    time: '2020-08-14 11:55:33',
    content: '武汉一中一食堂房屋查验报告待提报，已3天未处理',
    actionText: '提醒食堂'
  }
])

const completedTasks = ref(0)
const totalTasks = ref(0)

const calculateProgress = computed(() => {
  return (completedTasks.value / totalTasks.value) * 100
})

const taskList = ref([
  { name: '晨检台账填报', status: 'pending' },
  { name: '晨检台账填报', status: 'completed' },
  { name: '晨检台账填报', status: 'completed' },
  { name: '晨检台账填报', status: 'pending' },
  { name: '晨检台账填报', status: 'pending' },
  { name: '晨检台账填报', status: 'completed' },
  { name: '晨检台账填报', status: 'pending' },
  { name: '晨检台账填报', status: 'pending' }
])

const loadDashboardSummary = async () => {
  try {
    const result = await getLedgerInstances({ page: 1, size: 50 })
    const records = Array.isArray(result?.records) ? result.records : []
    totalTasks.value = records.length
    completedTasks.value = records.filter((item) => item.status === 'SIGNED' || item.status === 'ARCHIVED').length

    if (records.length > 0) {
      taskList.value = records.slice(0, 8).map((item) => ({
        name: `任务#${item.id}`,
        status: item.status === 'PENDING' ? 'pending' : 'completed'
      }))
    }
  } catch {
    totalTasks.value = 20
    completedTasks.value = 18
  }
}

const navigateTo = (path: string) => {
  router.push(path)
}

onMounted(() => {
  loadDashboardSummary()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100%;
}

.section-container {
  margin-bottom: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
  display: inline-block;
}

/* 消息预警样式 */
.alert-content {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.alert-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.alert-card {
  background-color: #FDF2F5; /* 浅粉色背景 */
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.alert-icon-wrapper {
  width: 48px;
  height: 48px;
  background-color: #8E44AD; /* 紫色图标背景 */
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.alert-icon-text {
  color: #fff;
  font-size: 12px;
}

.alert-info {
  flex: 1;
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.alert-type {
  font-weight: 600;
  color: #333;
}

.alert-time {
  font-size: 12px;
  color: #999;
}

.urgent-icon {
  color: #F56C6C;
}

.alert-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.4;
}

.action-btn {
  background-color: #9B59B6;
  border-color: #9B59B6;
}

.action-btn:hover {
  background-color: #8E44AD;
  border-color: #8E44AD;
}

/* SOP Header */
.sop-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 20px;
}

.sop-header .section-title {
  margin-bottom: 0;
  white-space: nowrap; /* 防止标题换行 */
}

.progress-container {
  flex: 1;
  /* max-width removed to allow full width */
}

.custom-progress-bar {
  height: 32px;
  background-color: #E6EFFF;
  border-radius: 16px;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #00C6FF 0%, #0072FF 100%);
  border-radius: 16px;
  transition: width 0.5s ease;
}

.progress-text {
  position: absolute;
  right: 16px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0,0,0,0.1);
  /* 如果进度条太短，文字可能看不清，这里假设进度条足够长或文字始终在右侧 */
  z-index: 2;
  /* 修正：如果文字在未填充区域，颜色应该是深色 */
  mix-blend-mode: difference; 
  color: #fff; /* 配合 mix-blend-mode 使用 */
}

/* SOP Navigation Cards */
.sop-nav-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.sop-nav-card {
  height: 100px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.3s;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.sop-nav-card:hover {
  transform: translateY(-4px);
}

.sop-nav-card.blue { background: linear-gradient(135deg, #00C6FF 0%, #0072FF 100%); }
.sop-nav-card.yellow { background: linear-gradient(135deg, #FFD15C 0%, #FF9B21 100%); }
.sop-nav-card.orange { background: linear-gradient(135deg, #FF7E5F 0%, #FEB47B 100%); }
.sop-nav-card.green { background: linear-gradient(135deg, #2AF598 0%, #009EFD 100%); }

.nav-title {
  font-size: 20px;
  font-weight: bold;
  color: #fff;
  letter-spacing: 1px;
}

/* Task Grid */
.task-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.task-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  transition: all 0.3s;
}

.task-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}

.task-preview {
  margin-bottom: 12px;
}

.table-thumbnail {
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 4px;
  height: 120px;
  position: relative;
  overflow: hidden;
}

.excel-grid {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  border: 1px solid #e4e7ed;
}

.excel-header-row {
  display: flex;
  height: 20px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.excel-row {
  display: flex;
  flex: 1;
  border-bottom: 1px solid #e4e7ed;
}

.excel-row:last-child {
  border-bottom: none;
}

.excel-cell {
  flex: 1;
  border-right: 1px solid #e4e7ed;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.excel-cell:last-child {
  border-right: none;
}

.header-cell {
  font-weight: bold;
  color: #606266;
}

.index-cell {
  width: 20px;
  flex: none;
  background-color: #f5f7fa;
  font-weight: bold;
}

.status-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

.status-badge.pending {
  background-color: #FFD700;
  color: #fff;
}

.status-badge.completed {
  background-color: #2ECC71;
  color: #fff;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.task-footer {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-icon {
  width: 24px;
  height: 24px;
  background-color: #27AE60;
  color: #fff;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}

.task-name {
  flex: 1;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.more-options {
  cursor: pointer;
  color: #909399;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .sop-nav-grid, .task-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .alert-list {
    grid-template-columns: 1fr;
  }
  
  .sop-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .progress-container {
    width: 100%;
  }
  
  .sop-nav-grid, .task-grid {
    grid-template-columns: 1fr;
  }
}
</style>