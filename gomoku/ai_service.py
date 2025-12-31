"""
AI服务工厂

负责根据配置创建对应的AI提供商实例
"""

from typing import Optional
from gomoku.config import AIConfig, AIProviderType, load_ai_config, ConfigError
from gomoku.ai_provider import AIProvider
from gomoku.logger import get_logger


class AIServiceFactory:
    """
    AI服务工厂
    
    根据配置创建对应的AI提供商实例
    """
    
    @staticmethod
    def create_provider(config: Optional[AIConfig] = None) -> Optional[AIProvider]:
        """
        创建AI提供商实例
        
        Args:
            config: AI配置，如果为None则从环境变量加载
            
        Returns:
            AIProvider实例，如果是传统AI则返回None
            
        Raises:
            ConfigError: 配置错误
            ImportError: 缺少必要的依赖库
        """
        logger = get_logger()
        
        if config is None:
            try:
                config = load_ai_config()
            except ConfigError as e:
                logger.error(f"加载AI配置失败: {e}")
                raise
        
        # 传统AI不需要创建provider
        if config.provider == AIProviderType.TRADITIONAL:
            logger.info("使用传统AI算法")
            return None
        
        # 创建对应的提供商
        try:
            if config.provider == AIProviderType.OPENAI:
                from gomoku.providers.openai_provider import OpenAIProvider
                provider = OpenAIProvider(config)
                logger.info(f"创建OpenAI提供商: {config.model}")
                return provider
                
            elif config.provider == AIProviderType.ANTHROPIC:
                from gomoku.providers.anthropic_provider import AnthropicProvider
                provider = AnthropicProvider(config)
                logger.info(f"创建Anthropic提供商: {config.model}")
                return provider
            
            else:
                raise ConfigError(f"未知的AI提供商: {config.provider}")
                
        except ImportError as e:
            logger.error(f"创建AI提供商失败，缺少依赖: {e}")
            raise
        except Exception as e:
            logger.error(f"创建AI提供商失败: {e}")
            raise


def get_ai_provider() -> tuple[Optional[AIProvider], AIConfig]:
    """
    获取AI提供商实例和配置
    
    便捷函数，用于游戏初始化
    
    Returns:
        (provider, config) 元组
    """
    try:
        config = load_ai_config()
        provider = AIServiceFactory.create_provider(config)
        return provider, config
    except Exception as e:
        get_logger().error(f"获取AI提供商失败: {e}")
        # 返回传统AI作为降级
        from gomoku.config import AIConfig, AIProviderType
        fallback_config = AIConfig(provider=AIProviderType.TRADITIONAL)
        return None, fallback_config
