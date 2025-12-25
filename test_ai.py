"""
快速测试脚本 - 不使用curses，测试AI逻辑
"""

from gomoku.board import Board
from gomoku.ai import GomokuAI


def print_board(board):
    """打印棋盘（简化版）"""
    print("\n   " + " ".join([chr(65 + i) for i in range(board.SIZE)]))
    for row in range(board.SIZE):
        line = f"{row + 1:2d} "
        for col in range(board.SIZE):
            stone = board.get_stone(row, col)
            if stone == Board.BLACK:
                line += "● "
            elif stone == Board.WHITE:
                line += "○ "
            else:
                line += "· "
        print(line)


def test_ai(difficulty):
    """测试AI"""
    print(f"\n{'='*50}")
    print(f"测试 {difficulty.upper()} 难度 AI")
    print(f"{'='*50}")
    
    board = Board()
    ai = GomokuAI(difficulty)
    
    # 玩家先落子（中心）
    board.place_stone(7, 7, Board.BLACK)
    print("\n玩家落子: (7, 7)")
    print_board(board)
    
    # AI第一步
    ai_move = ai.get_move(board, Board.WHITE)
    if ai_move:
        print(f"\nAI落子: {ai_move}")
        board.place_stone(ai_move[0], ai_move[1], Board.WHITE)
        print_board(board)
    
    # 玩家再落子
    board.place_stone(7, 8, Board.BLACK)
    print("\n玩家落子: (7, 8)")
    print_board(board)
    
    # AI第二步
    ai_move = ai.get_move(board, Board.WHITE)
    if ai_move:
        print(f"\nAI落子: {ai_move}")
        board.place_stone(ai_move[0], ai_move[1], Board.WHITE)
        print_board(board)
    
    print(f"\n✓ {difficulty.upper()} 难度 AI 运行正常")


if __name__ == '__main__':
    print("五子棋 AI 测试")
    print("="*50)
    
    test_ai("easy")
    test_ai("medium")
    test_ai("hard")
    
    print("\n" + "="*50)
    print("✅ 所有AI难度测试完成！")
    print("\n运行游戏请使用:")
    print("  python -m gomoku              # 默认中等难度")
    print("  python -m gomoku -d easy      # 简单难度")
    print("  python -m gomoku -d hard      # 困难难度")
