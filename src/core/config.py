"""
全局配置管理模块 (config.py)

基于 pydantic-settings 开发，实现环境变量统一管理、多环境适配、敏感信息保护。
绝对禁止硬编码密钥、密码等敏感信息。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional


class GlobalSettings(BaseSettings):
    """全局配置基类，固定配置加载规则"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class ProjectSettings(GlobalSettings):
    """项目基础配置"""
    project_name: str = Field(default="food_safety_agent_cluster", description="项目名称")
    env: str = Field(default="dev", description="运行环境：dev/test/prod")
    debug: bool = Field(default=True, description="是否开启调试模式")
    service_port: int = Field(default=8000, description="服务端口")


class MySQLSettings(GlobalSettings):
    """MySQL数据库配置（与中间件环境搭建任务对齐）"""
    mysql_host: str = Field(default="localhost", description="MySQL地址")
    mysql_port: int = Field(default=3306, description="MySQL端口")
    mysql_database: str = Field(default="food_safety_agent", description="数据库名")
    mysql_admin_user: Optional[str] = Field(default=None, description="管理员账号")
    mysql_admin_password: Optional[str] = Field(default=None, description="管理员密码", repr=False)
    mysql_readonly_user: Optional[str] = Field(default=None, description="只读账号")
    mysql_readonly_password: Optional[str] = Field(default=None, description="只读账号密码", repr=False)


class RedisSettings(GlobalSettings):
    """Redis配置"""
    redis_host: str = Field(default="localhost", description="Redis地址")
    redis_port: int = Field(default=6379, description="Redis端口")
    redis_password: Optional[str] = Field(default=None, description="Redis密码", repr=False)
    redis_db: int = Field(default=0, description="Redis数据库编号")
    stream_topic: str = Field(default="agent_message_bus", description="Agent通信Stream主题")


class LLMSettings(GlobalSettings):
    """大模型配置"""
    llm_base_url: str = Field(default="", description="大模型API地址")
    llm_api_key: Optional[str] = Field(default=None, description="大模型API密钥", repr=False)
    llm_model_name: str = Field(default="", description="大模型名称")
    llm_timeout: int = Field(default=60, description="调用超时时间，单位秒")
    llm_max_retries: int = Field(default=3, description="最大重试次数")

    @field_validator("llm_base_url")
    @classmethod
    def _validate_url(cls, v: str) -> str:
        """校验 llm_base_url 格式：非空时必须为合法 HTTP/HTTPS URL"""
        if not v:
            return v
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("llm_base_url 必须以 http:// 或 https:// 开头")
        return v


class JWTSettings(GlobalSettings):
    """JWT 认证配置"""
    jwt_secret: Optional[str] = Field(default=None, description="JWT 签名密钥（HS256）", repr=False)
    jwt_algorithm: str = Field(default="HS256", description="JWT 签名算法")
    jwt_disable_verify: bool = Field(default=False, description="是否禁用 JWT 验签（仅开发/测试环境）")
    jwt_issuer: Optional[str] = Field(default=None, description="JWT 签发者")
    jwt_audience: Optional[str] = Field(default=None, description="JWT 受众")

    @field_validator("jwt_disable_verify")
    @classmethod
    def _validate_disable_verify(cls, v: bool) -> bool:
        if v and project_settings.env == "prod":
            raise ValueError("jwt_disable_verify 不允许在 prod 环境开启")
        return v


# 全局配置单例，全项目直接导入使用
project_settings = ProjectSettings()
mysql_settings = MySQLSettings()
redis_settings = RedisSettings()
llm_settings = LLMSettings()
jwt_settings = JWTSettings()

__all__ = [
    "project_settings",
    "mysql_settings",
    "redis_settings",
    "llm_settings",
    "jwt_settings",
    "ProjectSettings",
    "MySQLSettings",
    "RedisSettings",
    "LLMSettings",
    "JWTSettings",
]
