# Safefood Platform - Mobile App

食品安全监管平台移动端应用，基于 **uni-app + Vue 3 + TypeScript** 构建，支持多端发布（H5、微信小程序、支付宝小程序、App 等）。

## 目录结构

```
app-mobile/
├── common/                 # 公共模块（组件、工具、类型定义等）
│   ├── api/               # 公共 API 接口
│   ├── components/        # 公共组件
│   ├── types/             # TypeScript 类型定义
│   └── utils/             # 工具函数
├── app-execution/         # 执行端 App（食堂/企业使用）
│   ├── src/
│   │   ├── pages/        # 页面组件
│   │   ├── static/       # 静态资源
│   │   └── ...
│   └── package.json
├── app-admin/             # 监管端 App（监管部门使用）
│   ├── src/
│   │   ├── pages/        # 页面组件
│   │   ├── static/       # 静态资源
│   │   └── ...
│   └── package.json
└── README.md
```

## 技术栈

- **框架**: uni-app (Vue 3)
- **语言**: TypeScript 4.9+
- **构建工具**: Vite 5.2 + @dcloudio/vite-plugin-uni
- **UI**: uni-ui + 自定义组件
- **状态管理**: Pinia
- **样式**: SCSS
- **类型检查**: vue-tsc

## 环境要求

- **Node.js**: >= 18.0.0
- **npm**: >= 9.0.0
- **HBuilderX** (可选): 用于 App 打包和小程序预览
- **微信开发者工具** (可选): 用于微信小程序开发

## 快速开始

### 1. 安装依赖

```bash
# 执行端
cd app-execution
npm install

# 监管端
cd app-admin
npm install
```

### 2. 开发模式

```bash
# H5 开发（浏览器访问）
npm run dev:h5

# 微信小程序开发
npm run dev:mp-weixin

# App 开发（需 HBuilderX 或 uni-app CLI）
npm run dev:app

# 其他平台
npm run dev:mp-alipay     # 支付宝小程序
npm run dev:mp-baidu      # 百度小程序
npm run dev:mp-toutiao    # 头条小程序
```

### 3. 构建发布

```bash
# H5 构建
npm run build:h5

# 微信小程序构建
npm run build:mp-weixin

# App 构建
npm run build:app

# 其他平台
npm run build:mp-alipay
npm run build:mp-baidu
```

### 4. 类型检查

```bash
npm run type-check
```

## 平台支持

| 平台 | 命令 | 说明 |
|------|------|------|
| H5 | `dev:h5` / `build:h5` | 网页版，支持 SSR |
| 微信小程序 | `dev:mp-weixin` / `build:mp-weixin` | 需配置小程序 AppID |
| 支付宝小程序 | `dev:mp-alipay` / `build:mp-alipay` | 需配置小程序 AppID |
| 百度小程序 | `dev:mp-baidu` / `build:mp-baidu` | - |
| 头条小程序 | `dev:mp-toutiao` / `build:mp-toutiao` | - |
| App (Android/iOS) | `dev:app` / `build:app` | 需 HBuilderX 打包 |
| 快应用 | `dev:quickapp-webview` | - |

## 项目配置

### manifest.json

配置应用名称、版本、权限、各平台参数等：

```json
{
  "name": "食品安全监管平台",
  "versionName": "1.0.0",
  "versionCode": "100",
  "app-plus": { /* App 配置 */ },
  "mp-weixin": { /* 微信小程序配置 */ }
}
```

### pages.json

配置页面路由、导航栏样式、下拉刷新等：

```json
{
  "pages": [
    {
      "path": "pages/login/login",
      "style": {
        "navigationBarTitleText": "登录"
      }
    }
  ],
  "globalStyle": {
    "navigationBarTextStyle": "black",
    "navigationBarTitleText": "食品安全监管平台",
    "navigationBarBackgroundColor": "#F8F8F8"
  }
}
```

### 环境变量

在 `uni.scss` 或通过 `process.env` 访问环境变量：

