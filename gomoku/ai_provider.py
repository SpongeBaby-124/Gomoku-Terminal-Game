"""
AI服务提供商抽象层

定义AI服务的统一接口，支持多种AI提供商实现
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum


class MoveResult(Enum):
    """落子结果枚举"""
    SUCCESS = "success"
    INVALID_POSITION = "invalid_position"
    PARSE_ERROR = "parse_error"
    API_ERROR = "api_error"
    TIMEOUT = "timeout"


@dataclass
class AIMove:
    """AI落子响应数据类"""
    row: int
    col: int
    result: MoveResult
    reasoning: Optional[str] = None  # AI的思考过程
    error_message: Optional[str] = None


@dataclass
class ChatMessage:
    """聊天消息数据类"""
    role: str  # "user" 或 "assistant"
    content: str


@dataclass
class ChatResponse:
    """聊天响应数据类"""
    content: str
    success: bool
    error_message: Optional[str] = None


class AIProvider(ABC):
    """
    AI服务提供商抽象基类
    
    所有AI提供商实现必须继承此类并实现抽象方法
    """
    
    @abstractmethod
    def get_move(
        self,
        board: List[List[int]],
        current_player: int,
        history: List[Tuple[int, int, int]],
        board_size: int = 15
    ) -> AIMove:
        """
        获取AI的下一步落子位置
        
        Args:
            board: 棋盘状态，二维数组，0=空，1=黑棋，2=白棋
            current_player: 当前玩家（1=黑棋，2=白棋）
            history: 落子历史 [(row, col, player), ...]
            board_size: 棋盘大小，默认15
            
        Returns:
            AIMove: 包含落子位置和结果的响应对象
        """
        pass
    
    @abstractmethod
    def chat(
        self,
        message: str,
        chat_history: List[ChatMessage],
        board: Optional[List[List[int]]] = None,
        current_player: Optional[int] = None
    ) -> ChatResponse:
        """
        与AI进行对话
        
        Args:
            message: 用户消息
            chat_history: 聊天历史
            board: 当前棋盘状态（可选，用于上下文）
            current_player: 当前玩家（可选）
            
        Returns:
            ChatResponse: AI的回复
        """
        pass
    
    @abstractmethod
    def validate_connection(self) -> Tuple[bool, str]:
        """
        验证与AI服务的连接
        
        Returns:
            (是否连接成功, 消息)
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """获取提供商名称"""
        pass


