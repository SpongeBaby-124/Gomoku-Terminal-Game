"""
聊天上下文管理器

管理聊天历史和上下文信息
"""

from typing import List, Optional
from dataclasses import dataclass, field
from gomoku.ai_provider import ChatMessage


@dataclass
class ChatManager:
    """
    聊天管理器
    
    负责管理聊天历史、上下文等信息
    """
    
    max_history: int = 10  # 最大历史消息数量
    history: List[ChatMessage] = field(default_factory=list)
    
    def add_user_message(self, content: str):
        """
        添加用户消息
        
        Args:
            content: 消息内容
        """
        self.history.append(ChatMessage(role="user", content=content))
        self._trim_history()
    
    def add_assistant_message(self, content: str):
        """
        添加助手消息
        
        Args:
            content: 消息内容
        """
        self.history.append(ChatMessage(role="assistant", content=content))
        self._trim_history()
    
    def get_history(self) -> List[ChatMessage]:
        """
        获取聊天历史
        
        Returns:
            聊天历史列表
        """
        return self.history.copy()
    
    def clear_history(self):
        """清空聊天历史"""
        self.history.clear()
    
    def _trim_history(self):
        """裁剪历史记录，保持在最大数量以内"""
        while len(self.history) > self.max_history:
            self.history.pop(0)
    
    def get_recent_messages(self, count: int = 5) -> List[ChatMessage]:
        """
        获取最近的消息
        
        Args:
            count: 消息数量
            
        Returns:
            最近的消息列表
        """
        return self.history[-count:] if len(self.history) >= count else self.history.copy()
    
    def format_for_display(self, max_width: int = 35) -> List[tuple]:
        """
        格式化消息用于显示
        
        Args:
            max_width: 最大显示宽度
            
        Returns:
            [(role, formatted_lines), ...] 列表
        """
        result = []
        for msg in self.history:
            # 将消息内容按宽度分割成多行
            lines = self._wrap_text(msg.content, max_width)
            result.append((msg.role, lines))
        return result
    
    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """
        按宽度分割文本
        
        Args:
            text: 原始文本
            max_width: 最大宽度
            
        Returns:
            分割后的行列表
        """
        lines = []
        for paragraph in text.split('\n'):
            if not paragraph:
                lines.append('')
                continue
            
            current_line = ''
            current_width = 0
            
            for char in paragraph:
                # 中文字符宽度为2，其他为1
                char_width = 2 if '\u4e00' <= char <= '\u9fff' else 1
                
                if current_width + char_width > max_width:
                    lines.append(current_line)
                    current_line = char
                    current_width = char_width
                else:
                    current_line += char
                    current_width += char_width
            
            if current_line:
                lines.append(current_line)
        
        return lines if lines else ['']
