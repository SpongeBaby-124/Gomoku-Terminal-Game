"""
棋盘类 - 管理25x25的五子棋棋盘
"""


class Board:
    """五子棋棋盘类"""
    
    EMPTY = 0
    BLACK = 1  # 玩家 ●
    WHITE = 2  # AI ○
    SIZE = 25
    
    def __init__(self):
        """初始化棋盘"""
        self.board = [[self.EMPTY for _ in range(self.SIZE)] for _ in range(self.SIZE)]
        self.last_move = None  # 记录最后一步 (row, col, player)
        self.move_count = 0
    
    def is_valid_move(self, row, col):
        """检查落子位置是否合法"""
        if not (0 <= row < self.SIZE and 0 <= col < self.SIZE):
            return False
        return self.board[row][col] == self.EMPTY
    
    def place_stone(self, row, col, player):
        """在指定位置落子"""
        if not self.is_valid_move(row, col):
            return False
        
        self.board[row][col] = player
        self.last_move = (row, col, player)
        self.move_count += 1
        return True
    
    def get_stone(self, row, col):
        """获取指定位置的棋子"""
        if 0 <= row < self.SIZE and 0 <= col < self.SIZE:
            return self.board[row][col]
        return None
    
    def check_win(self, row, col):
        """检查指定位置是否形成五子连珠
        
        Args:
            row: 行坐标
            col: 列坐标
            
        Returns:
            bool: 是否获胜
        """
        player = self.board[row][col]
        if player == self.EMPTY:
            return False
        
        # 四个方向：横、竖、左斜、右斜
        directions = [
            [(0, 1), (0, -1)],   # 横向
            [(1, 0), (-1, 0)],   # 纵向
            [(1, 1), (-1, -1)],  # 左上到右下
            [(1, -1), (-1, 1)]   # 右上到左下
        ]
        
        for direction in directions:
            count = 1  # 包含当前位置
            
            # 检查两个方向
            for dx, dy in direction:
                x, y = row + dx, col + dy
                while 0 <= x < self.SIZE and 0 <= y < self.SIZE:
                    if self.board[x][y] == player:
                        count += 1
                        x += dx
                        y += dy
                    else:
                        break
            
            if count >= 5:
                return True
        
        return False
    
    def is_full(self):
        """检查棋盘是否已满"""
        return self.move_count >= self.SIZE * self.SIZE
    
    def get_empty_positions(self):
        """获取所有空位置"""
        positions = []
        for row in range(self.SIZE):
            for col in range(self.SIZE):
                if self.board[row][col] == self.EMPTY:
                    positions.append((row, col))
        return positions
    
    def get_nearby_positions(self, distance=2):
        """获取已有棋子附近的空位置
        
        Args:
            distance: 搜索半径
            
        Returns:
            list: 空位置列表
        """
        positions = set()
        
        # 如果棋盘为空，返回中心位置
        if self.move_count == 0:
            center = self.SIZE // 2
            return [(center, center)]
        
        # 找到所有已有棋子附近的空位
        for row in range(self.SIZE):
            for col in range(self.SIZE):
                if self.board[row][col] != self.EMPTY:
                    # 检查周围的空位
                    for dr in range(-distance, distance + 1):
                        for dc in range(-distance, distance + 1):
                            new_row, new_col = row + dr, col + dc
                            if (0 <= new_row < self.SIZE and 
                                0 <= new_col < self.SIZE and
                                self.board[new_row][new_col] == self.EMPTY):
                                positions.add((new_row, new_col))
        
        return list(positions)
    
    def count_consecutive(self, row, col, player, direction):
        """统计某方向上的连子数
        
        Args:
            row, col: 起始位置
            player: 玩家
            direction: 方向 (dx, dy)
            
        Returns:
            int: 连子数
        """
        dx, dy = direction
        count = 0
        x, y = row, col
        
        while 0 <= x < self.SIZE and 0 <= y < self.SIZE:
            if self.board[x][y] == player:
                count += 1
                x += dx
                y += dy
            else:
                break
        
        return count
    
    def reset(self):
        """重置棋盘"""
        self.board = [[self.EMPTY for _ in range(self.SIZE)] for _ in range(self.SIZE)]
        self.last_move = None
        self.move_count = 0
