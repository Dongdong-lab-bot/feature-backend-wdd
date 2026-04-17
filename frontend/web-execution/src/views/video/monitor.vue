<template>
  <div class="video-monitor-container">
    <div class="page-header">
      <h2>视频画面选择</h2>
    </div>

    <div class="content-wrapper">
      <!-- Sidebar -->
      <div class="sidebar">
        <el-tree
          :data="treeData"
          :props="defaultProps"
          default-expand-all
          :expand-on-click-node="true"
          class="custom-tree"
          @node-click="handleNodeClick"
        >
          <template #default="{ node, data }">
            <span class="custom-tree-node">
              <span>{{ node.label }}</span>
            </span>
          </template>
        </el-tree>
      </div>

      <!-- Main Video Grid -->
      <div class="main-content">
        <div class="video-grid">
          <div v-for="n in 9" :key="n" class="video-slot">
            <div class="placeholder-content">
              <!-- 模拟视频播放区域 -->
              <div v-if="activeSlot === n && currentPlayParams" class="video-playing">
                <span class="video-text">监控画面播放中...</span>
                <span class="video-text-small">序列号: {{ currentPlayParams.deviceSerial }} 通道: {{ currentPlayParams.channelNo }}</span>
                <!-- 模拟抓拍按钮 -->
                <el-button 
                  type="primary" 
                  size="small" 
                  class="capture-btn"
                  @click.stop="handleCapture"
                >
                  <el-icon><Camera /></el-icon> 抓拍
                </el-button>
              </div>
              <div v-else class="mountain-icon">
                <!-- Simple CSS/SVG representation of the placeholder in screenshot -->
                <svg viewBox="0 0 100 60" class="placeholder-svg">
                  <path d="M0 60 L30 20 L50 40 L70 10 L100 60 Z" fill="#0099cc" />
                  <circle cx="80" cy="15" r="5" fill="#ccc" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer Controls -->
        <div class="video-footer">
          <div class="footer-actions">
            <el-button link type="primary" class="footer-btn">分屏选择</el-button>
            <el-button link type="primary" class="footer-btn">录像回看</el-button>
            <el-icon class="fullscreen-icon"><FullScreen /></el-icon>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { FullScreen, Camera } from '@element-plus/icons-vue'
import { 
  getVideoCameraTree, 
  getHikvisionPlayParams,
  captureCameraFrame,
  type VideoCameraTreeNode 
} from '@/api/video-inspection'

interface Tree {
  id?: number | string
  cameraId?: string | number
  label: string
  type?: string
  children?: Tree[]
}

const treeData = ref<Tree[]>([
  {
    id: 'fallback-root',
    label: '武岗一食堂',
    children: [
      {
        id: 'fallback-1',
        label: '烹饪间',
        children: [
          { id: 'fallback-1-1', label: '一号摄像头', type: 'CAMERA' },
          { id: 'fallback-1-2', label: '二号摄像头', type: 'CAMERA' },
          { id: 'fallback-1-3', label: '三号摄像头', type: 'CAMERA' },
          { id: 'fallback-1-4', label: '四号摄像头', type: 'CAMERA' },
        ],
      },
      {
        id: 'fallback-2',
        label: '售卖间',
        children: [
          { id: 'fallback-2-1', label: '五号摄像头', type: 'CAMERA' },
          { id: 'fallback-2-2', label: '六号摄像头', type: 'CAMERA' },
          { id: 'fallback-2-3', label: '七号摄像头', type: 'CAMERA' },
          { id: 'fallback-2-4', label: '八号摄像头', type: 'CAMERA' },
        ],
      },
      {
        id: 'fallback-3',
        label: '洗消间',
        children: [
          { id: 'fallback-3-1', label: '九号摄像头', type: 'CAMERA' },
          { id: 'fallback-3-2', label: '十号摄像头', type: 'CAMERA' },
        ],
      },
      {
        id: 'fallback-4',
        label: '大厅',
        children: [
          { id: 'fallback-4-1', label: '十一号摄像头', type: 'CAMERA' },
          { id: 'fallback-4-2', label: '十二号摄像头', type: 'CAMERA' },
        ],
      },
    ],
  },
])

const defaultProps = {
  children: 'children',
  label: 'label',
}

const activeSlot = ref(1)
const currentPlayParams = ref<any>(null)
const currentCameraId = ref<string | number | null>(null)

