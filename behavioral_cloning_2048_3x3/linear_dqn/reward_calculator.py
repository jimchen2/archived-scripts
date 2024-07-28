import numpy as np

class RewardCalculator:
    @staticmethod
    def calculate_reward(old_board, new_board):
        # if np.array_equal(old_board, new_board):
        #     return -1
        
        reward = 0
                
        # reward += RewardCalculator.position_reward(new_board)

        # old_max = np.max(old_board)
        # new_max = np.max(new_board)
        # reward += 1000000* (new_max-old_max)*new_max

        # # Reward for empty spaces
        # old_empty = np.count_nonzero(old_board == 0)
        # new_empty = np.count_nonzero(new_board == 0)
        # reward += 10* (new_empty - old_empty)

        reward += 1
        return reward
    



#     def position_reward(board):
#         reward = 0
#         sorted_tiles = np.sort(board.flatten())[::-1][:4]  # Top 4 largest tiles
        
#         for i, tile in enumerate(sorted_tiles):
#             if i == 0:  
#                 if tile == board[0, 0] or tile < 8:
#                     pass
#                 else:
#                     reward -= 20000
#             if i == 1: 
#                 if tile == board[0, 1] or tile < 7 or tile + 2 < sorted_tiles[0] :
#                     pass 
#                 else:
#                     reward -= 1000
#             if i == 2: 
#                 if tile == board[0, 2] or tile < 7 or tile + 3 < sorted_tiles[0] or tile == board[1,0]:
#                     pass 
#                 else:
#                     reward -= 50

#         return reward


# if __name__ == "__main__":
#     # Example usage
#     old_board = np.array([[4, 2, 2, 0],
#                           [2, 0, 0, 0],
#                           [0, 0, 0, 0],
#                           [0, 0, 0, 0]])
    
#     new_board = np.array([[4, 3, 0, 0],
#                           [2, 0, 0, 0],
#                           [0, 0, 0, 0],
#                           [0, 0, 0, 1]])
    
#     reward_calc = RewardCalculator()
#     reward = reward_calc.calculate_reward(old_board, new_board)
#     print(f"Reward: {reward}")