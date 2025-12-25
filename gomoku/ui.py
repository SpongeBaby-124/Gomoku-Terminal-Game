"""
UI界面 - 使用curses实现终端界面
"""

try:
    import curses
except ImportError:
    import sys
    print("错误: 未安装curses库")
    print("Windows用户请运行: pip install windows-curses")
    sys.exit(1)


class GomokuUI:
    """五子棋终端界面"""
    
    # 颜色对
    COLOR_BOARD = 1
    COLOR_BLACK = 2
    COLOR_WHITE = 3
    COLOR_CURSOR = 4
    COLOR_LAST_MOVE = 5
    COLOR_TITLE = 6
    
    # 显示符号 - 使用ASCII兼容字符
    SYMBOL_EMPTY = '+'
    SYMBOL_BLACK = 'X'
    SYMBOL_WHITE = 'O'
    SYMBOL_CURSOR = '#'
    
    def __init__(self):
        """初始化UI"""
        self.stdscr = None
        self.cursor_row = 12
        self.cursor_col = 12
        self.message = ""
        self.use_unicode = True  # 是否使用Unicode字符
    
    
    def init(self):
        """初始化curses"""
        self.stdscr = curses.initscr()
        curses.start_color()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)  # 隐藏光标
        self.stdscr.keypad(True)
        
        # 初始化颜色对
        curses.init_pair(self.COLOR_BOARD, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(self.COLOR_BLACK, curses.COLOR_BLACK, curses.COLOR_BLACK)
        curses.init_pair(self.COLOR_WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(self.COLOR_CURSOR, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(self.COLOR_LAST_MOVE, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(self.COLOR_TITLE, curses.COLOR_CYAN, curses.COLOR_BLACK)
        
        # 尝试支持UTF-8
        try:
            import locale
            locale.setlocale(locale.LC_ALL, '')
            # 测试是否支持Unicode
            self.stdscr.addstr(0, 0, "●", curses.color_pair(1))
            self.stdscr.refresh()
            self.stdscr.clear()
            self.use_unicode = True
            # 使用Unicode符号
            self.SYMBOL_EMPTY = '·'
            self.SYMBOL_BLACK = '●'
            self.SYMBOL_WHITE = '○'
            self.SYMBOL_CURSOR = '◆'
        except:
            # 如果不支持，使用ASCII字符
            self.use_unicode = False
            self.SYMBOL_EMPTY = '+'
            self.SYMBOL_BLACK = 'X'
            self.SYMBOL_WHITE = 'O'
            self.SYMBOL_CURSOR = '#'
        
        self.stdscr.clear()
        
    def cleanup(self):
        """清理curses"""
        if self.stdscr:
            self.stdscr.keypad(False)
            curses.nocbreak()
            curses.echo()
            curses.endwin()
    
    def safe_addstr(self, y, x, text, attr=0):
        """安全地添加字符串，处理异常"""
        try:
            self.stdscr.addstr(y, x, text, attr)
        except curses.error:
            # 忽略边界错误
            pass
    
    def draw_board(self, board, last_move=None):
        """绘制棋盘"""
        self.stdscr.clear()
        
        # 标题
        if self.use_unicode:
            title = "=== Terminal Gomoku - VS AI ==="
        else:
            title = "=== Terminal Gomoku - VS AI ==="
        self.safe_addstr(0, 2, title, curses.color_pair(self.COLOR_TITLE) | curses.A_BOLD)
        
        # 列标签 (A-O)
        col_labels = "   " + " ".join([chr(65 + i) for i in range(board.SIZE)])
        self.safe_addstr(2, 0, col_labels, curses.color_pair(self.COLOR_BOARD))
        
        # 绘制棋盘
        for row in range(board.SIZE):
            # 行号
            row_label = f"{row + 1:2d} "
            self.safe_addstr(3 + row, 0, row_label, curses.color_pair(self.COLOR_BOARD))
            
            # 绘制每个位置
            for col in range(board.SIZE):
                stone = board.get_stone(row, col)
                x_pos = 3 + col * 2
                y_pos = 3 + row
                
                # 判断是否是光标位置或最后落子位置
                is_cursor = (row == self.cursor_row and col == self.cursor_col)
                is_last = (last_move and last_move[0] == row and last_move[1] == col)
                
                # 选择显示内容和颜色
                # 光标位置：显示原内容但加上下划线和闪烁效果（朦胧透视）
                if is_cursor:
                    if stone == board.EMPTY:
                        # 空位显示光标符号
                        symbol = self.SYMBOL_CURSOR
                        color = curses.color_pair(self.COLOR_CURSOR) | curses.A_BOLD
                    elif stone == board.BLACK:
                        # 有黑棋：显示黑棋，加下划线高亮（透视效果）
                        symbol = self.SYMBOL_BLACK
                        color = curses.color_pair(self.COLOR_BLACK) | curses.A_BOLD | curses.A_UNDERLINE | curses.A_STANDOUT
                    elif stone == board.WHITE:
                        # 有白棋：显示白棋，加下划线高亮（透视效果）
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
        self.safe_addstr(status_y, 0, "-" * 60, curses.color_pair(self.COLOR_BOARD))
        
    def draw_status(self, game_state):
        """绘制状态信息
        
        Args:
            game_state: dict with keys: difficulty, turn, current_player, message
        """
        difficulty_text = {
            'easy': 'Easy',
            'medium': 'Medium',
            'hard': 'Hard'
        }.get(game_state.get('difficulty', 'medium'), 'Medium')
        
        # 显示当前光标位置（列字母+行号）
        cursor_col_label = chr(65 + self.cursor_col) if self.cursor_col < 26 else '?'
        cursor_pos = f"({cursor_col_label}{self.cursor_row + 1})"
        
        status_line = f"Difficulty: {difficulty_text} | Turn: {game_state.get('turn', 0)} | Position: {cursor_pos} | "
        
        current = game_state.get('current_player', 'black')
        if current == 'black':
            if self.use_unicode:
                status_line += "Current: Player(Black)"
            else:
                status_line += "Current: Player(X)"
        else:
            if self.use_unicode:
                status_line += "Current: AI(White)"
            else:
                status_line += "Current: AI(O)"
        
        # 动态计算状态栏位置
        from .board import Board
        status_y = Board.SIZE + 5
        self.safe_addstr(status_y, 0, status_line, curses.color_pair(self.COLOR_TITLE))
        
        # 消息
        message = game_state.get('message', '')
        if message:
            from .board import Board
            msg_y = Board.SIZE + 6
            self.safe_addstr(msg_y, 0, message, curses.color_pair(self.COLOR_CURSOR) | curses.A_BOLD)
        
    def draw_controls(self):
        """绘制操作说明"""
        controls = [
            "Controls: Arrow Keys or WASD - Move cursor",
            "          Enter/Space - Place stone | Q - Quit | R - Restart | H - Help"
        ]
        
        from .board import Board
        controls_y = Board.SIZE + 8
        for i, text in enumerate(controls):
            self.safe_addstr(controls_y + i, 0, text, curses.color_pair(self.COLOR_BOARD))
    
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
            "  Horizontal, vertical, or diagonal",
            "",
            "Controls:",
            "  Arrow Keys or WASD - Move cursor",
            "  Enter or Space     - Place stone",
            "  Q - Quit game",
            "  R - Restart",
            "  H - Show/Hide help",
            "",
            "Difficulty:",
            "  Easy   - Basic AI strategy",
            "  Medium - Scoring system",
            "  Hard   - Search algorithm",
            "",
            "Symbols:",
            "  X or Black - Player",
            "  O or White - AI",
            "  # - Cursor position",
            "  + - Empty space",
            "",
            "Press any key to return to game...",
        ]
        
        for i, line in enumerate(help_text):
            color = curses.color_pair(self.COLOR_TITLE) if i < 3 else curses.color_pair(self.COLOR_BOARD)
            self.safe_addstr(i, 2, line, color)
        
        self.stdscr.refresh()
        self.stdscr.getch()
    
    def draw_game_over(self, winner, board):
        """绘制游戏结束界面"""
        # 先绘制最终棋盘
        self.draw_board(board, board.last_move)
        
        # 游戏结束消息
        y_pos = board.SIZE + 5
        self.safe_addstr(y_pos, 0, "=" * 60, curses.color_pair(self.COLOR_TITLE))
        
        if winner == 'black':
            msg = "Congratulations! You Win!"
        elif winner == 'white':
            msg = "AI Wins! Try again!"
        else:
            msg = "Draw Game!"
        
        self.safe_addstr(y_pos + 1, 5, msg, 
                          curses.color_pair(self.COLOR_CURSOR) | curses.A_BOLD)
        self.safe_addstr(y_pos + 2, 5, "Press R to Restart, Q to Quit", 
                          curses.color_pair(self.COLOR_BOARD))
        
        self.stdscr.refresh()
    
    def get_input(self):
        """获取用户输入"""
        return self.stdscr.getch()
    
    def move_cursor(self, direction, board_size):
        """移动光标
        
        Args:
            direction: 'up', 'down', 'left', 'right'
            board_size: 棋盘大小
        """
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
        self.cursor_row = 12
        self.cursor_col = 12
    
    def refresh(self):
        """刷新屏幕"""
        self.stdscr.refresh()
    
    def show_ai_thinking(self):
        """显示AI思考中"""
        from .board import Board
        msg_y = Board.SIZE + 6
        self.safe_addstr(msg_y, 0, "AI is thinking...", 
                          curses.color_pair(self.COLOR_CURSOR) | curses.A_BOLD)
        self.stdscr.refresh()
