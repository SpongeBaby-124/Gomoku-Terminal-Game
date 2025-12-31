"""
AI配置管理模块

从环境变量读取AI服务配置，支持多种AI提供商
"""

import os
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class AIProviderType(Enum):
    """AI提供商类型枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    TRADITIONAL = "traditional"  # 传统AI（内置算法）


@dataclass
class AIConfig:
    """AI配置数据类"""
    provider: AIProviderType
    api_key: Optional[str] = None
    model: Optional[str] = None
    endpoint: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    
    # 默认模型配置
    DEFAULT_OPENAI_MODEL = "gpt-4o"
    DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
    
    def __post_init__(self):
        """初始化后处理，设置默认值"""
        if self.model is None:
            if self.provider == AIProviderType.OPENAI:
                self.model = self.DEFAULT_OPENAI_MODEL
            elif self.provider == AIProviderType.ANTHROPIC:
                self.model = self.DEFAULT_ANTHROPIC_MODEL


class ConfigError(Exception):
    """配置错误异常"""
    pass


def load_ai_config() -> AIConfig:
    """
    从环境变量加载AI配置
    
    环境变量:
        AI_PROVIDER: AI提供商类型 (openai/anthropic/traditional)
        AI_API_KEY: API密钥
        AI_MODEL: 模型名称（可选）
        AI_ENDPOINT: 自定义API端点（可选）
        AI_TIMEOUT: 请求超时时间（可选，默认30秒）
        AI_MAX_RETRIES: 最大重试次数（可选，默认3次）
    
    Returns:
        AIConfig: AI配置对象
        
    Raises:
        ConfigError: 配置错误时抛出
    """
    provider_str = os.environ.get("AI_PROVIDER", "traditional").lower().strip()
    
    # 解析提供商类型
    try:
        provider = AIProviderType(provider_str)
    except ValueError:
        valid_providers = [p.value for p in AIProviderType]
        raise ConfigError(
            f"无效的AI提供商: '{provider_str}'\n"
            f"有效选项: {', '.join(valid_providers)}"
        )
    
    # 如果是传统AI，不需要其他配置
    if provider == AIProviderType.TRADITIONAL:
        return AIConfig(provider=provider)
    
    # 获取API密钥
    api_key = os.environ.get("AI_API_KEY", "").strip()
    if not api_key:
        raise ConfigError(
            f"使用 {provider.value} 需要设置 AI_API_KEY 环境变量\n"
            f"请设置: export AI_API_KEY='your-api-key'"
        )
    
    # 获取模型名称（可选）
    model = os.environ.get("AI_MODEL", "").strip() or None
    
    # 获取自定义端点（可选）
    endpoint = os.environ.get("AI_ENDPOINT", "").strip() or None
    
    # 获取超时时间
    timeout_str = os.environ.get("AI_TIMEOUT", "30").strip()
    try:
        timeout = int(timeout_str)
        if timeout <= 0:
            raise ValueError()
    except ValueError:
        raise ConfigError(
            f"无效的超时时间: '{timeout_str}'\n"
            f"请设置一个正整数（秒）"
        )
    
    # 获取最大重试次数
    retries_str = os.environ.get("AI_MAX_RETRIES", "3").strip()
    try:
        max_retries = int(retries_str)
        if max_retries < 0:
            raise ValueError()
    except ValueError:
        raise ConfigError(
            f"无效的重试次数: '{retries_str}'\n"
            f"请设置一个非负整数"
        )
    
    return AIConfig(
        provider=provider,
        api_key=api_key,
        model=model,
        endpoint=endpoint,
        timeout=timeout,
        max_retries=max_retries
    )


def validate_config(config: AIConfig) -> tuple[bool, str]:
    """
    验证配置是否有效
    
    Args:
        config: AI配置对象
        
    Returns:
        (是否有效, 错误消息或成功消息)
    """
    if config.provider == AIProviderType.TRADITIONAL:
        return True, "使用传统AI（内置算法）"
    
    if not config.api_key:
        return False, f"缺少API密钥，请设置 AI_API_KEY 环境变量"
    
    # 基本格式检查
    if config.provider == AIProviderType.OPENAI:
        if not config.api_key.startswith("sk-"):
            return False, "OpenAI API密钥格式可能不正确（应以 'sk-' 开头）"
    
    if config.provider == AIProviderType.ANTHROPIC:
        if not config.api_key.startswith("sk-ant-"):
            return False, "Anthropic API密钥格式可能不正确（应以 'sk-ant-' 开头）"
    
    return True, f"配置有效: {config.provider.value} - {config.model}"


def get_config_summary(config: AIConfig) -> str:
    """
    获取配置摘要信息（用于显示）
    
    Args:
        config: AI配置对象
        
    Returns:
        配置摘要字符串
    """
    if config.provider == AIProviderType.TRADITIONAL:
        return "AI模式: 传统算法"
    
    lines = [
        f"AI模式: {config.provider.value.upper()}",
        f"模型: {config.model}",
    ]
    
    if config.endpoint:
        lines.append(f"端点: {config.endpoint}")
    
    lines.append(f"超时: {config.timeout}秒")
    
    return "\n".join(lines)