class PromptBuilder:
    """
    提示词构建器
    
    负责构建发送给AI的提示词，包含游戏规则、棋盘状态等信息
    """
    
    # 列标签（A-T，支持20x20棋盘）
    COL_LABELS = "ABCDEFGHIJKLMNOPQRST"
    
    @classmethod
    def build_move_prompt(
        cls,
        board: List[List[int]],
        current_player: int,
        history: List[Tuple[int, int, int]],
        board_size: int = 20,
        suggested_move: Optional[Tuple[int, int]] = None,
        user_instruction: Optional[str] = None
    ) -> str:
        """
        构建落子请求的提示词
        
        Args:
            board: 棋盘状态
            current_player: 当前玩家
            history: 落子历史
            board_size: 棋盘大小
            suggested_move: 传统AI建议的落子位置 (row, col)
            user_instruction: 用户的落子指令（如果有）
            
        Returns:
            完整的提示词字符串
        """
        player_symbol = "●(黑棋)" if current_player == 1 else "○(白棋)"
        
        # 构建建议位置文本
        suggestion_text = ""
        if suggested_move:
            row, col = suggested_move
            pos_str = cls.coords_to_position(row, col)
            suggestion_text = f"""
## 算法建议
传统五子棋算法分析认为最优落子位置是：{pos_str}
这个建议基于棋盘评估和搜索算法，仅供参考。你可以采纳，也可以根据自己的判断选择其他位置。
"""
        
        # 用户指令优先
        user_instruction_text = ""
        if user_instruction:
            user_instruction_text = f"""
## 用户指令（最高优先级）
用户要求你下在：{user_instruction}
请优先遵循用户的指令。
"""
        
        prompt = f"""你是一个正在和用户下五子棋的AI，你执{player_symbol}。

## 游戏规则
1. 棋盘大小为 {board_size}x{board_size}
2. 先连成五子（横、竖、斜）的一方获胜
3. 黑棋先手（用户），你是白棋

## 当前棋盘状态
坐标系统：列用字母A-T表示，行用数字1-20表示
例如：A1表示左上角，J10表示中心位置

{cls.board_to_text(board, board_size)}

## 落子历史（最近10步）
{cls.history_to_text(history[-10:] if len(history) > 10 else history)}
{user_instruction_text}{suggestion_text}
## 你的任务
1. 如果用户有指令，优先遵循用户指令
2. 否则可以参考算法建议，或根据自己判断选择落子位置
3. 简要分析你的落子策略

**重要：你的回复必须包含以下格式的落子位置：**
MOVE: <列字母><行数字>

例如：MOVE: J10 或 MOVE: H8

请给出你的落子："""
        
        return prompt
    
    @classmethod
    def coords_to_position(cls, row: int, col: int) -> str:
        """将坐标转换为位置字符串，如 (7, 7) -> 'H8'"""
        if 0 <= col < len(cls.COL_LABELS):
            return f"{cls.COL_LABELS[col]}{row + 1}"
        return f"({row}, {col})"
    
    @classmethod
    def build_chat_prompt(
        cls,
        board: Optional[List[List[int]]] = None,
        current_player: Optional[int] = None,
        history: Optional[List[Tuple[int, int, int]]] = None,
        board_size: int = 20
    ) -> str:
        """
        构建聊天系统提示词
        
        Args:
            board: 当前棋盘状态
            current_player: 当前玩家
            history: 落子历史
            board_size: 棋盘大小
            
        Returns:
            系统提示词字符串
        """
        base_prompt = """你是一个正在和用户下五子棋的AI对手，你执白棋(○)，用户执黑棋(●)。

你可以：
1. 讨论你的落子策略和思考过程
2. 分析当前局势和对手的走法
3. 回答用户关于五子棋的任何问题
4. 进行友好的对战交流

注意：
- 你是白棋选手，记住你下过的每一步棋
- 如果用户询问你为什么这样下，要解释你的策略
- 回复请控制在100字以内，保持简洁"""
        
        if board is not None:
            player_str = "黑棋(用户)" if current_player == 1 else "白棋(你)" if current_player == 2 else "未知"
            board_context = f"""

## 当前棋盘状态（{player_str}回合）
{cls.board_to_text(board, board_size)}"""
            
            if history:
                board_context += f"""

## 落子历史（最近10步）
{cls.history_to_text(history[-10:] if len(history) > 10 else history)}"""
            
            return base_prompt + board_context
        
        return base_prompt
    
    @classmethod
    def board_to_text(cls, board: List[List[int]], board_size: int = 20) -> str:
        """
        将棋盘转换为文本表示
        
        Args:
            board: 棋盘状态
            board_size: 棋盘大小
            
        Returns:
            棋盘的文本表示
        """
        lines = []
        
        # 列标签
        col_header = "   " + " ".join(cls.COL_LABELS[:board_size])
        lines.append(col_header)
        
        # 棋盘内容
        for row in range(board_size):
            row_num = str(row + 1).rjust(2)
            cells = []
            for col in range(board_size):
                cell = board[row][col]
                if cell == 0:
                    cells.append("·")
                elif cell == 1:
                    cells.append("●")
                else:
                    cells.append("○")
            lines.append(f"{row_num} " + " ".join(cells))
        
        return "\n".join(lines)
    
    @classmethod
    def history_to_text(cls, history: List[Tuple[int, int, int]]) -> str:
        """
        将落子历史转换为文本
        
        Args:
            history: 落子历史 [(row, col, player), ...]
            
        Returns:
            历史的文本表示
        """
        if not history:
            return "（暂无落子历史）"
        
        lines = []
        for i, (row, col, player) in enumerate(history, 1):
            player_symbol = "●" if player == 1 else "○"
            position = f"{cls.COL_LABELS[col]}{row + 1}"
            lines.append(f"{i}. {player_symbol} {position}")
        
        return "\n".join(lines)
    
    @classmethod
    def position_to_coords(cls, position: str, board_size: int = 20) -> Optional[Tuple[int, int]]:
        """
        将位置字符串转换为坐标
        
        支持的格式：
        - "A1", "H8", "M13", "Y25" （标准格式）
        - "a1", "h8" （小写）
        
        Args:
            position: 位置字符串
            board_size: 棋盘大小，默认25
            
        Returns:
            (row, col) 元组，解析失败返回 None
        """
        position = position.strip().upper()
        
        if len(position) < 2 or len(position) > 3:
            return None
        
        col_char = position[0]
        row_str = position[1:]
        
        # 解析列
        if col_char not in cls.COL_LABELS:
            return None
        col = cls.COL_LABELS.index(col_char)
        if col >= board_size:
            return None
        
        # 解析行
        try:
            row = int(row_str) - 1  # 转换为0索引
            if row < 0 or row >= board_size:
                return None
        except ValueError:
            return None
        
        return (row, col)