```bash
# .env
VITE_APP_BASE_API=http://localhost:8000
VITE_APP_VERSION=1.0.0
```

## 开发规范

### 目录命名

- 页面目录：小写 + 连字符（如 `user-info/`）
- 组件目录：PascalCase（如 `UserProfile/`）
- 文件命名：与目录名一致（如 `user-info.vue`）

### 代码风格

- 使用 `<script setup lang="ts">` 语法
- 始终定义接口类型，避免使用 `any`
- 使用 `@/` 路径别名导入本地模块
- 遵循 Vue 3 Composition API 最佳实践

```typescript
// 示例：定义接口并使用
interface UserInfo {
  id: number
  username: string
  phone?: string
}

const user = ref<UserInfo>({
  id: 1,
  username: 'admin'
})
```

### 组件开发

公共组件放在 `common/components/`，业务组件放在各自应用的 `components/` 目录。

```vue
<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  title: string
  visible: boolean
}

const props = defineProps<Props>()
const emit = defineEmits(['update:visible', 'confirm'])
</script>
```

### API 调用

使用 `common/api/` 中的封装方法，统一处理请求拦截和响应格式：

```typescript
import { request } from '@/api'

export function login(data: LoginParams) {
  return request<LoginResult>({
    url: '/auth/login',
    method: 'post',
    data
  })
}
```

## 多端适配

### 条件编译

使用 uni-app 条件编译语法处理平台差异：

```vue
<template>
  <!-- #ifdef MP-WEIXIN -->
  <view>微信小程序特有内容</view>
  <!-- #endif -->
  
  <!-- #ifdef H5 -->
  <div>H5 特有内容</div>
  <!-- #endif -->
</template>

<script>
// #ifdef APP-PLUS
console.log('App 端逻辑')
// #endif
</script>
```

### 平台差异化配置

在 `manifest.json` 中为不同平台配置特定参数：

```json
{
  "mp-weixin": {
    "appid": "your-wechat-appid",
    "setting": {
      "urlCheck": false
    }
  },
  "app-plus": {
    "modules": {
      "Camera": {}
    }
  }
}
```

## 调试与预览

### H5 调试

在浏览器中打开开发服务器地址（默认 `http://localhost:5173`），使用浏览器 DevTools 调试。

### 小程序预览

1. 运行对应平台的开发命令（如 `npm run dev:mp-weixin`）
2. 使用微信开发者工具导入生成的 `dist/dev/mp-weixin` 目录
3. 在开发者工具中预览和调试

### App 调试

**方法一：HBuilderX**
1. 在 HBuilderX 中打开项目
2. 连接手机或模拟器
3. 点击"运行" → "运行到手机或模拟器"

**方法二：uni-app CLI**
```bash
npx cross-env UNI_PLATFORM=app-plus vite build --mode development
```

## 打包发布

### App 打包

1. 在 HBuilderX 中配置证书和包名
2. 选择"发行" → "原生 App-云打包"
3. 等待打包完成后下载 APK/IPA

### 小程序发布

1. 运行构建命令（如 `npm run build:mp-weixin`）
2. 在微信开发者工具中上传代码
3. 登录小程序管理后台提交审核

## 常见问题

### 依赖安装失败

```bash
# 清除缓存后重试
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### TypeScript 类型错误

运行类型检查查看详细错误：

```bash
npm run type-check
```

### 小程序编译错误

检查 `manifest.json` 中的平台配置是否正确，确保已安装对应平台的开发者工具。

### App 热更新失败

检查 `versionCode` 是否递增，确保打包配置正确。

## 相关文档

- [uni-app 官方文档](https://uniapp.dcloud.net.cn/)
- [Vue 3 文档](https://vuejs.org/)
- [TypeScript 文档](https://www.typescriptlang.org/)
- [监管端页面架构说明](./app-admin/监管端文档描述.md)

## 开发团队联系方式

如有问题请联系开发团队或提交 Issue。
