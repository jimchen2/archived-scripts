import json
import os
import numpy as np
from collections import defaultdict, Counter

def analyze_game_log(file_path):
    with open(file_path, 'r') as f:
        game_data = json.load(f)
    
    final_state = np.array(game_data[-1]['state'])
    max_tile = 2 ** np.max(final_state)
    num_moves = len(game_data)
    final_score = np.sum(2 ** final_state[final_state > 0])
    
    return max_tile, num_moves, final_score

def analyze_expert_performance(log_directory):
    performance_data = defaultdict(list)
    
    for filename in os.listdir(log_directory):
        if filename.startswith('game_log_') and filename.endswith('.json'):
            file_path = os.path.join(log_directory, filename)
            max_tile, num_moves, final_score = analyze_game_log(file_path)
            
            performance_data['max_tile'].append(max_tile)
            performance_data['num_moves'].append(num_moves)
            performance_data['final_score'].append(final_score)
    
    return performance_data

# Analyze the expert's performance
log_directory = 'expert_3x3/'
performance_data = analyze_expert_performance(log_directory)

# Calculate summary statistics
num_games = len(performance_data['max_tile'])
avg_max_tile = np.mean(performance_data['max_tile'])
max_max_tile = np.max(performance_data['max_tile'])
min_max_tile = np.min(performance_data['max_tile'])
avg_moves = np.mean(performance_data['num_moves'])
avg_score = np.mean(performance_data['final_score'])

# Count occurrences of each max tile
max_tile_counts = Counter(performance_data['max_tile'])

# Print the results
print(f"Number of games analyzed: {num_games}")
print(f"Average max tile: {avg_max_tile:.2f}")
print(f"Highest max tile: {max_max_tile}")
print(f"Lowest max tile: {min_max_tile}")
print(f"Average number of moves: {avg_moves:.2f}")
print(f"Average final score: {avg_score:.2f}")

print("\nMax tile distribution:")
for tile, count in sorted(max_tile_counts.items()):
    print(f"  {tile}: {count} times ({count/num_games*100:.2f}%)")