"""
OpenAI AI提供商实现

使用OpenAI API进行五子棋对战和聊天
"""

from typing import List, Tuple, Optional
import time

from gomoku.ai_provider import (
    AIProvider, AIMove, MoveResult,
    ChatMessage, ChatResponse,
    PromptBuilder, ResponseParser
)
from gomoku.config import AIConfig


class OpenAIProvider(AIProvider):
    """
    OpenAI AI提供商
    
    支持 GPT-4, GPT-4o, GPT-3.5-turbo 等模型
    """
    
    def __init__(self, config: AIConfig):
        """
        初始化OpenAI提供商
        
        Args:
            config: AI配置对象
        """
        self.config = config
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """初始化OpenAI客户端"""
        try:
            from openai import OpenAI
            
            kwargs = {"api_key": self.config.api_key}
            if self.config.endpoint:
                kwargs["base_url"] = self.config.endpoint
            
            self._client = OpenAI(**kwargs)
        except ImportError:
            raise ImportError(
                "OpenAI库未安装，请运行: pip install openai"
            )
    
    @property
    def provider_name(self) -> str:
        return "OpenAI"
    
    def validate_connection(self) -> Tuple[bool, str]:
        """验证与OpenAI的连接"""
        try:
            # 使用简单的请求测试连接
            response = self._client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
                timeout=10
            )
            return True, f"成功连接到 OpenAI ({self.config.model})"
        except Exception as e:
            return False, f"连接OpenAI失败: {str(e)}"
    
    def get_move(
        self,
        board: List[List[int]],
        current_player: int,
        history: List[Tuple[int, int, int]],
        board_size: int = 20,
        suggested_move: Optional[Tuple[int, int]] = None,
        user_instruction: Optional[str] = None
    ) -> AIMove:
        """获取AI的下一步落子"""
        prompt = PromptBuilder.build_move_prompt(
            board=board,
            current_player=current_player,
            history=history,
            board_size=board_size,
            suggested_move=suggested_move,
            user_instruction=user_instruction
        )
        
        for attempt in range(self.config.max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的五子棋AI。请分析棋局并给出最佳落子位置。"
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.3,
                    timeout=self.config.timeout
                )
                
                content = response.choices[0].message.content
                result = ResponseParser.parse_move_response(content, board_size)
                
                if result:
                    row, col, reasoning = result
                    # 验证位置是否为空
                    if board[row][col] == 0:
                        return AIMove(
                            row=row,
                            col=col,
                            result=MoveResult.SUCCESS,
                            reasoning=reasoning
                        )
                    else:
                        # 位置已被占用，继续重试
                        continue
                else:
                    # 解析失败，继续重试
                    continue
                    
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    return AIMove(
                        row=-1,
                        col=-1,
                        result=MoveResult.API_ERROR,
                        error_message=str(e)
                    )
                time.sleep(1)  # 重试前等待
        
        return AIMove(
            row=-1,
            col=-1,
            result=MoveResult.PARSE_ERROR,
            error_message="无法解析AI的落子位置"
        )
    
    def chat(
        self,
        message: str,
        chat_history: List[ChatMessage],
        board: Optional[List[List[int]]] = None,
        current_player: Optional[int] = None,
        board_history: Optional[List[Tuple[int, int, int]]] = None
    ) -> ChatResponse:
        """与AI进行对话"""
        try:
            system_prompt = PromptBuilder.build_chat_prompt(
                board=board,
                current_player=current_player,
                history=board_history,
                board_size=20
            )
            
            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加聊天历史
            for msg in chat_history[-10:]:  # 最多保留最近10条
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # 添加当前消息
            messages.append({"role": "user", "content": message})
            
            response = self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=150,
                temperature=0.7,
                timeout=self.config.timeout
            )
            
            content = response.choices[0].message.content
            return ChatResponse(content=content, success=True)
            
        except Exception as e:
            return ChatResponse(
                content="",
                success=False,
                error_message=f"聊天请求失败: {str(e)}"
            )
