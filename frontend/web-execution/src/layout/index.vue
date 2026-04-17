<template>
  <Layout
    system-title="智慧食安执行平台"
    :user-name="userName"
    :menu-routes="menuRoutes"
    @logout="handleLogout"
  >
    <router-view />
  </Layout>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { asyncRoutes } from '@/router/routes'
import Layout from '@common/layout/Layout.vue'

const router = useRouter()
const userStore = useUserStore()

const userName = computed(() => userStore.nickname || userStore.username)
const menuRoutes = computed(() =>
  asyncRoutes
    .filter(r => !r.meta?.hidden)
    .map(r => ({
      ...r,
      children: r.children?.filter(c => !c.meta?.hidden)
    }))
)

const handleLogout = async () => {
  // [Fix] 退出登录时调用后端 /auth/logout 接口（callApi=true），确保服务端 token 失效
  await userStore.logout(true)
  router.push('/login')
}
</script>
