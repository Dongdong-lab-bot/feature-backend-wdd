<template>
  <div class="custom-layout">
    <!-- 顶部导航栏 -->
    <header class="top-header">
      <div class="header-left">
        <div class="system-logo">
          <span class="system-name">{{ systemTitle }}</span>
        </div>
      </div>
      <div class="header-right">
        <span class="welcome-text">欢迎您，{{ userName }}</span>
        <el-dropdown trigger="click" @command="handleCommand">
          <span class="el-dropdown-link">
            退出登录
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <div class="layout-body">
      <!-- 一级导航（图标栏）-->
      <aside class="sidebar-level-1">
        <div class="nav-icons">
          <div class="nav-item" :class="{ active: activeGroup === 'main' }" @click="switchGroup('main')">
            <el-icon :size="24"><Grid /></el-icon>
          </div>
          <div class="nav-item" @click="switchGroup('settings')">
            <el-icon :size="24"><Setting /></el-icon>
          </div>
          <div class="nav-item" @click="switchGroup('data')">
            <el-icon :size="24"><DataAnalysis /></el-icon>
          </div>
        </div>
      </aside>

      <!-- 二级菜单（可折叠面板）-->
      <aside class="sidebar-level-2">
        <el-scrollbar class="menu-scrollbar" style="margin-top: 12px;">
          <div class="menu-groups">
            <div v-for="group in menuRoutes" :key="group.path" class="menu-group">
              <!-- 分组标题 -->
              <div
                class="group-header"
                :class="{ active: isGroupActive(group), expanded: expandedGroups.includes(group.path) }"
                @click="toggleGroup(group.path)"
              >
                <span class="group-title">{{ group.meta?.title }}</span>
                <el-icon class="arrow-icon" :class="{ rotated: expandedGroups.includes(group.path) }">
                  <ArrowRight />
                </el-icon>
              </div>

              <!-- 子菜单项 -->
              <transition name="submenu">
                <div v-show="expandedGroups.includes(group.path)" class="submenu-list">
                  <div
                    v-for="child in group.children"
                    :key="child.path"
                    class="submenu-item"
                    :class="{ active: isItemActive(group.path, child.path) }"
                    @click="navigateTo(group.path, child.path)"
                  >
                    {{ child.meta?.title }}
                  </div>
                </div>
              </transition>
            </div>
          </div>
        </el-scrollbar>
      </aside>

      <!-- 主内容区 -->
      <main class="main-content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Grid,
  Setting,
  DataAnalysis,
  ArrowRight
} from '@element-plus/icons-vue'
import type { RouteRecordRaw } from 'vue-router'

interface Props {
  systemTitle?: string
  userName?: string
  menuRoutes?: RouteRecordRaw[]
}

const props = withDefaults(defineProps<Props>(), {
  systemTitle: '智慧食安管理平台',
  userName: '用户',
  menuRoutes: () => []
})

const emit = defineEmits<{
  (e: 'logout'): void
}>()

const router = useRouter()
const route = useRoute()

const activeGroup = ref('main')
const expandedGroups = ref<string[]>([])

// 初始化展开当前路由所在的分组
const initExpandedGroups = () => {
  const currentPath = route.path
  for (const group of props.menuRoutes) {
    if (currentPath.startsWith(group.path)) {
      if (!expandedGroups.value.includes(group.path)) {
        expandedGroups.value.push(group.path)
      }
      break
    }
  }
}

// 切换一级导航
const switchGroup = (group: string) => {
  activeGroup.value = group
}

// 切换分组展开/收起
const toggleGroup = (groupPath: string) => {
  const index = expandedGroups.value.indexOf(groupPath)
  if (index > -1) {
    expandedGroups.value.splice(index, 1)
  } else {
    expandedGroups.value.push(groupPath)
  }
}

// 判断分组是否激活
const isGroupActive = (group: any) => {
  return route.path.startsWith(group.path)
}

// 判断子项是否激活
const isItemActive = (groupPath: string, childPath: string) => {
  const fullPath = childPath.startsWith('/') ? childPath : `${groupPath}/${childPath}`
  return route.path === fullPath
}

