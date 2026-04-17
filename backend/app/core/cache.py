import redis
import json
import time
import logging
from typing import Optional, Any
from .config import settings
from .context import UserContext

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            # 测试连接
            self.redis_client.ping()
            self.available = True
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, will use database directly")
            self.available = False
    
    def _get_tenant_prefix(self) -> str:
        """获取租户前缀"""
        if UserContext.is_system_mode():
            return "tenant:system"
        tenant_id = UserContext.get_tenant_id()
        if not tenant_id:
            raise RuntimeError("No Tenant ID in context!")
        return f"tenant:{tenant_id}"
    
    def _get_cache_key(self, key: str) -> str:
        """生成缓存Key"""
        tenant_prefix = self._get_tenant_prefix()
        return f"{tenant_prefix}:{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.available:
            return None
        
        try:
            cache_key = self._get_cache_key(key)
            value = self.redis_client.get(cache_key)
            if value:
                logger.info(f"Cache hit for key: {cache_key}")
                return json.loads(value)
            logger.info(f"Cache miss for key: {cache_key}")
            return None
        except Exception as e:
            logger.warning(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """设置缓存"""
        if not self.available:
            return False
        
        try:
            cache_key = self._get_cache_key(key)
            self.redis_client.setex(cache_key, expire, json.dumps(value))
            logger.info(f"Cache set for key: {cache_key}, expire: {expire}s")
            return True
        except Exception as e:
            logger.warning(f"Redis set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.available:
            return False
        
        try:
            cache_key = self._get_cache_key(key)
            self.redis_client.delete(cache_key)
            logger.info(f"Cache deleted for key: {cache_key}")
            return True
        except Exception as e:
            logger.warning(f"Redis delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> bool:
        """删除匹配模式的缓存"""
        if not self.available:
            return False
        
        try:
            tenant_prefix = self._get_tenant_prefix()
            full_pattern = f"{tenant_prefix}:{pattern}"
            keys = self.redis_client.keys(full_pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cache deleted for pattern: {full_pattern}, keys: {len(keys)}")
            return True
        except Exception as e:
            logger.warning(f"Redis delete pattern error: {e}")
            return False

# 创建全局缓存实例
cache = RedisCache()
