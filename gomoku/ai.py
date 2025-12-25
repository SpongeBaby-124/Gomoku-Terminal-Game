"""
AI引擎 - 三种难度的人工智能对手
"""

import random
from typing import Tuple, List, Optional


class GomokuAI:
    """五子棋AI引擎"""
    
    # 评分权重
    SCORE_FIVE = 100000      # 连五
    SCORE_LIVE_FOUR = 10000  # 活四
    SCORE_RUSH_FOUR = 1000   # 冲四
    SCORE_LIVE_THREE = 1000  # 活三
    SCORE_SLEEP_THREE = 100  # 眠三
    SCORE_LIVE_TWO = 100     # 活二
    SCORE_SLEEP_TWO = 10     # 眠二
    
    def __init__(self, difficulty="medium"):
        """
        初始化AI
        
        Args:
            difficulty: 难度级别 easy/medium/hard
        """
        self.difficulty = difficulty.lower()
        
    def get_move(self, board, player) -> Optional[Tuple[int, int]]:
        """
        获取AI的下一步落子位置
        
        Args:
            board: Board对象
            player: 当前玩家 (Board.BLACK 或 Board.WHITE)
            
        Returns:
            (row, col) 或 None
        """
        if self.difficulty == "easy":
            return self._easy_move(board, player)
        elif self.difficulty == "medium":
            return self._medium_move(board, player)
        elif self.difficulty == "hard":
            return self._hard_move(board, player)
        else:
            return self._medium_move(board, player)
    
    def _easy_move(self, board, player) -> Optional[Tuple[int, int]]:
        """简单难度 - 增强版基础策略"""
        opponent = board.BLACK if player == board.WHITE else board.WHITE
        
        # 1. 必胜检查：如果AI能连成5子，立即落子
        winning_move = self._find_winning_move(board, player)
        if winning_move:
            return winning_move
        
        # 2. 必防检查：如果对手能连成5子，必须阻挡
        blocking_move = self._find_winning_move(board, opponent)
        if blocking_move:
            return blocking_move
        
        # 3. 进攻：尝试形成4子连线（包括活四和冲四）
        attack_move = self._find_four_threat(board, player)
        if attack_move and random.random() > 0.3:  # 70%概率进攻
            return attack_move
        
        # 4. 防守：阻挡对手的4子连线
        defense_move = self._find_four_threat(board, opponent)
        if defense_move:
            return defense_move
        
        # 5. 尝试形成3子连线
        three_move = self._find_three_threat(board, player)
        if three_move and random.random() > 0.4:  # 60%概率
            return three_move
        
        # 6. 阻挡对手的3子连线
        block_three = self._find_three_threat(board, opponent)
        if block_three and random.random() > 0.3:  # 70%概率
            return block_three
        
        # 7. 在合理范围内随机选择（已有棋子附近）
        nearby_positions = board.get_nearby_positions(distance=2)
        if nearby_positions:
            return random.choice(nearby_positions)
        
        # 8. 如果棋盘为空，选择中心
        if board.move_count == 0:
            center = board.SIZE // 2
            return (center, center)
        
        # 9. 随机落子
        empty_positions = board.get_empty_positions()
        return random.choice(empty_positions) if empty_positions else None
    
    def _medium_move(self, board, player) -> Optional[Tuple[int, int]]:
        """中等难度 - 评分系统"""
        opponent = board.BLACK if player == board.WHITE else board.WHITE
        
        # 1. 必胜检查
        winning_move = self._find_winning_move(board, player)
        if winning_move:
            return winning_move
        
        # 2. 必防检查
        blocking_move = self._find_winning_move(board, opponent)
        if blocking_move:
            return blocking_move
        
        # 3. 评估所有可行位置
        candidates = board.get_nearby_positions(distance=2)
        if not candidates:
            candidates = board.get_empty_positions()
        
        if not candidates:
            return None
        
        # 评分每个位置
        best_score = -1
        best_moves = []
        
        for row, col in candidates:
            # 计算进攻得分
            attack_score = self._evaluate_position(board, row, col, player)
            # 计算防守得分
            defense_score = self._evaluate_position(board, row, col, opponent)
            
            # 综合得分（防守权重稍高）
            total_score = attack_score + defense_score * 1.1
            
            if total_score > best_score:
                best_score = total_score
                best_moves = [(row, col)]
            elif total_score == best_score:
                best_moves.append((row, col))
        
        return random.choice(best_moves) if best_moves else None
    
    def _hard_move(self, board, player) -> Optional[Tuple[int, int]]:
        """困难难度 - Minimax算法"""
        opponent = board.BLACK if player == board.WHITE else board.WHITE
        
        # 1. 必胜检查
        winning_move = self._find_winning_move(board, player)
        if winning_move:
            return winning_move
        
        # 2. 必防检查
        blocking_move = self._find_winning_move(board, opponent)
        if blocking_move:
            return blocking_move
        
        # 3. Minimax搜索
        depth = 2 if board.move_count < 10 else 3  # 后期搜索更深
        candidates = board.get_nearby_positions(distance=2)
        
        if not candidates:
            candidates = board.get_empty_positions()
        
        if not candidates:
            return None
        
        # 限制候选位置数量以提高性能
        if len(candidates) > 20:
            # 预评估并选择前20个最优位置
            scored_candidates = []
            for row, col in candidates:
                score = self._evaluate_position(board, row, col, player)
                score += self._evaluate_position(board, row, col, opponent)
                scored_candidates.append((score, row, col))
            scored_candidates.sort(reverse=True)
            candidates = [(r, c) for _, r, c in scored_candidates[:20]]
        
        best_score = float('-inf')
        best_move = None
        
        for row, col in candidates:
            # 尝试落子
            board.place_stone(row, col, player)
            
            # Minimax评估
            score = self._minimax(board, depth - 1, float('-inf'), float('inf'), False, player, opponent)
            
            # 撤销落子
            board.board[row][col] = board.EMPTY
            board.move_count -= 1
            
            if score > best_score:
                best_score = score
                best_move = (row, col)
        
        return best_move
    
    def _minimax(self, board, depth, alpha, beta, is_maximizing, player, opponent):
        """Minimax算法与Alpha-Beta剪枝"""
        # 终止条件
        if depth == 0:
            return self._evaluate_board(board, player, opponent)
        
        candidates = board.get_nearby_positions(distance=2)
        if not candidates or len(candidates) > 15:
            candidates = candidates[:15] if candidates else []
        
        if is_maximizing:
            max_eval = float('-inf')
            for row, col in candidates:
                board.place_stone(row, col, player)
                
                if board.check_win(row, col):
                    board.board[row][col] = board.EMPTY
                    board.move_count -= 1
                    return self.SCORE_FIVE
                
                eval_score = self._minimax(board, depth - 1, alpha, beta, False, player, opponent)
                board.board[row][col] = board.EMPTY
                board.move_count -= 1
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for row, col in candidates:
                board.place_stone(row, col, opponent)
                
                if board.check_win(row, col):
                    board.board[row][col] = board.EMPTY
                    board.move_count -= 1
                    return -self.SCORE_FIVE
                
                eval_score = self._minimax(board, depth - 1, alpha, beta, True, player, opponent)
                board.board[row][col] = board.EMPTY
                board.move_count -= 1
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    def _evaluate_board(self, board, player, opponent):
        """评估整个棋盘局面"""
        player_score = 0
        opponent_score = 0
        
        # 评估所有已有棋子
        for row in range(board.SIZE):
            for col in range(board.SIZE):
                if board.board[row][col] == player:
                    player_score += self._evaluate_position(board, row, col, player)
                elif board.board[row][col] == opponent:
                    opponent_score += self._evaluate_position(board, row, col, opponent)
        
        return player_score - opponent_score * 1.1
    
    def _evaluate_position(self, board, row, col, player):
        """评估某个位置的价值"""
        # 临时落子
        original = board.board[row][col]
        board.board[row][col] = player
        
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dx, dy in directions:
            line_score = self._evaluate_line(board, row, col, dx, dy, player)
            score += line_score
        
        # 恢复
        board.board[row][col] = original
        
        return score
    
    def _evaluate_line(self, board, row, col, dx, dy, player):
        """评估一条线的价值"""
        count = 1
        empty_left = 0
        empty_right = 0
        
        # 向左/上统计
        x, y = row - dx, col - dy
        while 0 <= x < board.SIZE and 0 <= y < board.SIZE and count < 5:
            if board.board[x][y] == player:
                count += 1
            elif board.board[x][y] == board.EMPTY:
                empty_left = 1
                break
            else:
                break
            x -= dx
            y -= dy
        
        # 向右/下统计
        x, y = row + dx, col + dy
        while 0 <= x < board.SIZE and 0 <= y < board.SIZE and count < 5:
            if board.board[x][y] == player:
                count += 1
            elif board.board[x][y] == board.EMPTY:
                empty_right = 1
                break
            else:
                break
            x += dx
            y += dy
        
        # 根据连子数和开口数评分
        if count >= 5:
            return self.SCORE_FIVE
        elif count == 4:
            if empty_left + empty_right == 2:
                return self.SCORE_LIVE_FOUR
            elif empty_left + empty_right == 1:
                return self.SCORE_RUSH_FOUR
        elif count == 3:
            if empty_left + empty_right == 2:
                return self.SCORE_LIVE_THREE
            elif empty_left + empty_right == 1:
                return self.SCORE_SLEEP_THREE
        elif count == 2:
            if empty_left + empty_right == 2:
                return self.SCORE_LIVE_TWO
            elif empty_left + empty_right == 1:
                return self.SCORE_SLEEP_TWO
        
        return 0
    
    def _find_winning_move(self, board, player) -> Optional[Tuple[int, int]]:
        """寻找能立即获胜的位置"""
        candidates = board.get_nearby_positions(distance=2)
        
        for row, col in candidates:
            board.place_stone(row, col, player)
            if board.check_win(row, col):
                board.board[row][col] = board.EMPTY
                board.move_count -= 1
                return (row, col)
            board.board[row][col] = board.EMPTY
            board.move_count -= 1
        
        return None
    
    def _find_four_threat(self, board, player) -> Optional[Tuple[int, int]]:
        """寻找能形成4子连线的位置"""
        candidates = board.get_nearby_positions(distance=2)
        
        for row, col in candidates:
            board.board[row][col] = player
            
            # 检查是否形成4子
            directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
            for dx, dy in directions:
                count = 1
                count += board.count_consecutive(row - dx, col - dy, player, (-dx, -dy))
                count += board.count_consecutive(row + dx, col + dy, player, (dx, dy))
                
                if count >= 4:
                    board.board[row][col] = board.EMPTY
                    return (row, col)
            
            board.board[row][col] = board.EMPTY
        
        return None
    
    def _find_three_threat(self, board, player) -> Optional[Tuple[int, int]]:
        """寻找能形成3子连线的位置"""
        candidates = board.get_nearby_positions(distance=2)
        good_moves = []
        
        for row, col in candidates:
            board.board[row][col] = player
            
            directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
            for dx, dy in directions:
                count = 1
                count += board.count_consecutive(row - dx, col - dy, player, (-dx, -dy))
                count += board.count_consecutive(row + dx, col + dy, player, (dx, dy))
                
                if count >= 3:
                    good_moves.append((row, col))
                    break
            
            board.board[row][col] = board.EMPTY
        
        return random.choice(good_moves) if good_moves else None
