# AdminLayout 通用布局组件使用说明

共享布局组件，适用于监管端和执行端项目。

## 使用方式

### 1. 在项目中引入

```vue
<template>
  <AdminLayout
    system-title="智慧食安监管平台"
    :user-name="userName"
    :menu-routes="menuRoutes"
    @logout="handleLogout"
  >
    <router-view />
  </AdminLayout>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '@common/layout/AdminLayout.vue'
import { useUserStore } from '@/store/user'
import { asyncRoutes } from '@/router/routes'

const router = useRouter()
const userStore = useUserStore()

const userName = computed(() => userStore.nickname || userStore.username || '管理员')
const menuRoutes = computed(() => asyncRoutes.filter(r => !r.meta?.hidden))

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>
```

### 2. Props 说明

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| systemTitle | string | '智慧食安管理平台' | 系统标题 |
| userName | string | '用户' | 当前用户名 |
| menuRoutes | RouteRecordRaw[] | [] | 菜单路由配置 |

### 3. Events 说明

| 事件名 | 说明 | 参数 |
|--------|------|------|
| logout | 用户点击退出登录时触发 | - |

## 路由配置

菜单通过 `menuRoutes` prop 传入路由配置，支持二级菜单。

### 路由结构示例

```typescript
const routes = [
  {
    path: '/system',
    meta: { title: '系统管理' },
    children: [
      {
        path: 'user',
        meta: { title: '用户管理' }
      },
      {
        path: 'role',
        meta: { title: '角色管理' }
      }
    ]
  }
]
```

### 路由配置规则

- 父级路由的 `meta.title` 作为分组标题
- 子路由的 `meta.title` 作为菜单项
- 设置 `meta.hidden = true` 可隐藏整个分组

## 不同项目差异化配置

监管端和执行端通过传入不同的 `menuRoutes` 实现差异化：

```typescript
// 监管端 - 包含用户管理
const adminRoutes = [
  { path: '/system', meta: { title: '系统管理' }, children: [...] },
  { path: '/canteen', meta: { title: '食堂管理' }, children: [...] }
]

// 执行端 - 不包含用户管理
const executionRoutes = [
  { path: '/canteen', meta: { title: '食堂管理' }, children: [...] }
]
```

## 注意事项

1. 确保项目已配置 `@common` 路径别名
2. 路由配置需包含 `meta.title` 字段
3. slot 默认放置 `<router-view />`，用于渲染页面内容
