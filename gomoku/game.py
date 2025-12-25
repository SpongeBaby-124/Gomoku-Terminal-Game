"""
游戏主逻辑 - 游戏流程控制
"""

import curses
import time
from .board import Board
from .ai import GomokuAI
from .ui import GomokuUI


class GomokuGame:
    """五子棋游戏主类"""
    
    def __init__(self, difficulty="medium"):
        """
        初始化游戏
        
        Args:
            difficulty: AI难度 easy/medium/hard
        """
        self.board = Board()
        self.ai = GomokuAI(difficulty)
        self.ui = GomokuUI()
        self.difficulty = difficulty
        self.current_player = Board.BLACK  # 玩家先手
        self.game_over = False
        self.winner = None
        self.turn = 0
        
    def run(self):
        """运行游戏主循环"""
        try:
            self.ui.init()
            self._game_loop()
        except KeyboardInterrupt:
            pass
        finally:
            self.ui.cleanup()
    
    def _game_loop(self):
        """游戏主循环"""
        show_help = False
        
        while True:
            # 绘制界面
            if show_help:
                self.ui.draw_help()
                show_help = False
                continue
            
            self._draw_game_state()
            
            # 游戏结束处理
            if self.game_over:
                self.ui.draw_game_over(self.winner, self.board)
                
                # 等待用户选择
                key = self.ui.get_input()
                if key in [ord('q'), ord('Q')]:
                    break
                elif key in [ord('r'), ord('R')]:
                    self._reset_game()
                    continue
                else:
                    continue
            
            # 玩家回合
            if self.current_player == Board.BLACK:
                action = self._handle_player_input()
                
                if action == 'quit':
                    break
                elif action == 'restart':
                    self._reset_game()
                elif action == 'help':
                    show_help = True
                elif action == 'move':
                    # 检查胜负
                    if self.board.last_move:
                        row, col, _ = self.board.last_move
                        if self.board.check_win(row, col):
                            self.game_over = True
                            self.winner = 'black'
                            continue
                    
                    # 切换到AI回合
                    self.current_player = Board.WHITE
                    self.turn += 1
            
            # AI回合
            else:
                self.ui.show_ai_thinking()
                time.sleep(0.5)  # 让用户看到"思考中"
                
                ai_move = self.ai.get_move(self.board, Board.WHITE)
                
                if ai_move:
                    row, col = ai_move
                    self.board.place_stone(row, col, Board.WHITE)
                    
                    # 检查胜负
                    if self.board.check_win(row, col):
                        self.game_over = True
                        self.winner = 'white'
                        continue
                    
                    # 切换到玩家回合
                    self.current_player = Board.BLACK
                else:
                    # AI无法落子（棋盘满）
                    self.game_over = True
                    self.winner = 'draw'
            
            # 检查平局
            if self.board.is_full() and not self.game_over:
                self.game_over = True
                self.winner = 'draw'
    
    def _handle_player_input(self):
        """处理玩家输入
        
        Returns:
            str: 'quit', 'restart', 'help', 'move', 'invalid', or None
        """
        key = self.ui.get_input()
        
        # 退出
        if key in [ord('q'), ord('Q')]:
            return 'quit'
        
        # 重新开始
        elif key in [ord('r'), ord('R')]:
            return 'restart'
        
        # 帮助
        elif key in [ord('h'), ord('H')]:
            return 'help'
        
        # 方向键移动
        elif key == curses.KEY_UP or key in [ord('w'), ord('W')]:
            self.ui.move_cursor('up', self.board.SIZE)
        
        elif key == curses.KEY_DOWN or key in [ord('s'), ord('S')]:
            self.ui.move_cursor('down', self.board.SIZE)
        
        elif key == curses.KEY_LEFT or key in [ord('a'), ord('A')]:
            self.ui.move_cursor('left', self.board.SIZE)
        
        elif key == curses.KEY_RIGHT or key in [ord('d'), ord('D')]:
            self.ui.move_cursor('right', self.board.SIZE)
        
        # 落子
        elif key in [curses.KEY_ENTER, ord('\n'), ord('\r'), ord(' ')]:
            row, col = self.ui.get_cursor_position()
            
            if self.board.place_stone(row, col, Board.BLACK):
                return 'move'
            else:
                return 'invalid'
        
        return None
    
    def _draw_game_state(self):
        """绘制当前游戏状态"""
        # 绘制棋盘
        last_move = self.board.last_move[:2] if self.board.last_move else None
        self.ui.draw_board(self.board, last_move)
        
        # 绘制状态
        game_state = {
            'difficulty': self.difficulty,
            'turn': self.turn,
            'current_player': 'black' if self.current_player == Board.BLACK else 'white',
            'message': ''
        }
        self.ui.draw_status(game_state)
        
        # 绘制操作说明
        self.ui.draw_controls()
        
        # 刷新屏幕
        self.ui.refresh()
    
    def _reset_game(self):
        """重置游戏"""
        self.board.reset()
        self.ui.reset_cursor()
        self.current_player = Board.BLACK
        self.game_over = False
        self.winner = None
        self.turn = 0
