from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi_events.handlers.local import local_handler
from fastapi_events.middleware import EventHandlerASGIMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.context import UserContext, system_mode_scope
from app.core.middleware import AuthMiddleware
from app.core.exceptions import register_exception_handlers
from app.db import Base, SessionLocal, engine
from app.modules.user.service import ensure_dev_admin_user
from app.db.security_guard import register_security_guards
from app.modules.ledger.scheduler import start_scheduler, shutdown_scheduler
from app.modules.device.mqtt import start_mqtt_client, stop_mqtt_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    register_security_guards(None, engine.sync_engine)

    if settings.environment != "production":
        with system_mode_scope():
            async with SessionLocal() as db:
                await ensure_dev_admin_user(db)

    start_scheduler()
    start_mqtt_client()
    try:
        yield
    finally:
        stop_mqtt_client()


def create_app() -> FastAPI:
    bearer_scheme = HTTPBearer(auto_error=False)
    app_client_scheme = APIKeyHeader(name="X-App-Client", auto_error=False, description="应用端标识(如: reg_app, exec_app)")

    app = FastAPI(
        title=settings.app_name,
        description="智慧食安平台后端接口",
        debug=(settings.environment == "development"),
        lifespan=lifespan,
        dependencies=[Depends(bearer_scheme), Depends(app_client_scheme)]
    )

    app.add_middleware(EventHandlerASGIMiddleware, handlers=[local_handler])

    # 注册全局异常处理 (来自 wph 分支)
    register_exception_handlers(app)

    # 配置 CORS 策略
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 待办：生产环境收紧域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 添加认证中间件 (由 AuthMiddleware 统一管理上下文)
    app.add_middleware(AuthMiddleware)

    # 注册路由
    app.include_router(api_router)

    # 挂载营业执照静态文件（浏览器可直接访问，无需鉴权）
    _license_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "image_license")
    os.makedirs(_license_dir, exist_ok=True)
    app.mount("/image_license", StaticFiles(directory=_license_dir), name="image_license")

    @app.get("/")
    async def root():
        return {
            "message": "Welcome to Food Safety Platform API",
            "docs": "/docs",
        }

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=(settings.environment == "development"),
    )
