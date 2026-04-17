# 认证中心与中间件 (Auth Core) - 前端对接文档

## 核心约定

### 🔑 Token 传递方式

**重要**：**固定使用 Header 传递** Token，不得使用 Cookie。

```http
Authorization: Bearer <token>
```

## 技术实现

### AuthMiddleware 处理流程

1. **请求拦截**：前端发送请求时，在 Header 中添加 `Authorization: Bearer <token>`
2. **Token 解析**：AuthMiddleware 解析 Header 中的 Bearer Token
3. **Token 验证**：
   - Token 有效：设置用户信息到上下文，继续处理请求
   - Token 无效：直接返回 401 错误
4. **响应返回**：后端返回响应给前端

## 前端实现

### 1. 登录流程

#### 1.1 登录请求

**接口**：`POST /auth/login`

**请求参数**：
```json
{
  "username": "admin",
  "password": "py427123"
}
```

**响应**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "1",
    "username": "admin",
    "tenant_id": "tenant_123",
    "role_type": "admin",
    "scope": "admin"
  }
}
```

#### 1.2 存储 Token

**推荐**：使用 `localStorage` 或 `sessionStorage` 存储 Token

```javascript
// 登录成功后存储 Token
localStorage.setItem('access_token', response.access_token);
localStorage.setItem('refresh_token', response.refresh_token);
localStorage.setItem('user', JSON.stringify(response.user));
```

### 2. Token 刷新机制

#### 2.1 刷新 Token

**接口**：`POST /auth/refresh`

**请求参数**：
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 2.2 自动刷新 Token

**推荐**：在请求拦截器中检查 Token 过期时间，在过期前自动刷新

```javascript
// 示例：使用 Axios 的请求拦截器
axios.interceptors.request.use(async (config) => {
  // 获取存储的 Token
  const accessToken = localStorage.getItem('access_token');
  
  if (accessToken) {
    // 添加到请求头
    config.headers['Authorization'] = `Bearer ${accessToken}`;
    
    // 检查 Token 是否即将过期
    const tokenExpiry = getTokenExpiry(accessToken);
    const now = Date.now() / 1000;
    
    // 如果 Token 将在 5 分钟内过期，刷新 Token
    if (tokenExpiry - now < 300) {
      await refreshToken();
      // 更新请求头中的 Token
      const newAccessToken = localStorage.getItem('access_token');
      config.headers['Authorization'] = `Bearer ${newAccessToken}`;
    }
  }
  
  return config;
});

// 示例：使用 Axios 的响应拦截器
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // 如果是 401 错误且不是刷新 Token 的请求
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // 刷新 Token
        await refreshToken();
        
        // 更新请求头中的 Token 并重试
        const newAccessToken = localStorage.getItem('access_token');
        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
        
        return axios(originalRequest);
      } catch (refreshError) {
        // 刷新 Token 失败，跳转到登录页
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// 刷新 Token 函数
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  
  const response = await axios.post('/auth/refresh', {
    refresh_token: refreshToken
  });
  
  // 更新存储的 Token
  localStorage.setItem('access_token', response.data.access_token);
  localStorage.setItem('refresh_token', response.data.refresh_token);
}

// 获取 Token 过期时间
function getTokenExpiry(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp;
  } catch (error) {
    return 0;
  }
}
```

### 3. API 调用示例

#### 3.1 带 Token 的 API 调用

```javascript
// 示例：获取用户信息
async function getUserInfo() {
  try {
    const response = await axios.get('/auth/me');
    return response.data;
  } catch (error) {
    console.error('获取用户信息失败:', error);
    throw error;
  }
}

