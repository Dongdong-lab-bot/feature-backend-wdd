from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)

class CORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        """CORS中间件"""
        # 处理预检请求
        if request.method == "OPTIONS":
            response = Response()
        else:
            # 调用下一个中间件或路由处理函数
            response = await call_next(request)
        
        # 设置CORS响应头
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Max-Age"] = "86400"
        
        logger.debug(f"CORS headers set for {request.method} {request.url.path}")
        
        return response
