"""
启动脚本：同时提供 API + 前端静态文件服务
"""
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from web_demo.backend.api import router

app = FastAPI(title="食安数据库 Demo")
app.include_router(router)
app.mount("/", StaticFiles(directory="web_demo/frontend", html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
