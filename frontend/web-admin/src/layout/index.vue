<template>
  <Layout
    system-title="智慧食安监管平台"
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

const userName = computed(() => userStore.nickname || userStore.username || '管理员')
const menuRoutes = computed(() => {
  return asyncRoutes
    .filter((route) => !route.meta?.hidden)
    .map((route) => ({
      ...route,
      children: (route.children || []).filter((child) => !child.meta?.hidden)
    }))
})

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>
