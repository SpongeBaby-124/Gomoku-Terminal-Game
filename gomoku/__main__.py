"""
程序入口 - 支持命令行参数和交互式配置
"""

import sys
import argparse
from .game import GomokuGame
from .config import interactive_config, get_config_file, delete_config_file


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='终端五子棋 - 人机对战游戏',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
难度说明:
  easy   - 简单：传统AI，有基础攻守策略，适合新手
  medium - 中等：传统AI，使用评分系统，有一定挑战性
  hard   - 困难：传统AI，使用搜索算法，难以战胜
  ai     - 智能AI：使用配置的AI服务（DeepSeek/GPT/Claude等）

AI服务配置:
  gomoku --config       进入交互式配置向导
  gomoku --show-config  显示当前配置
  gomoku --reset-config 重置配置（恢复传统AI）

示例:
  gomoku              # 使用默认难度（medium）
  gomoku -d easy      # 传统AI简单难度
  gomoku -d ai        # 使用AI服务对战（需要先配置）
  gomoku --config     # 配置AI服务
        """
    )
    
    parser.add_argument(
        '-d', '--difficulty',
        choices=['easy', 'medium', 'hard', 'ai'],
        default='medium',
        help='AI难度级别（easy/medium/hard为传统AI，ai为智能AI服务）'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s 1.0.1'
    )
    
    parser.add_argument(
        '--config',
        action='store_true',
        help='进入交互式AI配置向导'
    )
    
    parser.add_argument(
        '--show-config',
        action='store_true',
        help='显示当前配置信息'
    )
    
    parser.add_argument(
        '--reset-config',
        action='store_true',
        help='重置配置（删除配置文件，恢复传统AI）'
    )
    
    # AI服务命令行参数（可选，覆盖配置文件）
    parser.add_argument(
        '--api-key',
        help='API密钥（覆盖配置文件）'
    )
    
    parser.add_argument(
        '--endpoint',
        help='API端点（覆盖配置文件）'
    )
    
    parser.add_argument(
        '--model',
        help='模型名称（覆盖配置文件）'
    )
    
    args = parser.parse_args()
    
    # 处理配置相关命令
    if args.config:
        interactive_config()
        return
    
    if args.show_config:
        from .config import load_config_from_file, get_config_file
        config = load_config_from_file()
        print(f"\n配置文件: {get_config_file()}")
        if config:
            print("\n当前配置:")
            print(f"  提供商: {config.get('provider', '未设置')}")
            print(f"  模型: {config.get('model', '未设置')}")
            print(f"  端点: {config.get('endpoint') or '默认'}")
            print(f"  API密钥: {'已设置 (' + config.get('api_key', '')[:8] + '...)' if config.get('api_key') else '未设置'}")
            print(f"  超时: {config.get('timeout', 30)}秒")
        else:
            print("\n未找到配置文件，将使用传统AI。")
            print("运行 'gomoku --config' 进行配置。")
        return
    
    if args.reset_config:
        if delete_config_file():
            print("✅ 配置已重置，将使用传统AI。")
        else:
            print("⚠️ 重置失败")
        return
    
    # 创建并运行游戏
    try:
        game = GomokuGame(
            difficulty=args.difficulty,
            cli_api_key=args.api_key,
            cli_endpoint=args.endpoint,
            cli_model=args.model
        )
        game.run()
    except Exception as e:
        print(f"游戏运行出错: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