// 示例：创建用户
async function createUser(userData) {
  try {
    const response = await axios.post('/users', userData);
    return response.data;
  } catch (error) {
    console.error('创建用户失败:', error);
    throw error;
  }
}
```

#### 3.2 上传文件

```javascript
// 示例：上传头像
async function uploadAvatar(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await axios.post('/user/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  } catch (error) {
    console.error('上传头像失败:', error);
    throw error;
  }
}
```

### 4. 错误处理

#### 4.1 常见错误码

| 状态码 | 含义 | 处理方式 |
|--------|------|----------|
| 400 | 请求参数错误 | 显示错误信息给用户 |
| 401 | 未授权/Token 无效 | 跳转到登录页 |
| 403 | 权限不足 | 显示权限不足提示 |
| 404 | 资源不存在 | 显示资源不存在提示 |
| 500 | 服务器内部错误 | 显示服务器错误提示 |

#### 4.2 全局错误处理

```javascript
// 示例：全局错误处理
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const message = error.response?.data?.detail || '操作失败';
    
    switch (status) {
      case 401:
        // Token 无效，跳转到登录页
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        break;
      case 403:
        // 权限不足
        alert('权限不足，无法执行此操作');
        break;
      case 404:
        // 资源不存在
        alert('请求的资源不存在');
        break;
      case 500:
        // 服务器错误
        alert('服务器内部错误，请稍后重试');
        break;
      default:
        // 其他错误
        alert(message);
    }
    
    return Promise.reject(error);
  }
);
```

### 5. 登出流程

#### 5.1 登出操作

**接口**：`POST /auth/logout`

**实现**：
```javascript
async function logout() {
  try {
    await axios.post('/auth/logout');
  } catch (error) {
    console.error('登出失败:', error);
  } finally {
    // 清除存储的 Token 和用户信息
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    // 跳转到登录页
    window.location.href = '/login';
  }
}
```

### 6. 用户信息管理

#### 6.1 获取当前用户信息

**接口**：`GET /auth/me`

**响应**：
```json
{
  "id": "1",
  "username": "admin",
  "tenant_id": "tenant_123",
  "role_type": "admin",
  "created_at": "2023-01-01T00:00:00Z"
}
```

#### 6.2 获取用户权限

**接口**：`GET /auth/me/permissions`

**响应**：
```json
{
  "permissions": [
    "user:read",
    "user:write",
    "organization:read",
    "organization:write"
  ]
}
```

## 最佳实践

### 1. Token 存储

- **推荐**：使用 `localStorage` 存储 Token
- **注意**：避免在 localStorage 中存储敏感信息
- **替代方案**：对于安全性要求较高的应用，可以使用 `sessionStorage` 或内存存储

### 2. Token 管理

- **自动刷新**：实现 Token 自动刷新机制，避免用户频繁登录
- **过期检查**：在发送请求前检查 Token 是否即将过期
- **错误处理**：正确处理 Token 无效的情况，及时跳转到登录页

### 3. 安全措施

- **HTTPS**：确保所有请求使用 HTTPS
- **Token 泄露**：避免在控制台输出 Token
- **CORS 配置**：后端已配置 CORS，前端无需特殊处理

### 4. 性能优化

- **请求拦截器**：使用请求拦截器统一添加 Token
- **响应拦截器**：使用响应拦截器统一处理错误
- **缓存**：合理缓存用户信息，减少重复请求

## 前端框架示例

### React 示例

```javascript
// src/utils/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
});

// 请求拦截器
api.interceptors.request.use(async (config) => {
  const accessToken = localStorage.getItem('access_token');
  if (accessToken) {
    config.headers['Authorization'] = `Bearer ${accessToken}`;
  }
  return config;
});

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // 处理 401 错误
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// 使用示例
import api from './utils/api';

async function login(username, password) {
  const response = await api.post('/auth/login', { username, password });
  localStorage.setItem('access_token', response.data.access_token);
  localStorage.setItem('refresh_token', response.data.refresh_token);
  return response.data;
}
```

### Vue 示例

```javascript
// src/utils/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
});

// 请求拦截器
api.interceptors.request.use(async (config) => {
  const accessToken = localStorage.getItem('access_token');
  if (accessToken) {
    config.headers['Authorization'] = `Bearer ${accessToken}`;
  }
  return config;
});

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // 处理 401 错误
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// 使用示例
import api from './utils/api';

