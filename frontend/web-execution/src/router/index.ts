import { createRouter, createWebHistory } from 'vue-router'
import { constantRoutes, asyncRoutes } from './routes'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'

const router = createRouter({
  history: createWebHistory(),
  routes: [...constantRoutes, ...asyncRoutes] // 目前先全量合并，后续做动态权限分配
})

export default router

router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()
  const token = userStore.token

  // 开发中功能拦截
  if (to.meta.isDeveloping) {
    ElMessage.warning('功能开发中，敬请期待...')
    next(false)
    return
  }

  if (token) {
    if (to.path === '/login') {
      next({ path: '/' })
    } else {
      // 简单的权限判定逻辑
      const requiredPermissions = to.meta.permissions as string[]
      if (!requiredPermissions || userStore.hasAnyPermission(requiredPermissions)) {
        next()
      } else {
        // console.log('Permission denied:', {
        //   path: to.path,
        //   required: requiredPermissions,
        //   userPermissions: userStore.permissions
        // })
        next({ path: '/403' }) // 无权限页面
      }
    }
  } else {
    if (to.path === '/login') {
      next()
    } else {
      next('/login')
    }
  }
})
