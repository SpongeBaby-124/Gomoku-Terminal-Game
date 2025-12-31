"""
UI界面 - 使用curses实现终端界面（支持聊天功能）
"""

try:
    import curses
except ImportError:
    import sys
    print("错误: 未安装curses库")
    print("Windows用户请运行: pip install windows-curses")
    sys.exit(1)

from typing import List, Optional, Tuple
from enum import Enum


class InputMode(Enum):
    """输入模式枚举"""
    GAME = "game"    # 游戏模式
    CHAT = "chat"    # 聊天模式


class GomokuUI:
    """五子棋终端界面（支持聊天功能）"""
    
    # 颜色对
    COLOR_BOARD = 1
    COLOR_BLACK = 2
    COLOR_WHITE = 3
    COLOR_CURSOR = 4
    COLOR_LAST_MOVE = 5
    COLOR_TITLE = 6
    COLOR_CHAT_USER = 7
    COLOR_CHAT_AI = 8
    COLOR_CHAT_BORDER = 9
    COLOR_INPUT = 10
    
    # 显示符号
    SYMBOL_EMPTY = '+'
    SYMBOL_BLACK = 'X'
    SYMBOL_WHITE = 'O'
    SYMBOL_CURSOR = '#'
    
    # 布局常量
    BOARD_START_X = 0
    BOARD_START_Y = 2
    CHAT_MIN_WIDTH = 35
    CHAT_MAX_WIDTH = 45
    
    def __init__(self):
        """初始化UI"""
        self.stdscr = None
        self.cursor_row = 7
        self.cursor_col = 7
        self.message = ""
        self.use_unicode = True
        
        # 聊天相关
        self.chat_enabled = False
        self.chat_start_x = 40
        self.chat_width = 38
        self.chat_messages: List[Tuple[str, List[str]]] = []  # [(role, lines), ...]
        self.chat_scroll = 0
        self.chat_input_buffer = ""
        self.input_mode = InputMode.GAME
        self.ai_typing = False
        
        # 窗口尺寸
        self.term_height = 0
        self.term_width = 0
    
    def init(self):
        """初始化curses"""
        self.stdscr = curses.initscr()
        curses.start_color()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        self.stdscr.keypad(True)
        self.stdscr.timeout(100)  # 非阻塞输入，100ms超时
        
        # 初始化颜色对
        curses.init_pair(self.COLOR_BOARD, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(self.COLOR_BLACK, curses.COLOR_BLACK, curses.COLOR_BLACK)
        curses.init_pair(self.COLOR_WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(self.COLOR_CURSOR, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(self.COLOR_LAST_MOVE, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(self.COLOR_TITLE, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(self.COLOR_CHAT_USER, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(self.COLOR_CHAT_AI, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(self.COLOR_CHAT_BORDER, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(self.COLOR_INPUT, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        
        # 检测窗口大小
        self._update_window_size()
        
        # 初始化Unicode支持
        self._init_unicode()
        
        self.stdscr.clear()
    
    def _init_unicode(self):
        """初始化Unicode支持"""
        try:
            import locale
            locale.setlocale(locale.LC_ALL, '')
            self.stdscr.addstr(0, 0, "●", curses.color_pair(1))
            self.stdscr.refresh()
            self.stdscr.clear()
            self.use_unicode = True
            self.SYMBOL_EMPTY = '·'
            self.SYMBOL_BLACK = '●'
            self.SYMBOL_WHITE = '○'
            self.SYMBOL_CURSOR = '◆'
        except:
            self.use_unicode = False
            self.SYMBOL_EMPTY = '+'
            self.SYMBOL_BLACK = 'X'
            self.SYMBOL_WHITE = 'O'
            self.SYMBOL_CURSOR = '#'
    
    def _update_window_size(self):
        """更新窗口尺寸"""
        self.term_height, self.term_width = self.stdscr.getmaxyx()
        
        # 动态计算棋盘实际宽度: 行标签(3字符) + 棋盘列数 * 2
        from .board import Board
        board_width = 3 + Board.SIZE * 2  # 25x25棋盘 = 3 + 50 = 53
        remaining_width = self.term_width - board_width - 2
        
        if remaining_width >= self.CHAT_MIN_WIDTH:
            self.chat_enabled = True
            self.chat_start_x = board_width + 2
            self.chat_width = min(remaining_width, self.CHAT_MAX_WIDTH)
        else:
            self.chat_enabled = False
    
    def cleanup(self):
        """清理curses"""
        if self.stdscr:
            self.stdscr.keypad(False)
            curses.nocbreak()
            curses.echo()
            curses.endwin()
    
    def safe_addstr(self, y, x, text, attr=0):
        """安全地添加字符串"""
        try:
            if y >= 0 and y < self.term_height and x >= 0:
                max_len = self.term_width - x
                if max_len > 0:
                    self.stdscr.addstr(y, x, text[:max_len], attr)
        except curses.error:
            pass
    
    def draw_board(self, board, last_move=None):
        """绘制棋盘"""
        self.stdscr.clear()
        self._update_window_size()
        
        # 标题
        title = "=== Terminal Gomoku - VS AI ==="
        if self.chat_enabled:
            title += " [C:Chat]"
        self.safe_addstr(0, 2, title, curses.color_pair(self.COLOR_TITLE) | curses.A_BOLD)
        
        # 列标签 (A-O)
        col_labels = "   " + " ".join([chr(65 + i) for i in range(board.SIZE)])
        self.safe_addstr(2, 0, col_labels, curses.color_pair(self.COLOR_BOARD))
        
        # 绘制棋盘
        for row in range(board.SIZE):
            row_label = f"{row + 1:2d} "
            self.safe_addstr(3 + row, 0, row_label, curses.color_pair(self.COLOR_BOARD))
            
            for col in range(board.SIZE):
                stone = board.get_stone(row, col)
                x_pos = 3 + col * 2
                y_pos = 3 + row
                
                is_cursor = (row == self.cursor_row and col == self.cursor_col)
                is_last = (last_move and last_move[0] == row and last_move[1] == col)
                
                if is_cursor:
                    if stone == board.EMPTY:
                        symbol = self.SYMBOL_CURSOR
                        color = curses.color_pair(self.COLOR_CURSOR) | curses.A_BOLD
                    elif stone == board.BLACK:
                        symbol = self.SYMBOL_BLACK
                        color = curses.color_pair(self.COLOR_BLACK) | curses.A_BOLD | curses.A_UNDERLINE | curses.A_STANDOUT
                    elif stone == board.WHITE:
                        symbol = self.SYMBOL_WHITE
                        color = curses.color_pair(self.COLOR_WHITE) | curses.A_BOLD | curses.A_UNDERLINE | curses.A_STANDOUT
                elif stone == board.BLACK:
                    symbol = self.SYMBOL_BLACK
                    if is_last:
                        color = curses.color_pair(self.COLOR_LAST_MOVE) | curses.A_BOLD
                    else:
                        color = curses.color_pair(self.COLOR_BLACK) | curses.A_BOLD
                elif stone == board.WHITE:
                    symbol = self.SYMBOL_WHITE
                    if is_last:
                        color = curses.color_pair(self.COLOR_LAST_MOVE) | curses.A_BOLD
                    else:
                        color = curses.color_pair(self.COLOR_WHITE) | curses.A_BOLD
                else:
                    symbol = self.SYMBOL_EMPTY
                    color = curses.color_pair(self.COLOR_BOARD)
                
                self.safe_addstr(y_pos, x_pos, symbol, color)
        
        # 状态栏
        status_y = board.SIZE + 4
        self.safe_addstr(status_y, 0, "-" * 35, curses.color_pair(self.COLOR_BOARD))
        
        # 绘制聊天区域
        if self.chat_enabled:
            self._draw_chat_area(board.SIZE)
    
    def _draw_chat_area(self, board_size: int):
        """绘制聊天区域"""
        chat_height = board_size + 5
        
        # 绘制边框
        border_char = "│" if self.use_unicode else "|"
        top_border = "┌" + "─" * (self.chat_width - 2) + "┐" if self.use_unicode else "+" + "-" * (self.chat_width - 2) + "+"
        bottom_border = "└" + "─" * (self.chat_width - 2) + "┘" if self.use_unicode else "+" + "-" * (self.chat_width - 2) + "+"
        
        # 顶部边框
        self.safe_addstr(1, self.chat_start_x, top_border, curses.color_pair(self.COLOR_CHAT_BORDER))
        
        # 标题
        chat_title = " 💬 AI Chat " if self.use_unicode else " AI Chat "
        title_x = self.chat_start_x + (self.chat_width - len(chat_title)) // 2
        self.safe_addstr(1, title_x, chat_title, curses.color_pair(self.COLOR_TITLE) | curses.A_BOLD)
        
        # 左右边框和消息区域
        msg_area_height = chat_height - 5
        for i in range(msg_area_height):
            self.safe_addstr(2 + i, self.chat_start_x, border_char, curses.color_pair(self.COLOR_CHAT_BORDER))
            self.safe_addstr(2 + i, self.chat_start_x + self.chat_width - 1, border_char, curses.color_pair(self.COLOR_CHAT_BORDER))
        
        # 绘制消息
        self._draw_chat_messages(msg_area_height)
        
        # 分隔线
        sep_y = 2 + msg_area_height
        sep_line = "├" + "─" * (self.chat_width - 2) + "┤" if self.use_unicode else "+" + "-" * (self.chat_width - 2) + "+"
        self.safe_addstr(sep_y, self.chat_start_x, sep_line, curses.color_pair(self.COLOR_CHAT_BORDER))
        
        # 输入区域
        input_y = sep_y + 1
        self.safe_addstr(input_y, self.chat_start_x, border_char, curses.color_pair(self.COLOR_CHAT_BORDER))
        self.safe_addstr(input_y, self.chat_start_x + self.chat_width - 1, border_char, curses.color_pair(self.COLOR_CHAT_BORDER))
        
        # 输入提示或AI状态
        if self.ai_typing:
            prompt = " AI typing..."
            self.safe_addstr(input_y, self.chat_start_x + 1, prompt, curses.color_pair(self.COLOR_CHAT_AI))
        elif self.input_mode == InputMode.CHAT:
            # 显示输入内容
            prompt = "> "
            max_input_width = self.chat_width - 4
            display_text = self.chat_input_buffer[-max_input_width:] if len(self.chat_input_buffer) > max_input_width else self.chat_input_buffer
            self.safe_addstr(input_y, self.chat_start_x + 1, prompt + display_text, curses.color_pair(self.COLOR_INPUT) | curses.A_BOLD)
            # 显示光标
            cursor_x = self.chat_start_x + 1 + len(prompt) + len(display_text)
            if cursor_x < self.chat_start_x + self.chat_width - 1:
                self.safe_addstr(input_y, cursor_x, "_", curses.color_pair(self.COLOR_INPUT) | curses.A_BLINK)
        else:
            hint = " Press C to chat"
            self.safe_addstr(input_y, self.chat_start_x + 1, hint, curses.color_pair(self.COLOR_BOARD))
        
        # 底部边框
        self.safe_addstr(input_y + 1, self.chat_start_x, bottom_border, curses.color_pair(self.COLOR_CHAT_BORDER))
    
    def _draw_chat_messages(self, area_height: int):
        """绘制聊天消息"""
        if not self.chat_messages:
            # 显示欢迎消息
            welcome = "Start chatting!"
            y = 2 + area_height // 2
            x = self.chat_start_x + (self.chat_width - len(welcome)) // 2
            self.safe_addstr(y, x, welcome, curses.color_pair(self.COLOR_BOARD))
            return
        
        # 收集所有要显示的行
        all_lines = []
        for role, lines in self.chat_messages:
            prefix = "You: " if role == "user" else "AI: "
            color = self.COLOR_CHAT_USER if role == "user" else self.COLOR_CHAT_AI
            
            for i, line in enumerate(lines):
                if i == 0:
                    all_lines.append((prefix + line, color))
                else:
                    all_lines.append(("    " + line, color))
        
        # 计算显示范围（从底部往上显示）
        total_lines = len(all_lines)
        start_idx = max(0, total_lines - area_height + self.chat_scroll)
        end_idx = min(total_lines, start_idx + area_height)
        
        # 绘制消息
        display_lines = all_lines[start_idx:end_idx]
        for i, (line, color) in enumerate(display_lines):
            y = 2 + i
            x = self.chat_start_x + 1
            max_len = self.chat_width - 3
            display_text = line[:max_len]
            self.safe_addstr(y, x, display_text, curses.color_pair(color))
    
    def update_chat_messages(self, messages: List[Tuple[str, List[str]]]):
        """更新聊天消息"""
        self.chat_messages = messages
        self.chat_scroll = 0  # 重置滚动
    
    def add_chat_message(self, role: str, lines: List[str]):
        """添加单条聊天消息"""
        self.chat_messages.append((role, lines))
        self.chat_scroll = 0
    
    def set_ai_typing(self, typing: bool):
        """设置AI正在输入状态"""
        self.ai_typing = typing
    
    def set_input_mode(self, mode: InputMode):
        """设置输入模式"""
        self.input_mode = mode
        if mode == InputMode.GAME:
            self.chat_input_buffer = ""
    
    def get_input_mode(self) -> InputMode:
        """获取当前输入模式"""
        return self.input_mode
    
    def append_chat_input(self, char: str):
        """追加聊天输入字符"""
        max_len = 200  # 最大输入长度
        if len(self.chat_input_buffer) < max_len:
            self.chat_input_buffer += char
    
    def backspace_chat_input(self):
        """删除聊天输入的最后一个字符"""
        if self.chat_input_buffer:
            self.chat_input_buffer = self.chat_input_buffer[:-1]
    
    def get_chat_input(self) -> str:
        """获取并清空聊天输入"""
        text = self.chat_input_buffer
        self.chat_input_buffer = ""
        return text
    
    def clear_chat_input(self):
        """清空聊天输入"""
        self.chat_input_buffer = ""
    
    def draw_status(self, game_state):
        """绘制状态信息"""
        difficulty_text = {
            'easy': 'Easy',
            'medium': 'Medium',
            'hard': 'Hard',
            'ai': 'AI'
        }.get(game_state.get('difficulty', 'medium'), 'Medium')
        
        cursor_col_label = chr(65 + self.cursor_col) if self.cursor_col < 26 else '?'
        cursor_pos = f"({cursor_col_label}{self.cursor_row + 1})"
        
        # AI提供商信息
        ai_provider = game_state.get('ai_provider', '')
        if ai_provider:
            status_line = f"AI: {ai_provider} | Turn: {game_state.get('turn', 0)} | Pos: {cursor_pos} | "
        else:
            status_line = f"Diff: {difficulty_text} | Turn: {game_state.get('turn', 0)} | Pos: {cursor_pos} | "
        
        current = game_state.get('current_player', 'black')
        if current == 'black':
            status_line += "Current: You(●)" if self.use_unicode else "Current: You(X)"
        else:
            status_line += "Current: AI(○)" if self.use_unicode else "Current: AI(O)"
        
        from .board import Board
        status_y = Board.SIZE + 5
        self.safe_addstr(status_y, 0, status_line[:35], curses.color_pair(self.COLOR_TITLE))
        
        # 消息
        message = game_state.get('message', '')
        if message:
            msg_y = Board.SIZE + 6
            self.safe_addstr(msg_y, 0, message[:35], curses.color_pair(self.COLOR_CURSOR) | curses.A_BOLD)
    
    def draw_controls(self):
        """绘制操作说明"""
        from .board import Board
        controls_y = Board.SIZE + 8
        
        if self.input_mode == InputMode.CHAT:
            controls = [
                "Chat: Type message, Enter to send",
                "      ESC - Exit chat mode"
            ]
        else:
            controls = [
                "Move: Arrows/WASD | Place: Enter",
                "C-Chat Q-Quit R-Restart H-Help"
            ]
        
        for i, text in enumerate(controls):
            self.safe_addstr(controls_y + i, 0, text[:35], curses.color_pair(self.COLOR_BOARD))
    
    def draw_help(self):
        """绘制帮助信息"""
        self.stdscr.clear()
        
        help_text = [
            "=======================================",
            "        Gomoku Game Help",
            "=======================================",
            "",
            "Goal:",
            "  Form 5 consecutive stones in a row",
            "",
            "Controls:",
            "  Arrow Keys/WASD - Move cursor",
            "  Enter/Space     - Place stone",
            "  C - Open chat with AI",
            "  Q - Quit game",
            "  R - Restart",
            "  H - Show/Hide help",
            "",
            "Chat Mode:",
            "  Type message and press Enter",
            "  ESC - Exit chat mode",
            "",
            "AI Settings (Environment Variables):",
            "  AI_PROVIDER - openai/anthropic",
            "  AI_API_KEY  - Your API key",
            "  AI_MODEL    - Model name (optional)",
            "",
            "Press any key to return...",
        ]
        
        for i, line in enumerate(help_text):
            color = curses.color_pair(self.COLOR_TITLE) if i < 3 else curses.color_pair(self.COLOR_BOARD)
            self.safe_addstr(i, 2, line, color)
        
        self.stdscr.refresh()
        self.stdscr.timeout(-1)  # 阻塞等待
        self.stdscr.getch()
        self.stdscr.timeout(100)  # 恢复非阻塞
    
    def draw_game_over(self, winner, board):
        """绘制游戏结束界面"""
        self.draw_board(board, board.last_move)
        
        y_pos = board.SIZE + 5
        self.safe_addstr(y_pos, 0, "=" * 35, curses.color_pair(self.COLOR_TITLE))
        
        if winner == 'black':
            msg = "You Win!"
        elif winner == 'white':
            msg = "AI Wins!"
        else:
            msg = "Draw!"
        
        self.safe_addstr(y_pos + 1, 2, msg, curses.color_pair(self.COLOR_CURSOR) | curses.A_BOLD)
        self.safe_addstr(y_pos + 2, 2, "R-Restart Q-Quit", curses.color_pair(self.COLOR_BOARD))
        
        self.stdscr.refresh()
    
    def get_input(self):
        """获取用户输入"""
        return self.stdscr.getch()
    
    def get_input_blocking(self):
        """阻塞式获取用户输入"""
        self.stdscr.timeout(-1)
        key = self.stdscr.getch()
        self.stdscr.timeout(100)
        return key
    
    def move_cursor(self, direction, board_size):
        """移动光标"""
        if direction == 'up':
            self.cursor_row = max(0, self.cursor_row - 1)
        elif direction == 'down':
            self.cursor_row = min(board_size - 1, self.cursor_row + 1)
        elif direction == 'left':
            self.cursor_col = max(0, self.cursor_col - 1)
        elif direction == 'right':
            self.cursor_col = min(board_size - 1, self.cursor_col + 1)
    
    def get_cursor_position(self):
        """获取当前光标位置"""
        return (self.cursor_row, self.cursor_col)
    
    def reset_cursor(self):
        """重置光标到中心"""
        self.cursor_row = 7
        self.cursor_col = 7
    
    def refresh(self):
        """刷新屏幕"""
        self.stdscr.refresh()
    
    def show_ai_thinking(self, message: str = "AI thinking..."):
        """显示AI思考中"""
        from .board import Board
        msg_y = Board.SIZE + 6
        self.safe_addstr(msg_y, 0, message[:35], curses.color_pair(self.COLOR_CURSOR) | curses.A_BOLD)
        self.stdscr.refresh()
    
    def is_chat_enabled(self) -> bool:
        """检查聊天功能是否启用"""
        return self.chat_enabled
    
    def clear_chat(self):
        """清空聊天消息"""
        self.chat_messages = []
        self.chat_scroll = 0
        self.chat_input_buffer = ""
