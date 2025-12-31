"""
游戏主逻辑 - 游戏流程控制（支持AI对战和聊天）
"""

import curses
import time
import threading
from typing import Optional

from .board import Board
from .ai import GomokuAI
from .ui import GomokuUI, InputMode
from .chat_manager import ChatManager
from .logger import get_logger
from .config import AIProviderType, load_ai_config, ConfigError
from .ai_service import get_ai_provider
from .ai_provider import AIProvider, MoveResult


class GomokuGame:
    """五子棋游戏主类（支持AI对战和聊天）"""
    
    def __init__(
        self, 
        difficulty="medium",
        cli_api_key: Optional[str] = None,
        cli_endpoint: Optional[str] = None,
        cli_model: Optional[str] = None
    ):
        """
        初始化游戏
        
        Args:
            difficulty: AI难度 easy/medium/hard（仅传统AI使用）
            cli_api_key: 命令行指定的API密钥
            cli_endpoint: 命令行指定的端点
            cli_model: 命令行指定的模型
        """
        self.board = Board()
        self.traditional_ai = GomokuAI(difficulty)
        self.ui = GomokuUI()
        self.difficulty = difficulty
        self.current_player = Board.BLACK
        self.game_over = False
        self.winner = None
        self.turn = 0
        
        # 命令行参数
        self.cli_api_key = cli_api_key
        self.cli_endpoint = cli_endpoint
        self.cli_model = cli_model
        
        # AI服务
        self.ai_provider: Optional[AIProvider] = None
        self.ai_config = None
        self.use_ai_service = False
        
        # 聊天管理
        self.chat_manager = ChatManager()
        self.chat_thread: Optional[threading.Thread] = None
        self.chat_response_pending = False
        
        # 日志
        self.logger = get_logger()
        
        # 初始化AI服务
        self._init_ai_service()
    
    def _init_ai_service(self):
        """初始化AI服务"""
        try:
            self.ai_provider, self.ai_config = get_ai_provider(
                cli_api_key=self.cli_api_key,
                cli_endpoint=self.cli_endpoint,
                cli_model=self.cli_model
            )
            
            # 如果 difficulty='ai'，强制使用AI服务
            if self.difficulty == 'ai':
                if self.ai_config.provider != AIProviderType.TRADITIONAL and self.ai_provider:
                    self.use_ai_service = True
                    self.logger.info(f"AI对战模式: 使用 {self.ai_config.provider.value} - {self.ai_config.model}")
                else:
                    # AI服务未配置，提示用户
                    self.logger.warning("AI服务未配置，将降级到传统AI")
                    self.use_ai_service = False
            else:
                # 传统AI模式：即使配置了AI服务也不用于下棋（但可用于聊天）
                self.use_ai_service = False
                self.logger.info(f"传统AI模式: {self.difficulty}")
                
        except Exception as e:
            self.logger.error(f"初始化AI服务失败: {e}")
            self.use_ai_service = False

    
    def run(self):
        """运行游戏主循环"""
        try:
            self.ui.init()
            self._game_loop()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.logger.exception(f"游戏异常: {e}")
        finally:
            self.ui.cleanup()
    
    def _game_loop(self):
        """游戏主循环"""
        show_help = False
        need_redraw = True  # 标记是否需要重绘
        
        # 使用阻塞式输入，避免反复刷新
        self.ui.stdscr.timeout(-1)
        
        while True:
            # 只在需要时绘制界面
            if need_redraw:
                if show_help:
                    self.ui.draw_help()
                    show_help = False
                    need_redraw = True
                    continue
                
                self._draw_game_state()
                need_redraw = False
            
            # 游戏结束处理
            if self.game_over:
                self.ui.draw_game_over(self.winner, self.board)
                
                key = self.ui.get_input()
                if key in [ord('q'), ord('Q')]:
                    break
                elif key in [ord('r'), ord('R')]:
                    self._reset_game()
                    need_redraw = True
                    continue
                elif key in [ord('c'), ord('C')]:
                    # 游戏结束后仍可聊天
                    self._handle_chat_mode()
                    need_redraw = True
                continue
            
            # 玩家回合
            if self.current_player == Board.BLACK:
                action = self._handle_player_input()
                
                if action == 'quit':
                    break
                elif action == 'restart':
                    self._reset_game()
                    need_redraw = True
                elif action == 'help':
                    show_help = True
                    need_redraw = True
                elif action == 'chat':
                    self._handle_chat_mode()
                    need_redraw = True
                elif action == 'move':
                    need_redraw = True
                    if self.board.last_move:
                        row, col, _ = self.board.last_move
                        if self.board.check_win(row, col):
                            self.game_over = True
                            self.winner = 'black'
                            continue
                    
                    self.current_player = Board.WHITE
                    self.turn += 1
                elif action == 'cursor_move':
                    # 光标移动需要重绘
                    need_redraw = True
            
            # AI回合
            else:
                self._handle_ai_turn()
                need_redraw = True
            
            # 检查平局
            if self.board.is_full() and not self.game_over:
                self.game_over = True
                self.winner = 'draw'
                need_redraw = True
    
    def _handle_player_input(self):
        """处理玩家输入"""
        key = self.ui.get_input()
        
        if key == -1:  # 超时，无输入
            return None
        
        # 退出
        if key in [ord('q'), ord('Q')]:
            return 'quit'
        
        # 重新开始
        elif key in [ord('r'), ord('R')]:
            return 'restart'
        
        # 帮助
        elif key in [ord('h'), ord('H')]:
            return 'help'
        
        # 聊天（始终可用，使用独立的终端输入界面）
        elif key in [ord('c'), ord('C'), ord('/')]:
            return 'chat'
        
        # 方向键移动
        elif key == curses.KEY_UP or key in [ord('w'), ord('W')]:
            self.ui.move_cursor('up', self.board.SIZE)
            return 'cursor_move'
        
        elif key == curses.KEY_DOWN or key in [ord('s'), ord('S')]:
            self.ui.move_cursor('down', self.board.SIZE)
            return 'cursor_move'
        
        elif key == curses.KEY_LEFT or key in [ord('a'), ord('A')]:
            self.ui.move_cursor('left', self.board.SIZE)
            return 'cursor_move'
        
        elif key == curses.KEY_RIGHT or key in [ord('d'), ord('D')]:
            self.ui.move_cursor('right', self.board.SIZE)
            return 'cursor_move'
        
        # 落子
        elif key in [curses.KEY_ENTER, ord('\n'), ord('\r'), ord(' ')]:
            row, col = self.ui.get_cursor_position()
            
            if self.board.place_stone(row, col, Board.BLACK):
                return 'move'
            else:
                return 'invalid'
        
        return None
    
    def _handle_ai_turn(self):
        """处理AI回合"""
        self.ui.show_ai_thinking("AI thinking...")
        time.sleep(0.3)
        
        ai_move = None
        
        if self.use_ai_service and self.ai_provider:
            # 使用AI服务
            ai_move = self._get_ai_service_move()
        
        if ai_move is None:
            # 降级到传统AI
            ai_move = self.traditional_ai.get_move(self.board, Board.WHITE)
            if ai_move:
                self.logger.info(f"传统AI落子: {ai_move}")
        
        if ai_move:
            row, col = ai_move
            self.board.place_stone(row, col, Board.WHITE)
            
            if self.board.check_win(row, col):
                self.game_over = True
                self.winner = 'white'
                return
            
            self.current_player = Board.BLACK
        else:
            # AI无法落子
            self.game_over = True
            self.winner = 'draw'
    
    def _get_ai_service_move(self):
        """从AI服务获取落子"""
        if not self.ai_provider:
            return None
        
        try:
            # 构建历史记录
            history = []
            for move in self.board.history:
                history.append((move[0], move[1], move[2]))
            
            # 先用传统AI（中等难度）计算建议位置
            from .ai import GomokuAI
            traditional_ai = GomokuAI("medium")
            suggested_move = traditional_ai.get_move(self.board, Board.WHITE)
            
            if suggested_move:
                self.logger.info(f"传统AI建议位置: {suggested_move}")
            
            # 获取用户指令（如果有的话，从聊天历史中检查最近的指令）
            user_instruction = self._get_user_move_instruction()
            
            # 调用AI服务，传入建议位置
            result = self.ai_provider.get_move(
                board=self.board.grid,
                current_player=Board.WHITE,
                history=history,
                board_size=self.board.SIZE,
                suggested_move=suggested_move,
                user_instruction=user_instruction
            )
            
            if result.result == MoveResult.SUCCESS:
                self.logger.info(f"AI服务落子: ({result.row}, {result.col}), 理由: {result.reasoning}")
                return (result.row, result.col)
            else:
                self.logger.warning(f"AI服务落子失败: {result.result.value}, {result.error_message}")
                return None
                
        except Exception as e:
            self.logger.exception(f"AI服务调用异常: {e}")
            return None
    
    def _get_user_move_instruction(self) -> Optional[str]:
        """
        从最近的聊天历史中提取用户的落子指令
        
        例如用户说："下在H8" 或 "走J10"
        """
        recent_messages = self.chat_manager.get_recent_messages(3)
        for msg in reversed(recent_messages):
            if msg.role == "user":
                content = msg.content.lower()
                # 检查是否包含落子指令关键词
                keywords = ["下在", "走", "下", "落", "放", "move", "play"]
                for kw in keywords:
                    if kw in content:
                        return msg.content
        return None
    
    def _handle_chat_mode(self):
        """
        进入聊天模式处理
        
        保持棋盘显示，使用get_wch()支持中文输入
        """
        import curses
        
        self.ui.set_input_mode(InputMode.CHAT)
        chat_input = ""
        
        while True:
            # 绘制当前状态
            self._draw_game_state()
            
            # 在棋盘下方显示输入提示
            from .board import Board
            input_y = Board.SIZE + 10
            
            # 清除整行（使用更长的空格）
            terminal_width = self.ui.cols if hasattr(self.ui, 'cols') else 120
            self.ui.safe_addstr(input_y, 0, " " * (terminal_width - 1), curses.color_pair(self.ui.COLOR_BOARD))
            
            prompt = f"聊天> {chat_input}_"
            # 截断以适应屏幕宽度
            max_len = terminal_width - 1
            display_prompt, _ = self.ui._truncate_text(prompt, max_len)
            
            self.ui.safe_addstr(input_y, 0, display_prompt, curses.color_pair(self.ui.COLOR_INPUT) | curses.A_BOLD)
            self.ui.safe_addstr(input_y + 1, 0, "ESC退出 | Enter发送", curses.color_pair(self.ui.COLOR_BOARD))
            self.ui.refresh()
            
            # 获取输入（支持中文）
            try:
                # 尝试使用 get_wch() 支持宽字符（中文）
                try:
                    ch = self.ui.stdscr.get_wch()
                except AttributeError:
                    # 如果不支持 get_wch，降级为 getch
                    ch = self.ui.stdscr.getch()
                    if isinstance(ch, int) and ch != -1:
                        ch = chr(ch) if 32 <= ch <= 126 else ch
                
                # ESC 退出
                if ch == '\x1b' or ch == 27:
                    break
                
                # Enter 发送消息
                elif ch in ['\n', '\r', curses.KEY_ENTER]:
                    if chat_input.strip():
                        # 清空输入行后再发送
                        self.ui.safe_addstr(input_y, 0, " " * (terminal_width - 1), curses.color_pair(self.ui.COLOR_BOARD))
                        self._send_chat_in_ui(chat_input.strip())
                    chat_input = ""
                
                # Backspace 删除
                elif ch in ['\x7f', '\b', curses.KEY_BACKSPACE, 8, 127]:
                    if chat_input:
                        chat_input = chat_input[:-1]
                
                # 普通字符（包括中文）
                elif isinstance(ch, str) and len(ch) == 1 and ord(ch) >= 32:
                    chat_input += ch
                    
            except curses.error:
                pass
            except Exception as e:
                self.logger.error(f"聊天输入错误: {e}")
                break
        
        self.ui.set_input_mode(InputMode.GAME)
    
    def _send_chat_in_ui(self, message: str):
        """在UI中发送聊天消息并显示回复"""
        import curses
        from .board import Board
        
        # 添加用户消息
        self.chat_manager.add_user_message(message)
        
        # 显示等待提示
        input_y = Board.SIZE + 10
        terminal_width = self.ui.cols if hasattr(self.ui, 'cols') else 120
        self.ui.safe_addstr(input_y, 0, " " * (terminal_width - 1), curses.color_pair(self.ui.COLOR_BOARD))
        self.ui.safe_addstr(input_y, 0, "AI思考中...", curses.color_pair(self.ui.COLOR_CHAT_AI))
        self.ui.refresh()
        
        # 发送到AI
        if self.ai_provider:  # 只要有AI provider就可以聊天
            try:
                response = self.ai_provider.chat(
                    message=message,
                    chat_history=self.chat_manager.get_history()[:-1],
                    board=self.board.board,
                    current_player=self.current_player,
                    board_history=self.board.history  # 传递落子历史
                )
                
                if response.success:
                    ai_reply = response.content
                    self.logger.info(f"聊天回复: {ai_reply[:50]}...")
                else:
                    ai_reply = f"错误: {response.error_message}"
                    self.logger.error(f"聊天失败: {response.error_message}")
                    
            except Exception as e:
                ai_reply = "抱歉，无法连接到AI服务"
                self.logger.exception(f"聊天异常: {e}")
        else:
            ai_reply = "AI服务未配置。请运行 'gomoku --config' 进行配置。"
        
        self.chat_manager.add_assistant_message(ai_reply)
        
        # 更新聊天显示
        self._update_chat_display()
    
    def _handle_chat_input(self) -> bool:
        """
        处理聊天输入
        
        Returns:
            是否需要刷新界面
        """
        key = self.ui.get_input()
        
        if key == -1:  # 超时（阻塞模式下不会发生）
            return False
        
        # ESC退出聊天模式
        if key == 27:
            self.ui.set_input_mode(InputMode.GAME)
            self.ui.clear_chat_input()
            return True
        
        # Enter发送消息
        elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
            message = self.ui.get_chat_input()
            if message.strip():
                self._send_chat_message(message.strip())
            return True
        
        # Backspace删除
        elif key in [curses.KEY_BACKSPACE, 127, 8]:
            self.ui.backspace_chat_input()
            return True
        
        # 普通字符输入
        elif 32 <= key <= 126:
            self.ui.append_chat_input(chr(key))
            return True
        
        return False
    
    def _send_chat_message(self, message: str):
        """发送聊天消息"""
        # 添加用户消息
        self.chat_manager.add_user_message(message)
        self._update_chat_display()
        
        # 显示AI正在输入
        self.ui.set_ai_typing(True)
        self._draw_game_state()
        
        # 发送到AI
        if self.use_ai_service and self.ai_provider:
            try:
                response = self.ai_provider.chat(
                    message=message,
                    chat_history=self.chat_manager.get_history()[:-1],  # 不包含刚添加的消息
                    board=self.board.board,
                    current_player=self.current_player
                )
                
                if response.success:
                    self.chat_manager.add_assistant_message(response.content)
                    self.logger.info(f"聊天回复: {response.content[:50]}...")
                else:
                    self.chat_manager.add_assistant_message(f"抱歉，出现错误: {response.error_message}")
                    self.logger.error(f"聊天失败: {response.error_message}")
                    
            except Exception as e:
                self.chat_manager.add_assistant_message("抱歉，无法连接到AI服务")
                self.logger.exception(f"聊天异常: {e}")
        else:
            # 无AI服务，使用默认回复
            self.chat_manager.add_assistant_message("AI服务未配置。请设置环境变量 AI_PROVIDER 和 AI_API_KEY")
        
        self.ui.set_ai_typing(False)
        self._update_chat_display()
    
    def _update_chat_display(self):
        """更新聊天显示"""
        formatted = self.chat_manager.format_for_display(self.ui.chat_width - 8)
        self.ui.update_chat_messages(formatted)
    
    def _draw_game_state(self):
        """绘制当前游戏状态"""
        last_move = self.board.last_move[:2] if self.board.last_move else None
        self.ui.draw_board(self.board, last_move)
        
        # 构建游戏状态
        game_state = {
            'difficulty': self.difficulty,
            'turn': self.turn,
            'current_player': 'black' if self.current_player == Board.BLACK else 'white',
            'message': ''
        }
        
        # 添加AI提供商信息
        if self.use_ai_service and self.ai_config:
            game_state['ai_provider'] = f"{self.ai_config.provider.value}"
        
        self.ui.draw_status(game_state)
        self.ui.draw_controls()
        self.ui.refresh()
    
    def _reset_game(self):
        """重置游戏"""
        self.board.reset()
        self.ui.reset_cursor()
        self.ui.set_input_mode(InputMode.GAME)
        self.current_player = Board.BLACK
        self.game_over = False
        self.winner = None
        self.turn = 0
        
        # 清空聊天历史
        self.chat_manager.clear_history()
        self.ui.clear_chat()
        
        self.logger.info("游戏重置")
