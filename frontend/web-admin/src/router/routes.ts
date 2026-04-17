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
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404',
    meta: { hidden: true }
  }
]

// 业务路由（监管端菜单）
export const asyncRoutes: Array<RouteRecordRaw> = [
  {
    path: '/user-center',
    component: () => import('@/layout/index.vue'),
    redirect: '/user-center/menu',
    meta: { title: '用户中心', icon: 'User' },
    children: [
      {
        path: 'menu',
        name: 'FunctionMenu',
        component: () => import('@/views/system/menu/index.vue'),
        meta: { title: '功能菜单管理', permissions: ['menu:view'], isDeveloping: true }
      },
      {
        path: 'dept',
        name: 'Department',
        component: () => import('@/views/system/dept/index.vue'),
        meta: { title: '部门管理', permissions: ['dept:view'], isDeveloping: true }
      },
      {
        path: 'position',
        name: 'Position',
        component: () => import('@/views/system/role/index.vue'),
        meta: { title: '职务管理', permissions: ['role:view'], isDeveloping: true }
      },
      {
        path: 'user',
        name: 'UserManagement',
        component: () => import('@/views/system/user/index.vue'),
        meta: { title: '用户管理', permissions: ['user:view'] }
      }
    ]
  },
  {
    path: '/canteen-center',
    component: () => import('@/layout/index.vue'),
    redirect: '/canteen-center/organization',
    meta: { title: '食堂中心', icon: 'Shop' },
    children: [
      {
        path: 'organization',
        name: 'CanteenOrganization',
        component: () => import('@/views/canteen/organization/index.vue'),
        meta: { title: '食堂组织架构', permissions: ['canteen:org'], isDeveloping: true }
      },
      {
        path: 'device',
        name: 'CanteenDevice',
        component: () => import('@/views/canteen/list/index.vue'),
        meta: { title: '食堂设备中心', permissions: ['canteen:device'], isDeveloping: true }
      },
      {
        path: 'device-logs',
        name: 'DeviceLogs',
        component: () => import('@/views/canteen/device-logs/index.vue'),
        meta: { title: '设备消息记录', permissions: ['canteen:logs'], isDeveloping: true }
      }
    ]
  },
  {
    path: '/daily-control',
    component: () => import('@/layout/index.vue'),
    redirect: '/daily-control/records',
    meta: { title: '日管控', icon: 'Calendar' },
    children: [
      {
        path: 'records',
        name: 'DailyRecords',
        component: () => import('@/views/inspection/daily/index.vue'),
        meta: { title: '记录查看与审核', permissions: ['daily:view'], isDeveloping: true }
      },
      {
        path: 'checklist',
        name: 'DailyChecklist',
        component: () => import('@/views/inspection/daily/index.vue'),
        meta: { title: '日管控检查表', permissions: ['daily:check'], isDeveloping: true }
      },
      {
        path: 'create',
        name: 'DailyCreate',
        component: () => import('@/views/inspection/daily/index.vue'),
        meta: { title: '新建日管控检查表', permissions: ['daily:create'], isDeveloping: true }
      }
    ]
  },
  {
    path: '/weekly-check',
    component: () => import('@/layout/index.vue'),
    redirect: '/weekly-check/records',
    meta: { title: '周排查', icon: 'Document' },
    children: [
      {
        path: 'records',
        name: 'WeeklyRecords',
        component: () => import('@/views/inspection/weekly/index.vue'),
        meta: { title: '记录查看与审核', permissions: ['weekly:view'] }
      },
      {
        path: 'detail',
        name: 'WeeklyDetail',
        component: () => import('@/views/inspection/weekly/index.vue'),
        meta: { title: '记录详情', permissions: ['weekly:detail'] }
      },
      {
        path: 'checklist',
        name: 'WeeklyChecklist',
        component: () => import('@/views/inspection/weekly/index.vue'),
        meta: { title: '周排查检查表', permissions: ['weekly:check'] }
      },
      {
        path: 'create',
        name: 'WeeklyCreate',
        component: () => import('@/views/inspection/weekly/index.vue'),
        meta: { title: '新建周排查检查表', permissions: ['weekly:create'], hidden: true }
      },
      {
        path: 'score',
        name: 'WeeklyScore',
        component: () => import('@/views/inspection/weekly/index.vue'),
        meta: { title: '分数统计', permissions: ['weekly:score'] }
      }
    ]
  },
  {
    path: '/monthly-dispatch',
    component: () => import('@/layout/index.vue'),
    redirect: '/monthly-dispatch/report-records',
    meta: { title: '月调度', icon: 'DataAnalysis' },
    children: [
      {
        path: 'report-export',
        name: 'MonthlyReportExport',
        component: () => import('@/views/inspection/monthly/index.vue'),
        meta: { title: '月调度报告导出', permissions: ['monthly:export'], isDeveloping: true }
      },
      {
        path: 'report-records',
        name: 'MonthlyReportRecords',
        component: () => import('@/views/inspection/monthly/index.vue'),
        meta: { title: '月调度报告记录', permissions: ['monthly:records'], isDeveloping: true }
      }
    ]
  },
  {
    path: '/joint-inspection',
    component: () => import('@/layout/index.vue'),
    redirect: '/joint-inspection/records',
    meta: { title: '联合巡检', icon: 'CameraFilled' },
    children: [
      {
        path: 'records',
        name: 'JointRecords',
        component: () => import('@/views/inspection/joint/index.vue'),
        meta: { title: '记录查看与审核', permissions: ['joint:view'], isDeveloping: true }
      },
      {
        path: 'detail',
        name: 'JointDetail',
        component: () => import('@/views/inspection/joint/index.vue'),
        meta: { title: '记录详情', permissions: ['joint:detail'], isDeveloping: true }
      },
      {
        path: 'checklist',
        name: 'JointChecklist',
        component: () => import('@/views/inspection/joint/index.vue'),
        meta: { title: '联合巡检检查表', permissions: ['joint:check'], isDeveloping: true }
      },
      {
        path: 'create',
        name: 'JointCreate',
        component: () => import('@/views/inspection/joint/index.vue'),
        meta: { title: '新建联合巡检检查表', permissions: ['joint:create'], hidden: true, isDeveloping: true }
      },
      {
        path: 'score',
        name: 'JointScore',
        component: () => import('@/views/inspection/joint/index.vue'),
        meta: { title: '分数统计', permissions: ['joint:score'], isDeveloping: true }
      }
    ]
  },
  {
    path: '/video-center',
    component: () => import('@/layout/index.vue'),
    redirect: '/video-center/view',
    meta: { title: '视频集控中心', icon: 'VideoCamera' },
    children: [
      {
        path: 'view',
        name: 'VideoView',
        component: () => import('@/views/video/wall/index.vue'),
        meta: { title: '视频查看', permissions: ['video:view'], isDeveloping: true }
      },
      {
        path: 'inspection',
        name: 'VideoInspection',
        component: () => import('@/views/video/wall/index.vue'),
        meta: { title: '视频巡检', permissions: ['video:inspection'], isDeveloping: true }
      },
      {
        path: 'records',
        name: 'VideoRecords',
        component: () => import('@/views/video/wall/index.vue'),
        meta: { title: '记录查看与审核', permissions: ['video:records'], isDeveloping: true }
      },
      {
        path: 'detail',
        name: 'VideoDetail',
        component: () => import('@/views/video/wall/index.vue'),
        meta: { title: '记录详情', permissions: ['video:detail'], isDeveloping: true }
      },
      {
        path: 'checklist',
        name: 'VideoChecklist',
        component: () => import('@/views/video/wall/index.vue'),
        meta: { title: '视频巡检检查表', permissions: ['video:check'], isDeveloping: true }
      },
      {
        path: 'score',
        name: 'VideoScore',
        component: () => import('@/views/video/wall/index.vue'),
        meta: { title: '分数统计', permissions: ['video:score'], isDeveloping: true }
      }
    ]
  },
  {
    path: '/ledger',
    component: () => import('@/layout/index.vue'),
    redirect: '/ledger/records',
    meta: { title: '电子台账', icon: 'Notebook' },
    children: [
      {
        path: 'records',
        name: 'LedgerRecords',
        component: () => import('@/views/canteen/list/index.vue'),
        meta: { title: '电子台账记录', permissions: ['ledger:view'], isDeveloping: true }
      },
      {
        path: 'templates',
        name: 'LedgerTemplates',
        component: () => import('@/views/ledger/templates/index.vue'),
        meta: { title: '电子台账模板', permissions: ['ledger:template'], isDeveloping: true }
      },
      {
        path: 'designer',
        name: 'LedgerDesigner',
        component: () => import('@/views/ledger/designer/index.vue'),
        meta: { title: '智能台账设计器', permissions: ['ledger:design'], isDeveloping: true }
      }
    ]
  }
]