class ResponseParser:
    """
    AI响应解析器
    
    负责解析AI返回的落子位置
    """
    
    @classmethod
    def parse_move_response(cls, response: str, board_size: int = 20) -> Optional[Tuple[int, int, str]]:
        """
        解析AI的落子响应
        
        Args:
            response: AI的原始响应
            board_size: 棋盘大小
            
        Returns:
            (row, col, reasoning) 元组，解析失败返回 None
        """
        lines = response.strip().split('\n')
        reasoning = ""
        position = None
        
        for line in lines:
            line = line.strip()
            
            # 查找 MOVE: 格式
            if line.upper().startswith("MOVE:"):
                pos_str = line[5:].strip()
                coords = PromptBuilder.position_to_coords(pos_str, board_size)
                if coords:
                    position = coords
            else:
                # 收集分析内容作为推理
                if line and not line.upper().startswith("MOVE"):
                    if reasoning:
                        reasoning += " "
                    reasoning += line
        
        if position:
            row, col = position
            if 0 <= row < board_size and 0 <= col < board_size:
                return (row, col, reasoning)
        
        # 尝试其他格式解析
        return cls._try_alternative_formats(response, board_size)
    
    @classmethod
    def _try_alternative_formats(cls, response: str, board_size: int) -> Optional[Tuple[int, int, str]]:
        """
        尝试解析其他格式的位置
        
        支持的格式：
        - 直接的坐标如 "H8", "M13"
        - "(row, col)" 格式
        - "row:X, col:Y" 格式
        """
        import re
        
        # 尝试匹配标准坐标格式（如 H8, M13, A1）- 支持A-Y
        pattern = r'\b([A-Ya-y])(\d{1,2})\b'
        matches = re.findall(pattern, response)
        
        for col_char, row_str in matches:
            coords = PromptBuilder.position_to_coords(col_char + row_str, board_size)
            if coords:
                row, col = coords
                if 0 <= row < board_size and 0 <= col < board_size:
                    return (row, col, "")
        
        # 尝试匹配 (row, col) 格式
        pattern = r'\((\d{1,2})\s*,\s*(\d{1,2})\)'
        matches = re.findall(pattern, response)
        
        for row_str, col_str in matches:
            try:
                row, col = int(row_str), int(col_str)
                if 0 <= row < board_size and 0 <= col < board_size:
                    return (row, col, "")
            except ValueError:
                continue
        
        return None
