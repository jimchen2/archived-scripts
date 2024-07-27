import numpy as np
import random

class Game2048Env:
    def __init__(self, n=3):
        self.n = n
        self.reset()

    def reset(self):
        self.board = np.zeros((self.n, self.n), dtype=int)
        self.add_new_tile()
        self.add_new_tile()
        return self.board.copy()

    def step(self, action):
        old_board = self.board.copy()
        
        if action == 0:  # Left
            self.board = self._move_left(self.board)
        elif action == 1:  # Right
            self.board = self._move_right(self.board)
        elif action == 2:  # Up
            self.board = self._move_up(self.board)
        elif action == 3:  # Down
            self.board = self._move_down(self.board)
        else:
            raise ValueError("Invalid action. Must be 0, 1, 2, or 3.")

        # Check if the board state changed
        if not np.array_equal(old_board, self.board):
            self.add_new_tile()

        done = self.is_game_over()
        return self.board.copy(), done, {}
    
    def add_new_tile(self):
        empty_cells = list(zip(*np.where(self.board == 0)))
        if empty_cells:
            x, y = random.choice(empty_cells)
            value = 1 if random.random() < 0.9 else 2
            self.board[x, y] = value

    def is_game_over(self):
        if np.any(self.board == 0):
            return False
        for action in range(4):
            if action == 0:
                test_board = self._move_left(self.board.copy())
            elif action == 1:
                test_board = self._move_right(self.board.copy())
            elif action == 2:
                test_board = self._move_up(self.board.copy())
            elif action == 3:
                test_board = self._move_down(self.board.copy())
            
            if not np.array_equal(test_board, self.board):
                return False
        return True

    def get_legal_actions(self):
        legal_actions = []
        for action in range(4):
            if action == 0:
                test_board = self._move_left(self.board.copy())
            elif action == 1:
                test_board = self._move_right(self.board.copy())
            elif action == 2:
                test_board = self._move_up(self.board.copy())
            elif action == 3:
                test_board = self._move_down(self.board.copy())
            
            if not np.array_equal(test_board, self.board):
                legal_actions.append(action)
        
        return legal_actions

    def _move_left(self, board):
        new_board = np.zeros_like(board)
        for i, row in enumerate(board):
            merged = []
            last_merged = False
            for tile in row[row != 0]:
                if not merged or last_merged or merged[-1] != tile:
                    merged.append(tile)
                    last_merged = False
                else:
                    merged[-1] += 1 
                    last_merged = True
            new_board[i, :len(merged)] = merged
        return new_board

    def _move_right(self, board):
        return np.flip(self._move_left(np.flip(board, axis=1)), axis=1)

    def _move_up(self, board):
        return self._move_left(board.T).T

    def _move_down(self, board):
        return np.flip(self._move_up(np.flip(board, axis=0)), axis=0)

    def get_max_tile(self):
        return np.max(self.board)

    def render(self):
        print(self.board)

if __name__ == "__main__":
    env = Game2048Env(n=3)
    state = env.reset()
    done = False

    print("Initial state:")
    env.render()
    print()

    actions = ["Left", "Right", "Up", "Down"]
    for step in range(12):  # 3 cycles through all 4 directions
        legal_actions = env.get_legal_actions()
        if not legal_actions:
            print("No legal moves left. Game Over!")
            break

        action = random.choice(legal_actions)
        old_state = state.copy()
        state, done, _ = env.step(action)

        print(f"Step {step + 1}")
        print(f"Legal actions: {[actions[a] for a in legal_actions]}")
        print(f"Chosen action: {actions[action]}")
        print(f"Old state:")
        print(old_state)
        print(f"New state:")
        print(state)
        print()

        if done:
            print("Game Over!")
            break

    if not done:
        print("Simulation completed (12 steps)")