// 导航到子项
const navigateTo = (groupPath: string, childPath: string) => {
  const fullPath = childPath.startsWith('/') ? childPath : `${groupPath}/${childPath}`
  router.push(fullPath)
}

// 用户命令处理
const handleCommand = (command: string) => {
  if (command === 'logout') {
    emit('logout')
  }
}

// 监听路由变化，自动展开对应分组
watch(() => route.path, () => {
  initExpandedGroups()
}, { immediate: true })
</script>

<style scoped lang="scss">
.custom-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

/* 顶部导航 */
.top-header {
  height: 60px;
  background: linear-gradient(90deg, #5B9DFF 0%, #4A8FFF 100%);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  color: #fff;
  flex-shrink: 0;
  z-index: 2000;
}

.header-left {
  display: flex;
  align-items: center;
}

.system-name {
  font-size: 20px;
  font-weight: bold;
  letter-spacing: 1px;
}

.header-right {
  display: flex;
  align-items: center;
}

.welcome-text {
  margin-right: 20px;
  font-size: 14px;
}

.el-dropdown-link {
  cursor: pointer;
  color: #fff;
  font-size: 14px;
}

/* 主体布局 */
.layout-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 一级导航（图标栏）*/
.sidebar-level-1 {
  width: 64px;
  background-color: #2F3542;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  z-index: 900;
}

.nav-icons {
  padding-top: 20px;
}

.nav-item {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8895a7;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;

  &:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: #fff;
  }

  &.active {
    color: #5B9DFF;
    background-color: rgba(91, 157, 255, 0.1);

    &::after {
      content: '';
      position: absolute;
      right: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 3px;
      height: 24px;
      background-color: #5B9DFF;
      border-radius: 2px 0 0 2px;
    }
  }
}

/* 二级菜单（可折叠面板）*/
.sidebar-level-2 {
  width: 200px;
  background-color: #ffffff;
  border-right: 1px solid #e8ecf0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.menu-scrollbar {
  flex: 1;
  :deep(.el-scrollbar__wrap) {
    overflow-x: hidden;
  }

  :deep(.el-scrollbar__bar.is-vertical) {
    width: 4px;
  }

  :deep(.el-scrollbar__thumb) {
    background-color: rgba(74, 139, 254, 0.3);
    border-radius: 2px;
  }
}

.menu-groups {
  padding: 8px 0;
}

.menu-group {
  margin-bottom: 4px;
}

/* 分组标题 */
.group-header {
  height: 42px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  user-select: none;

  &:hover {
    background-color: rgba(74, 139, 254, 0.05);
  }

  &.active,
  &.expanded {
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 4px;
      background-color: #4A8BFE;
    }
  }
}

.group-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  transition: color 0.3s;
  letter-spacing: 0.3px;

  .group-header.active &,
  .group-header.expanded & {
    color: #4A8BFE;
  }
}

.arrow-icon {
  color: #909399;
  transition: transform 0.3s, color 0.3s;
  font-size: 12px;

  &.rotated {
    transform: rotate(90deg);
  }

  .group-header.active &,
  .group-header.expanded & {
    color: #4A8BFE;
  }
}

/* 子菜单项 */
.submenu-list {
  overflow: hidden;
}

.submenu-item {
  height: auto;
  min-height: 36px;
  padding: 10px 16px 10px 40px;
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
  user-select: none;
  line-height: 1.6;
  letter-spacing: 0.3px;
  position: relative;

  &:hover {
    background-color: rgba(74, 139, 254, 0.1);
    color: #4A8BFE;
    font-weight: 600;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 4px;
      background-color: #4A8BFE;
      transition: all 0.3s;
    }
  }

  &.active {
    background-color: rgba(74, 139, 254, 0.1);
    color: #4A8BFE;
    font-weight: 600;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 4px;
      background-color: #4A8BFE;
    }
  }
}

/* 子菜单展开/收起动画 */
.submenu-enter-active,
.submenu-leave-active {
  transition: all 0.3s ease;
  max-height: 500px;
}

.submenu-enter-from,
.submenu-leave-to {
  max-height: 0;
  opacity: 0;
}

/* 主内容区 */
.main-content {
  flex: 1;
  background-color: #f5f7fa;
  overflow-y: auto;
  padding: 20px;
}
</style>
