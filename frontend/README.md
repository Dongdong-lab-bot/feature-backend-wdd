# 智慧食安管理平台 - 前端

> 基于 Vue 3 + TypeScript + Vite + Element Plus 的食品安全管理平台前端

## 技术栈

- **框架**: Vue 3.4 + TypeScript
- **构建工具**: Vite 5
- **UI 组件库**: Element Plus 2.5
- **状态管理**: Pinia 2.1
- **路由**: Vue Router 4.2
- **HTTP 客户端**: Axios 1.6
- **图表**: ECharts 5.4
- **样式**: SCSS

## 项目结构

```
frontend/
├── common/                    # 公共模块（共享组件、工具、类型）
│   ├── src/
│   │   ├── api/               # 公共 API 封装
│   │   ├── types/             # TypeScript 类型定义
│   │   └── utils/             # 工具函数
│   ├── package.json
│   └── tsconfig.json
├── web-execution/             # 执行端 Web 应用
│   ├── src/
│   │   ├── api/               # API 接口调用
│   │   ├── components/        # 可复用组件
│   │   ├── views/             # 页面组件
│   │   ├── store/             # Pinia 状态管理
│   │   ├── utils/             # 工具函数
│   │   └── App.vue
│   ├── .env.development       # 开发环境变量
│   ├── vite.config.ts         # Vite 配置
│   └── package.json
├── web-admin/                 # 监管端 Web 应用
│   ├── src/                   # 结构同 web-execution
│   ├── .env.development
│   ├── vite.config.ts
│   └── package.json
└── 食安 UI/                    # 设计资源
```

## 快速开始

### 环境要求

- Node.js >= 18
- npm >= 9

### 安装依赖

```bash
# 安装公共模块依赖
cd frontend/common && npm install

# 安装执行端依赖
cd frontend/web-execution && npm install

# 安装监管端依赖
cd frontend/web-admin && npm install
```

### 开发模式

```bash
# 启动执行端开发服务器（端口默认由 Vite 分配）
cd frontend/web-execution && npm run dev

# 启动监管端开发服务器
cd frontend/web-admin && npm run dev
```

### 生产构建

```bash
# 构建执行端
cd frontend/web-execution && npm run build

# 构建监管端
cd frontend/web-admin && npm run build

# 预览生产构建
npm run preview
```

## 配置说明

### 环境变量

在 `.env.development` 或 `.env.production` 中配置：

```env
# API 基础路径（开发环境使用代理）
VITE_APP_BASE_API=/api
```

### Vite 代理配置

开发环境下，`vite.config.ts` 已配置代理转发到后端服务：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

## 开发规范

### 目录命名

- 小写字母
- 单词间用短横线连接（kebab-case）

### TypeScript

- 使用严格类型检查，避免使用 `any`
- 为所有 API 请求/响应定义接口
- 使用 `@/` 路径别名导入模块

```typescript
// 示例：定义 API 接口
export interface LoginParams {
  username: string
  password: string
  app_client: string
}

export function login(data: LoginParams) {
  return request<LoginResult>({
    url: '/auth/login',
    method: 'post',
    data
  })
}
```

### Vue 组件

- 使用 `<script setup lang="ts">` 语法
- 组件文件使用 PascalCase 命名
- 页面组件放在 `views/`，可复用组件放在 `components/`

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'

const count = ref(0)
const doubleCount = computed(() => count.value * 2)
</script>
```

### API 请求

遵循统一的响应格式：

```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

请求头需包含：

- `Authorization: Bearer <token>`
- `X-App-Client: <client_id>`

## 常用命令

| 命令 | 说明 |
|------|------|
| `npm run dev` | 启动开发服务器（Vite） |
| `npm run build` | 生产构建（类型检查 + Vite） |
| `npm run preview` | 预览生产构建 |

## 状态管理 (Pinia)

```typescript
// store/modules/user.ts
import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: '',
    userInfo: null
  }),
  actions: {
    setToken(token: string) {
      this.token = token
    }
  }
})
```

## 注意事项

1. **多租户隔离**: 前端需配合后端进行租户边界控制
2. **Token 管理**: 登录后需在请求头携带 JWT token
3. **环境配置**: 不要提交 `.env` 等包含敏感信息的文件
4. **路径别名**: 使用 `@/` 而非相对路径导入模块

## 后端服务

启动后端服务（端口 8000）：

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 更多信息

- [Vue 3 文档](https://vuejs.org/)
- [TypeScript 文档](https://www.typescriptlang.org/)
- [Vite 文档](https://vitejs.dev/)
- [Element Plus 文档](https://element-plus.org/)
- [Pinia 文档](https://pinia.vuejs.org/)
