<template>
  <div class="dashboard-wrapper">
    <div class="dashboard-container">
      <!-- 左侧快捷导航 -->
      <aside class="quick-nav">
        <div class="quick-nav-title">今日待办</div>
        <div class="quick-nav-grid">
          <div class="quick-nav-item" @click="goToPage('/daily-control/records')">
            <div class="quick-nav-icon">
              <el-icon :size="24"><Document /></el-icon>
            </div>
            <div class="quick-nav-text">日管控控串联</div>
          </div>
          <div class="quick-nav-item" @click="goToPage('/weekly-check/records')">
            <div class="quick-nav-icon">
              <el-icon :size="24"><Calendar /></el-icon>
            </div>
            <div class="quick-nav-text">周排查串联</div>
          </div>
          <div class="quick-nav-item" @click="goToPage('/monthly-dispatch/report-records')">
            <div class="quick-nav-icon">
              <el-icon :size="24"><DocumentCopy /></el-icon>
            </div>
            <div class="quick-nav-text">月调度报告</div>
          </div>
          <div class="quick-nav-item" @click="goToPage('/ledger/records')">
            <div class="quick-nav-icon">
              <el-icon :size="24"><Notebook /></el-icon>
            </div>
            <div class="quick-nav-text">电子台账进度</div>
          </div>
          <div class="quick-nav-item" @click="goToPage('/video-center/inspection')">
            <div class="quick-nav-icon">
              <el-icon :size="24"><VideoCamera /></el-icon>
            </div>
            <div class="quick-nav-text">预频巡检</div>
          </div>
          <div class="quick-nav-item" @click="goToPage('/joint-inspection/records')">
            <div class="quick-nav-icon">
              <el-icon :size="24"><Connection /></el-icon>
            </div>
            <div class="quick-nav-text">联合巡检</div>
          </div>
        </div>
      </aside>

      <!-- 右侧主内容 -->
      <main class="main-section">
        <!-- Tab 切换 -->
        <el-tabs v-model="activeTab" class="content-tabs">
          <el-tab-pane label="提醒下达" name="reminder"></el-tab-pane>
          <el-tab-pane label="智能预警" name="warning"></el-tab-pane>
          <el-tab-pane label="全部工作" name="all"></el-tab-pane>
        </el-tabs>

        <!-- 待办事项列表 -->
        <div class="todo-section">
          <div class="todo-list">
            <div class="todo-item" v-for="(item, index) in todoList" :key="index">
              <div class="todo-avatar">
                <div class="avatar-circle">icon</div>
              </div>
              <div class="todo-content">
                <div class="todo-header">
                  <span class="todo-source">{{ item.source }}</span>
                  <span class="todo-time">{{ item.time }}</span>
                  <el-icon class="todo-warning" color="#f56c6c" :size="18" v-if="item.urgent">
                    <Warning />
                  </el-icon>
                </div>
                <div class="todo-desc">{{ item.description }}</div>
              </div>
              <div class="todo-action">
                <el-button type="primary" size="small">{{ item.actionText }}</el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 下方三栏布局 -->
        <div class="report-section">
          <div class="report-column">
            <div class="report-header">
              <span class="report-title">日管控</span>
              <el-icon class="report-more" :size="18"><Grid /></el-icon>
            </div>
            <div class="report-list">
              <div class="report-item" v-for="(item, index) in reportList" :key="index">
                <div class="report-text">{{ item.title }}</div>
                <div class="report-time">{{ item.time }}</div>
              </div>
            </div>
          </div>

          <div class="report-column">
            <div class="report-header">
              <span class="report-title">周排查</span>
              <el-icon class="report-more" :size="18"><Grid /></el-icon>
            </div>
            <div class="report-list">
              <div class="report-item" v-for="(item, index) in reportList" :key="index">
                <div class="report-text">{{ item.title }}</div>
                <div class="report-time">{{ item.time }}</div>
              </div>
            </div>
          </div>

          <div class="report-column">
            <div class="report-header">
              <span class="report-title">月调度</span>
              <el-icon class="report-more" :size="18"><Grid /></el-icon>
            </div>
            <div class="report-list">
              <div class="report-item" v-for="(item, index) in reportList" :key="index">
                <div class="report-text">{{ item.title }}</div>
                <div class="report-time">{{ item.time }}</div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Document,
  Calendar,
  DocumentCopy,
  Notebook,
  VideoCamera,
  Connection,
  Warning,
  Grid
} from '@element-plus/icons-vue'

const router = useRouter()
const activeTab = ref('reminder')

