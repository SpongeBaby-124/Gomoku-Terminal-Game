"""
程序入口 - 支持命令行参数
"""

import sys
import argparse
from .game import GomokuGame


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='终端五子棋 - 人机对战游戏',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
难度说明:
  easy   - 简单：AI有基础攻守策略，适合新手
  medium - 中等：AI使用评分系统，有一定挑战性
  hard   - 困难：AI使用搜索算法，难以战胜

示例:
  gomoku              # 默认中等难度
  gomoku -d easy      # 简单难度
  gomoku -d hard      # 困难难度
        """
    )
    
    parser.add_argument(
        '-d', '--difficulty',
        choices=['easy', 'medium', 'hard'],
        default='medium',
        help='AI难度级别 (默认: medium)'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    args = parser.parse_args()
    
    # 创建并运行游戏
    try:
        game = GomokuGame(difficulty=args.difficulty)
        game.run()
    except Exception as e:
        print(f"游戏运行出错: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
