"""
AI配置管理模块

支持多种配置方式（按优先级）：
1. 命令行参数（最高优先级）
2. 环境变量
3. 配置文件 (~/.gomoku/config.json)
4. 默认值（传统AI）
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
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


# 配置文件路径
def get_config_dir() -> Path:
    """获取配置目录路径"""
    return Path.home() / ".gomoku"


def get_config_file() -> Path:
    """获取配置文件路径"""
    return get_config_dir() / "config.json"


def save_config_to_file(config: AIConfig) -> bool:
    """
    保存配置到文件
    
    Args:
        config: AI配置对象
        
    Returns:
        是否保存成功
    """
    try:
        config_dir = get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_data = {
            "provider": config.provider.value,
            "api_key": config.api_key,
            "model": config.model,
            "endpoint": config.endpoint,
            "timeout": config.timeout,
            "max_retries": config.max_retries
        }
        
        config_file = get_config_file()
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception:
        return False


def load_config_from_file() -> Optional[Dict[str, Any]]:
    """
    从配置文件加载配置
    
    Returns:
        配置字典，如果文件不存在或读取失败返回 None
    """
    config_file = get_config_file()
    if not config_file.exists():
        return None
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def delete_config_file() -> bool:
    """
    删除配置文件
    
    Returns:
        是否删除成功
    """
    config_file = get_config_file()
    if config_file.exists():
        try:
            config_file.unlink()
            return True
        except Exception:
            return False
    return True


def load_ai_config(
    cli_provider: Optional[str] = None,
    cli_api_key: Optional[str] = None,
    cli_model: Optional[str] = None,
    cli_endpoint: Optional[str] = None
) -> AIConfig:
    """
    加载AI配置（按优先级合并多个来源）
    
    优先级: 命令行参数 > 环境变量 > 配置文件 > 默认值
    
    Args:
        cli_provider: 命令行指定的提供商
        cli_api_key: 命令行指定的API密钥
        cli_model: 命令行指定的模型
        cli_endpoint: 命令行指定的端点
    
    Returns:
        AIConfig: AI配置对象
        
    Raises:
        ConfigError: 配置错误时抛出
    """
    # 1. 从配置文件加载（最低优先级）
    file_config = load_config_from_file() or {}
    
    # 2. 从环境变量获取（中等优先级）
    env_provider = os.environ.get("AI_PROVIDER", "").strip() or None
    env_api_key = os.environ.get("AI_API_KEY", "").strip() or None
    env_model = os.environ.get("AI_MODEL", "").strip() or None
    env_endpoint = os.environ.get("AI_ENDPOINT", "").strip() or None
    env_timeout = os.environ.get("AI_TIMEOUT", "").strip() or None
    env_max_retries = os.environ.get("AI_MAX_RETRIES", "").strip() or None
    
    # 3. 合并配置（按优先级）
    provider_str = (
        cli_provider or 
        env_provider or 
        file_config.get("provider") or 
        "traditional"
    ).lower().strip()
    
    api_key = (
        cli_api_key or 
        env_api_key or 
        file_config.get("api_key")
    )
    
    model = (
        cli_model or 
        env_model or 
        file_config.get("model")
    )
    
    endpoint = (
        cli_endpoint or 
        env_endpoint or 
        file_config.get("endpoint")
    )
    
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
    
    # 检查API密钥
    if not api_key:
        raise ConfigError(
            f"使用 {provider.value} 需要配置 API 密钥\n"
            f"请运行: gomoku --config  进行配置"
        )
    
    # 解析超时时间
    timeout_str = env_timeout or str(file_config.get("timeout", 30))
    try:
        timeout = int(timeout_str)
        if timeout <= 0:
            raise ValueError()
    except ValueError:
        timeout = 30
    
    # 解析最大重试次数
    retries_str = env_max_retries or str(file_config.get("max_retries", 3))
    try:
        max_retries = int(retries_str)
        if max_retries < 0:
            raise ValueError()
    except ValueError:
        max_retries = 3
    
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
        return False, "缺少API密钥"
    
    # 基本格式检查（OpenAI兼容API可能有不同前缀，放宽检查）
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


def interactive_config() -> Optional[AIConfig]:
    """
    交互式配置向导
    
    Returns:
        配置好的 AIConfig 对象，如果用户取消则返回 None
    """
    print("\n" + "=" * 50)
    print("  🎮 五子棋 AI 配置向导")
    print("=" * 50)
    
    # 显示当前配置
    current_config = load_config_from_file()
    if current_config:
        print("\n当前配置:")
        print(f"  提供商: {current_config.get('provider', '未设置')}")
        print(f"  模型: {current_config.get('model', '未设置')}")
        print(f"  端点: {current_config.get('endpoint', '默认')}")
        print(f"  API密钥: {'已设置' if current_config.get('api_key') else '未设置'}")
    
    print("\n选择 AI 提供商:")
    print("  1. OpenAI (GPT-4, GPT-4o 等)")
    print("  2. Anthropic (Claude 系列)")
    print("  3. OpenAI 兼容 API (DeepSeek, 智谱, 月之暗面等)")
    print("  4. 传统 AI (内置算法，无需配置)")
    print("  0. 取消")
    
    try:
        choice = input("\n请选择 (0-4): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n已取消")
        return None
    
    if choice == "0":
        print("已取消")
        return None
    
    if choice == "4":
        config = AIConfig(provider=AIProviderType.TRADITIONAL)
        if save_config_to_file(config):
            print("\n✅ 配置已保存！将使用传统 AI 算法。")
        return config
    
    if choice not in ["1", "2", "3"]:
        print("无效选择")
        return None
    
    # 设置提供商
    if choice == "1":
        provider = AIProviderType.OPENAI
        default_endpoint = None
        default_model = "gpt-4o"
    elif choice == "2":
        provider = AIProviderType.ANTHROPIC
        default_endpoint = None
        default_model = "claude-3-5-sonnet-20241022"
    else:  # choice == "3"
        provider = AIProviderType.OPENAI
        print("\n常用 OpenAI 兼容 API 端点:")
        print("  - DeepSeek: https://api.deepseek.com/v1")
        print("  - 智谱 GLM: https://open.bigmodel.cn/api/paas/v4")
        print("  - 月之暗面: https://api.moonshot.cn/v1")
        print("  - Ollama:   http://localhost:11434/v1")
        default_endpoint = "https://api.deepseek.com/v1"
        default_model = "deepseek-chat"
    
    try:
        # 获取 API 密钥
        api_key = input(f"\n请输入 API 密钥: ").strip()
        if not api_key:
            print("API 密钥不能为空")
            return None
        
        # 获取端点（如果需要）
        if choice == "3":
            endpoint_input = input(f"请输入 API 端点 (默认: {default_endpoint}): ").strip()
            endpoint = endpoint_input or default_endpoint
        else:
            endpoint = default_endpoint
        
        # 获取模型
        model_input = input(f"请输入模型名称 (默认: {default_model}): ").strip()
        model = model_input or default_model
        
    except (KeyboardInterrupt, EOFError):
        print("\n已取消")
        return None
    
    # 创建配置
    config = AIConfig(
        provider=provider,
        api_key=api_key,
        model=model,
        endpoint=endpoint
    )
    
    # 保存配置
    if save_config_to_file(config):
        print(f"\n✅ 配置已保存到: {get_config_file()}")
        print("\n配置摘要:")
        print(f"  提供商: {provider.value}")
        print(f"  模型: {model}")
        if endpoint:
            print(f"  端点: {endpoint}")
        print("\n现在可以运行 'gomoku' 开始游戏了！")
    else:
        print("\n⚠️ 配置保存失败，但本次游戏仍可使用此配置")
    
    return config
