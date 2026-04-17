import { createRouter, createWebHistory } from 'vue-router'
import { constantRoutes, asyncRoutes } from './routes'
import { getRegToken } from '@/utils/auth-storage'

const router = createRouter({
  history: createWebHistory(),
  routes: [...constantRoutes, ...asyncRoutes]
})

const WHITE_LIST = ['/login', '/403', '/404']

router.beforeEach((to, _from, next) => {
  // 设置页面标题
  const title = to.meta.title as string
  document.title = title ? `${title} - 智慧食安监管平台` : '智慧食安监管平台'

  const token = getRegToken()

  if (token) {
    // 已登录：不允许再进登录页，跳到首页
    if (to.path === '/login') {
      next({ path: '/' })
    } else {
      next()
    }
  } else {
    // 未登录：白名单直接放行，其他跳登录页
    if (WHITE_LIST.includes(to.path)) {
      next()
    } else {
      next({ path: '/login' })
    }
  }
})

export default router
