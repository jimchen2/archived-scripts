import numpy as np
from framework import Game2048Env

class SmartAI:
    def __init__(self, game):
        self.game = game

    def next_move(self):
        original_quality = self.grid_quality(self.game.board)
        results = self.plan_ahead(self.game.board, 3, original_quality)
        best_result = self.choose_best_move(results, original_quality)
        return best_result['direction']

    def plan_ahead(self, grid, num_moves, original_quality):
        results = [None] * 4

        for d in range(4):
            test_env = Game2048Env(n=self.game.n)
            test_env.board = grid.copy()
            
            old_board = test_env.board.copy()
            test_env.step(d)
            if np.array_equal(old_board, test_env.board):
                results[d] = None
                continue

            result = {
                'quality': -1,
                'probability': 1,
                'quality_loss': 0,
                'direction': d
            }

            available_cells = np.argwhere(test_env.board == 0)
            for cell in available_cells:
                # Check if the cell has an adjacent tile
                has_adjacent_tile = False
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    adj_x, adj_y = cell[0] + dx, cell[1] + dy
                    if 0 <= adj_x < self.game.n and 0 <= adj_y < self.game.n:
                        if test_env.board[adj_x, adj_y] != 0:
                            has_adjacent_tile = True
                            break
                if not has_adjacent_tile:
                    continue

                test_env2 = Game2048Env(n=self.game.n)
                test_env2.board = test_env.board.copy()
                test_env2.board[cell[0], cell[1]] = 1  # Assume 1 (2^1 = 2) is added

                if num_moves > 1:
                    sub_results = self.plan_ahead(test_env2.board, num_moves - 1, original_quality)
                    tile_result = self.choose_best_move(sub_results, original_quality)
                else:
                    tile_quality = self.grid_quality(test_env2.board)
                    tile_result = {
                        'quality': tile_quality,
                        'probability': 1,
                        'quality_loss': max(original_quality - tile_quality, 0)
                    }

                if result['quality'] == -1 or tile_result['quality'] < result['quality']:
                    result['quality'] = tile_result['quality']
                    result['probability'] = tile_result['probability'] / len(available_cells)
                elif tile_result['quality'] == result['quality']:
                    result['probability'] += tile_result['probability'] / len(available_cells)

                result['quality_loss'] += tile_result['quality_loss'] / len(available_cells)

            results[d] = result

        return results

    def choose_best_move(self, results, original_quality):
        best_result = None
        for result in results:
            if result is None:
                continue
            if (best_result is None or
                result['quality_loss'] < best_result['quality_loss'] or
                (result['quality_loss'] == best_result['quality_loss'] and result['quality'] > best_result['quality']) or
                (result['quality_loss'] == best_result['quality_loss'] and result['quality'] == best_result['quality'] and result['probability'] < best_result['probability'])):
                best_result = result

        if best_result is None:
            best_result = {
                'quality': -1,
                'probability': 1,
                'quality_loss': original_quality,
                'direction': 0
            }

        return best_result

    def grid_quality(self, grid):
        mono_score = 0
        empty_cell_weight = 8

        for i in range(self.game.n):
            row_inc, row_dec = self.monotonicity_score(grid[i])
            col_inc, col_dec = self.monotonicity_score(grid[:, i])
            mono_score += max(row_inc, row_dec) + max(col_inc, col_dec)

        empty_score = np.count_nonzero(grid == 0) * empty_cell_weight
        return mono_score + empty_score

    def monotonicity_score(self, array):
        inc_score = dec_score = 0
        prev_value = -1

        for value in array:
            if value == 0:
                value = 1  # Treat empty cells as having a value of 1
            inc_score += value
            if value <= prev_value or prev_value == -1:
                dec_score += value
                if value < prev_value:
                    inc_score -= prev_value
            prev_value = value

        return inc_score, dec_score

# Example usage
if __name__ == "__main__":
    env = Game2048Env(n=3)
    state = env.reset()
    ai = SmartAI(env)
    done = False

    print("Initial state:")
    env.render()
    print()

    actions = ["Left", "Right", "Up", "Down"]
    step = 0
    while not done:
        action = ai.next_move()
        old_state = state.copy()
        state, done, _ = env.step(action)

        step += 1
        print(f"Step {step}")
        print(f"Chosen action: {actions[action]}")
        print(f"Old state:")
        print(old_state)
        print(f"New state:")
        print(state)
        print(f"Max tile: {env.get_max_tile()}")
        print()

        if step >= 100:
            print("Simulation stopped after 100 steps")
            break

    print("Game Over!")
    print(f"Final max tile: {env.get_max_tile()}")