// 待办事项
const todoList = [
  {
    source: '问题提报',
    time: '2020-08-14  11:55:33',
    description: '武汉一中一食堂房屋查验报告提报，已3天未处理',
    urgent: true,
    actionText: '报废审批'
  },
  {
    source: '问题提报',
    time: '2020-08-14  11:55:33',
    description: '武汉一中一食堂房屋查验报告提报，已3天未处理',
    urgent: true,
    actionText: '报废审批'
  },
  {
    source: '问题提报',
    time: '2020-08-14  11:55:33',
    description: '武汉一中一食堂房屋查验报告提报，已3天未处理',
    urgent: true,
    actionText: '报废审批'
  }
]

// 报告列表
const reportList = [
  {
    title: '武汉一中一食堂完成日管控记录提报',
    time: '2020-10-01 10:20:13'
  },
  {
    title: '武汉一中一食堂完成日管控记录提报',
    time: '2020-10-01 10:20:13'
  },
  {
    title: '武汉一中一食堂完成日管控记录提报',
    time: '2020-10-01 10:20:13'
  },
  {
    title: '武汉一中一食堂完成日管控记录提报',
    time: '2020-10-01 10:20:13'
  },
  {
    title: '武汉一中一食堂完成日管控记录提报',
    time: '2020-10-01 10:20:13'
  }
]

const goToPage = (path: string) => {
  router.push(path)
}
</script>

<style scoped lang="scss">
.dashboard-wrapper {
  height: 100%;
  background: #f5f7fa;
  overflow-y: auto;
}

.dashboard-container {
  display: flex;
  gap: 16px;
  height: 100%;
}

// 左侧快捷导航
.quick-nav {
  width: 240px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 4px;
  padding: 16px;
}

.quick-nav-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e8ecf0;
}

.quick-nav-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.quick-nav-item {
  background: linear-gradient(135deg, #e8f4ff 0%, #f0f9ff 100%);
  border: 1px solid #d9ecff;
  border-radius: 8px;
  padding: 16px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  min-height: 90px;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(74, 139, 254, 0.15);
    border-color: #4A8BFE;
  }
}

.quick-nav-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #5B9DFF 0%, #4A8FFF 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin-bottom: 8px;
}

.quick-nav-text {
  font-size: 12px;
  font-weight: 500;
  color: #303133;
  text-align: center;
  line-height: 1.4;
}

// 右侧主内容
.main-section {
  flex: 1;
  background: #fff;
  border-radius: 4px;
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-tabs {
  padding: 0 20px;
  
  :deep(.el-tabs__header) {
    margin-bottom: 0;
    border-bottom: 1px solid #e8ecf0;
  }

  :deep(.el-tabs__nav-wrap::after) {
    display: none;
  }

  :deep(.el-tabs__item) {
    font-size: 14px;
    font-weight: 500;
    color: #606266;
    padding: 0 20px;
    height: 44px;
    line-height: 44px;

    &:hover {
      color: #4A8BFE;
    }

    &.is-active {
      color: #4A8BFE;
      font-weight: 600;
    }
  }

  :deep(.el-tabs__active-bar) {
    height: 2px;
    background-color: #4A8BFE;
  }
}

// 待办事项区域
.todo-section {
  padding: 16px 20px;
  border-bottom: 1px solid #e8ecf0;
}

.todo-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.todo-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  background: #fff;
  border-bottom: 1px solid #f0f2f5;
  transition: all 0.3s;

  &:hover {
    background: linear-gradient(90deg, #f8f9fa 0%, #ffffff 100%);
  }

  &:last-child {
    border-bottom: none;
  }
}

.todo-avatar {
  margin-right: 12px;
}

.avatar-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #303133;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
}

.todo-content {
  flex: 1;
}

.todo-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.todo-source {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.todo-time {
  font-size: 13px;
  color: #909399;
}

.todo-warning {
  margin-left: 4px;
}

.todo-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.todo-action {
  margin-left: 16px;
}

// 报告三栏布局
.report-section {
  flex: 1;
  display: flex;
  border-top: 1px solid #e8ecf0;
  overflow: hidden;
}

.report-column {
  flex: 1;
  border-right: 1px solid #e8ecf0;
  display: flex;
  flex-direction: column;

  &:last-child {
    border-right: none;
  }
}

.report-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e8ecf0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f8f9fa;
}

.report-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.report-more {
  color: #909399;
  cursor: pointer;
  transition: color 0.3s;

  &:hover {
    color: #4A8BFE;
  }
}

.report-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
}

.report-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f2f5;

  &:last-child {
    border-bottom: none;
  }
}

.report-text {
  font-size: 13px;
  color: #303133;
  margin-bottom: 6px;
  line-height: 1.5;
}

.report-time {
  font-size: 12px;
  color: #909399;
}
</style>
