import torch
import numpy as np
import json
from framework import Game2048Env
from behavior_cloning_network import BehaviorNetwork
from datetime import datetime

def evaluate_model(model, num_games=500):
    env = Game2048Env(n=3)
    total_steps = 0
    max_tiles = []

    for game in range(num_games):
        state = env.reset()
        done = False
        steps = 0
        game_log = []

        while not done:
            state_tensor = torch.FloatTensor(state.flatten()).unsqueeze(0)
            with torch.no_grad():
                action_probs = model(state_tensor)
            
            legal_moves = env.get_legal_actions()
            legal_action_probs = action_probs[0][legal_moves]
            action = legal_moves[torch.argmax(legal_action_probs).item()]

            # Log the current state and action
            game_log.append({
                "move": steps,
                "state": state.tolist(),
                "action": action
            })

            state, done, _ = env.step(action)
            steps += 1

        total_steps += steps
        max_tile = 2**np.max(state)
        max_tiles.append(max_tile)


    avg_steps = total_steps / num_games
    avg_max_tile = sum(max_tiles) / num_games
    max_tile_reached = max(max_tiles)

    print(f"Evaluation Results:")
    print(f"Average Steps: {avg_steps:.2f}")
    print(f"Average Max Tile: {avg_max_tile:.2f}")
    print(f"Max Tile Reached: {max_tile_reached}")

    return avg_steps, avg_max_tile, max_tile_reached