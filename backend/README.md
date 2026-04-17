# Safefood Platform Backend

智慧食安平台后端服务，基于 FastAPI + SQLAlchemy 2.0 (async) 构建。

## 技术栈

- **框架**: FastAPI 0.128
- **数据库 ORM**: SQLAlchemy 2.0 (async)
- **数据库**: SQLite (开发环境), PostgreSQL/MySQL (生产环境)
- **迁移工具**: Alembic
- **认证**: JWT (python-jose)
- **数据验证**: Pydantic v2
- **测试**: pytest + pytest-asyncio
- **任务调度**: APScheduler

## 项目结构

```
backend/
├── app/
│   ├── api/              # API 路由注册
│   ├── core/             # 配置、安全、依赖、中间件
│   ├── db/               # 数据库会话、模型、混入类
│   ├── modules/          # 业务模块
│   │   ├── device/       # 设备管理
│   │   ├── inspection/   # 巡检管理
│   │   ├── ledger/       # 台账管理
│   │   ├── user/         # 用户管理
│   │   └── video/        # 视频监控
│   └── main.py           # 应用入口
├── tests/                # 测试文件
├── alembic/              # 数据库迁移
├── requirements.txt      # 依赖清单
└── pytest.ini           # 测试配置
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env` 文件并修改配置：

```bash
# 数据库连接 (SQLite 开发环境)
DATABASE_URL=sqlite+aiosqlite:///./dev.db

# JWT 配置 (生产环境请修改)
JWT_SECRET_KEY=your-secret-key-please-change
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

生产环境数据库示例：
```bash
# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/safefood

# MySQL
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/safefood
```

### 3. 启动开发服务器

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档。

### 4. 数据库迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "描述信息"

# 应用迁移
alembic upgrade head

# 回滚到上一版本
alembic downgrade -1
```

## 开发指南

### 运行测试

```bash
# 运行所有测试
pytest

# 运行单个测试文件
pytest tests/test_form_engine.py

# 运行单个测试函数 (推荐)
pytest tests/test_form_engine.py::test_name

# 按模式匹配测试
pytest -k "test_acceptance"

# 详细输出
pytest -v
pytest -vv -s
```

### 代码规范

**导入顺序**: 标准库 → 第三方库 → 本地模块

```python
from typing import Optional
from fastapi import APIRouter
from app.modules.user.service import get_user
```

**类型注解**: 所有函数必须标注参数和返回值类型

```python
async def get_user_by_id(user_id: int, db: AsyncSession) -> Optional[User]:
    ...
```

**命名规范**:
- 变量/函数: `snake_case`
- 类: `PascalCase`
- 常量: `UPPER_SNAKE_CASE`
- 私有成员: `_prefix`

**API 响应格式**:

```python
from app.core.response import ok

# 成功响应
return ok(data={"id": 1}, msg="success")

# 错误响应
return JSONResponse(
    status_code=400,
    content=ok(msg="invalid request", code=400)
)
```

### 多租户支持

所有业务模型继承 `TenantMixin`，自动注入 `tenant_id` 字段：

```python
class User(Base, TenantMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
```

使用 `UserContext` 获取当前租户/用户：

```python
from app.db.user_context import get_current_user

async def get_user_data(user: User = Depends(get_current_user)):
    return {"username": user.username}
```

### 异步编程

所有路由处理器必须使用 `async def`：

```python
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    users = await db.execute(select(User))
    return ok(data=users.scalars().all())
```

## API 使用

### 认证请求

所有受保护的 API 需要携带以下请求头：

```
Authorization: Bearer <jwt_token>
X-App-Client: <client_identifier>
```

### 客户端示例

```python
import httpx

async def call_api():
    headers = {
        "Authorization": "Bearer your_token",
        "X-App-Client": "web-execution"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/users",
            headers=headers
        )
        return response.json()
```

## 核心模块说明

### 业务模块

| 模块 | 说明 |
|------|------|
| `user` | 用户管理、认证授权 |
| `device` | 设备接入与管理 |
| `inspection` | 巡检任务与记录 |
| `ledger` | 电子台账管理 |
| `video` | 视频监控集成 |

### 中间件

- `AuthMiddleware`: 统一处理 JWT 认证和用户上下文
- `EventHandlerASGIMiddleware`: 事件分发处理
- `CORSMiddleware`: 跨域请求控制

### 安全特性

- JWT Token 认证
- 多租户数据隔离（Security Guard）
- 全异步数据库操作
- 统一异常处理

## 生产部署

### 环境要求

- Python 3.9+
- PostgreSQL 13+ / MySQL 8.0+
- Redis (可选，用于缓存)

### 启动命令

```bash
# 生产环境不启用热重载
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 或使用 gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 安全配置

1. 修改 `JWT_SECRET_KEY` 为强随机字符串
2. 配置 CORS 允许特定域名
3. 启用 HTTPS
4. 数据库连接使用加密凭证

## 常见问题

**Q: 如何创建新的业务模块？**

A: 在 `app/modules/` 下创建新目录，包含 `api.py`、`models.py`、`schemas.py`、`service.py` 四个文件，然后在 `app/api/__init__.py` 中注册路由。

**Q: 数据库迁移失败怎么办？**

A: 检查 `alembic/versions/` 中的迁移脚本，确保没有冲突。开发环境可删除 `dev.db` 重新迁移。

**Q: 如何调试异步代码？**

A: 使用 `pytest -s` 输出 print 语句，或在 VSCode 中配置 async 调试。

## 贡献指南

1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

**注意**: 请勿提交 `.env`、`credentials.json` 等包含敏感信息的文件。