export async function login(username, password) {
  const response = await api.post('/auth/login', { username, password });
  localStorage.setItem('access_token', response.data.access_token);
  localStorage.setItem('refresh_token', response.data.refresh_token);
  return response.data;
}
```

### Angular 示例

```typescript
// src/app/services/api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private baseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    const accessToken = localStorage.getItem('access_token');
    let headers = new HttpHeaders();
    if (accessToken) {
      headers = headers.set('Authorization', `Bearer ${accessToken}`);
    }
    return headers;
  }

  get<T>(url: string): Observable<T> {
    return this.http.get<T>(`${this.baseUrl}${url}`, {
      headers: this.getHeaders()
    }).pipe(
      catchError(this.handleError)
    );
  }

  post<T>(url: string, data: any): Observable<T> {
    return this.http.post<T>(`${this.baseUrl}${url}`, data, {
      headers: this.getHeaders()
    }).pipe(
      catchError(this.handleError)
    );
  }

  private handleError(error: any) {
    if (error.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return throwError(error);
  }
}

// 使用示例
import { ApiService } from './services/api.service';

export class AuthService {
  constructor(private apiService: ApiService) {}

  login(username: string, password: string) {
    return this.apiService.post('/auth/login', { username, password });
  }
}
```

## API 文档

### 访问方式

启动后端服务后，访问以下地址查看完整 API 文档：

```
http://localhost:8000/docs
```

### 核心接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/auth/login` | POST | 登录 |
| `/auth/refresh` | POST | 刷新 Token |
| `/auth/logout` | POST | 登出 |
| `/auth/me` | GET | 获取当前用户信息 |
| `/auth/me/permissions` | GET | 获取当前用户权限 |
| `/users` | GET | 获取用户列表 |
| `/users` | POST | 创建用户 |
| `/user` | GET | 获取当前用户详情 |
| `/user` | PUT | 更新当前用户信息 |
| `/user/{id}/status` | PATCH | 更新用户状态 |
| `/user/avatar` | POST | 上传头像 |
| `/organizations` | GET | 获取组织列表 |
| `/organizations` | POST | 创建组织 |
| `/organization/{id}` | GET | 获取组织详情 |
| `/organization/{id}` | PUT | 更新组织信息 |
| `/organization/{id}` | DELETE | 删除组织 |

## 常见问题

### Q1: 为什么要使用 Header 传递 Token 而不是 Cookie？

**A**：使用 Header 传递 Token 有以下优势：
- 跨域支持更好
- 避免 CSRF 攻击
- 更灵活，可用于不同类型的客户端
- 符合 RESTful API 设计规范

### Q2: Token 过期后如何处理？

**A**：实现 Token 自动刷新机制：
1. 存储 `refresh_token`（长效）和 `access_token`（短效）
2. 当 `access_token` 过期时，使用 `refresh_token` 刷新
3. 刷新失败时，跳转到登录页

### Q3: 如何处理多个标签页的登录状态同步？

**A**：可以使用 `localStorage` 的 `storage` 事件监听 Token 变化：

```javascript
window.addEventListener('storage', (event) => {
  if (event.key === 'access_token' || event.key === 'refresh_token') {
    // 更新当前标签页的 Token
    // 或跳转到登录页
  }
});
```

### Q4: 如何提高 Token 的安全性？

**A**：
- 使用 HTTPS 传输
- 设置合理的 Token 过期时间
- 实现 Token 刷新机制
- 避免在 localStorage 中存储敏感信息
- 后端实现 Token 黑名单机制

### Q5: 前端如何处理网络异常？

**A**：
- 实现请求重试机制
- 显示网络异常提示
- 监控网络状态变化

## 联系方式

如有问题，请联系：
- **谢传宇**（认证中心与中间件负责人）
- 邮箱：[你的邮箱]
- 电话：[你的电话]
