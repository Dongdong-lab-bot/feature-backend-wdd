import { RouteRecordRaw } from 'vue-router'

// 公共路由（不需要权限即可访问）
export const constantRoutes: Array<RouteRecordRaw> = [
  {
    path: '/login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', hidden: true }
  },
  {
    path: '/',
    component: () => import('@/layout/index.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '首页', icon: 'HomeFilled' }
      }
    ]
  },
  {
    path: '/403',
    component: () => import('@/views/error/403.vue'),
    meta: { title: '403', hidden: true }
  },
  {
    path: '/404',
    component: () => import('@/views/error/404.vue'),
    meta: { title: '404', hidden: true }
  }
]

// 业务路由（根据你的 UI 框架配置）
export const asyncRoutes: Array<RouteRecordRaw> = [
  {
    path: '/canteen',
    component: () => import('@/layout/index.vue'),
    redirect: '/canteen/staff',
    meta: { title: '食堂中心', icon: 'Shop' },
    children: [
      {
        path: 'position',
        name: 'CanteenPosition',
        component: () => import('@/views/canteen/position.vue'),
        meta: { title: '职务管理', icon: 'UserFilled' }
      },
      {
        path: 'staff',
        name: 'CanteenStaff',
        component: () => import('@/views/canteen/staff.vue'),
        meta: { title: '员工管理', icon: 'Avatar' }
      },
      {
        path: 'device',
        name: 'CanteenDevice',
        component: () => import('@/views/canteen/device.vue'),
        meta: { title: '食堂设备中心', icon: 'Cpu' }
      },
      {
        path: 'device-logs',
        name: 'CanteenDeviceLogs',
        component: () => import('@/views/canteen/device-logs.vue'),
        meta: { title: '设备消息记录', icon: 'Bell' }
      }
    ]
  },
  {
    path: '/daily',
    component: () => import('@/layout/index.vue'),
    redirect: '/daily/checklist',
    meta: { title: '日管控', icon: 'Calendar' },
    children: [
      {
        path: 'checklist',
        name: 'DailyChecklist',
        component: () => import('@/views/daily/checklist.vue'),
        meta: { title: '日管控检查表' }
      },
      {
        path: 'records',
        name: 'DailyRecords',
        component: () => import('@/views/daily/records.vue'),
        meta: { title: '记录查看' }
      },
      {
        path: 'details',
        name: 'DailyDetails',
        component: () => import('@/views/daily/details.vue'),
        meta: { title: '记录详情', hidden: true }
      }
    ]
  },
  {
    path: '/weekly',
    component: () => import('@/layout/index.vue'),
    meta: { title: '周排查', icon: 'List' },
    children: [
      {
        path: 'records',
        name: 'WeeklyRecords',
        component: () => import('@/views/weekly/records.vue'),
        meta: { title: '记录查看与整改' }
      },
      {
        path: 'details',
        name: 'WeeklyDetails',
        component: () => import('@/views/weekly/details.vue'),
        meta: { title: '记录详情', hidden: true }
      }
    ]
  },
  {
    path: '/monthly',
    component: () => import('@/layout/index.vue'),
    meta: { title: '月调度', icon: 'TrendCharts' },
    children: [
      {
        path: 'reports',
        name: 'MonthlyReports',
        component: () => import('@/views/monthly/reports.vue'),
        meta: { title: '月调度报告记录' }
      }
    ]
  },
  {
    path: '/inspection',
    component: () => import('@/layout/index.vue'),
    meta: { title: '联合巡检', icon: 'Aim' },
    children: [
      {
        path: 'records',
        name: 'InspectionRecords',
        component: () => import('@/views/joint/records.vue'),
        meta: { title: '记录查看与整改' }
      },
      {
        path: 'details',
        name: 'InspectionDetails',
        component: () => import('@/views/joint/details.vue'),
        meta: { title: '记录详情', hidden: true }
      }
    ]
  },
  {
    path: '/video',
    component: () => import('@/layout/index.vue'),
    meta: { title: '视频集控中心', icon: 'VideoCamera' },
    children: [
      {
        path: 'view',
        name: 'VideoView',
        component: () => import('@/views/video/monitor.vue'),
        meta: { title: '视频查看' }
      },
      {
        path: 'records',
        name: 'VideoRecords',
        component: () => import('@/views/video/records.vue'),
        meta: { title: '记录查看与整改' }
      },
      {
        path: 'details',
        name: 'VideoDetails',
        component: () => import('@/views/video/details.vue'),
        meta: { title: '记录详情', hidden: true }
      }
    ]
  },
  {
    path: '/ledger',
    component: () => import('@/layout/index.vue'),
    meta: { title: '电子台账中心', icon: 'Notebook' },
    children: [
      {
        path: 'submit',
        name: 'LedgerSubmit',
        component: () => import('@/views/ledger/submit.vue'),
        meta: { title: '电子台账提交' }
      },
      {
        path: 'records',
        name: 'LedgerRecords',
        component: () => import('@/views/ledger/records.vue'),
        meta: { title: '电子台账记录' }
      }
    ]
  },
  {
    path: '/score-records',
    component: () => import('@/layout/index.vue'),
    redirect: '/score-records/index',
    children: [
      {
        path: 'index',
        name: 'ScoreRecords',
        component: () => import('@/views/records.vue'),
        meta: { title: '食安指数处理记录', icon: 'DataLine' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404',
    meta: { hidden: true }
  }
]