const handleNodeClick = async (data: Tree) => {
  // 如果是叶子节点（没有 children），我们就认为它是摄像头
  const isLeaf = !data.children || data.children.length === 0
  
  if (data.type === 'CAMERA' || isLeaf) {
    currentCameraId.value = data.cameraId || data.id || null
    if (!currentCameraId.value) {
      ElMessage.warning('此节点无有效的摄像头ID')
      return
    }

    try {
      const res = await getHikvisionPlayParams({
        cameraId: currentCameraId.value,
        action: 'preview'
      })
      currentPlayParams.value = res || { deviceSerial: 'Mock-DS', channelNo: '1' }
      ElMessage.success(`正在连接摄像头: ${data.label}`)
    } catch {
      // 容错处理：为了让用户在没有真实后端环境时也能看到交互效果
      currentPlayParams.value = { deviceSerial: 'Mock-DS-1234', channelNo: '1' }
      ElMessage.warning('播放参数接口不可用，已模拟连接')
    }
  }
}

const handleCapture = async () => {
  if (!currentCameraId.value) return
  
  try {
    const timestamp = new Date().toISOString()
    const mockBase64 = "data:image/jpeg;base64,mockdata"
    
    await captureCameraFrame(currentCameraId.value, {
      image_base64: mockBase64,
      timestamp
    })
    ElMessage.success('监控画面抓拍并上传成功！')
  } catch {
    ElMessage.warning('抓拍接口调用失败，但已模拟抓拍动作')
  }
}

const mapCameraTree = (nodes: VideoCameraTreeNode[]): Tree[] => {
  return nodes.map((node) => ({
    id: node.id,
    label: node.name,
    type: node.type,
    children: Array.isArray(node.children) ? mapCameraTree(node.children) : []
  }))
}

const loadCameraTree = async () => {
  try {
    const res = await getVideoCameraTree()
    const list = Array.isArray(res?.tree) ? res.tree : []
    if (!Array.isArray(list) || list.length === 0) return
    treeData.value = mapCameraTree(list)
  } catch {
    ElMessage.warning('摄像头树接口不可用，当前展示示例数据')
  }
}

onMounted(() => {
  loadCameraTree()
})
</script>

<style scoped>
.video-monitor-container {
  padding: 20px;
  background-color: #fff;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 18px;
  font-weight: normal;
  color: #333;
  margin: 0;
}

.content-wrapper {
  display: flex;
  gap: 20px;
  height: calc(100vh - 100px); /* Adjust based on header/layout */
}

/* Sidebar Styling */
.sidebar {
  width: 240px;
  background-color: #7aa7f0; /* Matches screenshot blue */
  padding: 10px 0;
  flex-shrink: 0;
}

/* Custom Tree Styling to match screenshot */
:deep(.el-tree) {
  background-color: transparent;
  color: #fff;
}

:deep(.el-tree-node__content) {
  height: 32px;
}

:deep(.el-tree-node__content:hover) {
  background-color: rgba(255, 255, 255, 0.1);
}

:deep(.el-tree-node:focus > .el-tree-node__content) {
  background-color: rgba(255, 255, 255, 0.2);
}

:deep(.el-tree-node__expand-icon) {
  color: #fff;
}

:deep(.el-tree-node__expand-icon.is-leaf) {
  color: transparent;
}

.custom-tree-node {
  font-size: 14px;
}

/* Main Content Styling */
.main-content {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(3, 1fr);
  gap: 15px;
  background-color: #ccc; /* Grey background for grid gap area */
  padding: 15px;
  flex-grow: 1;
  border: 1px solid #ccc;
}

.video-slot {
  background-color: #fff;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-playing {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background-color: #000;
  color: #fff;
  gap: 10px;
}

.video-text {
  font-size: 16px;
  font-weight: bold;
}

.video-text-small {
  font-size: 12px;
  color: #aaa;
}

.capture-btn {
  margin-top: 10px;
}

.placeholder-content {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-svg {
  width: 100%;
  height: 100%;
  max-width: 150px;
  max-height: 100px;
}

.video-footer {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

.footer-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.footer-btn {
  font-size: 14px;
  color: #409eff;
}

.fullscreen-icon {
  cursor: pointer;
  font-size: 18px;
  color: #333;
}
</style>
