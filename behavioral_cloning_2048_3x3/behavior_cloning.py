import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import json
import os
from behavior_cloning_network import BehaviorNetwork
from evaluate_behavioral_cloning_model import evaluate_model

def rotate_90_degrees(state, action):
    rotated_state = np.rot90(state.reshape(3, 3), k=-1)
    action_map = {0: 2, 1: 3, 2: 1, 3: 0}
    rotated_action = action_map[action]
    return rotated_state.flatten(), rotated_action

def reflect_horizontal(state, action):
    reflected_state = np.fliplr(state.reshape(3, 3))
    action_map = {0: 1, 1: 0, 2: 2, 3: 3}
    reflected_action = action_map[action]
    return reflected_state.flatten(), reflected_action

def load_and_preprocess_data(directory):
    all_states = []
    all_actions = []

    for filename in os.listdir(directory):
        if filename.startswith('game_log_') and filename.endswith('.json'):
            with open(os.path.join(directory, filename), 'r') as f:
                game_data = json.load(f)
 
            final_state = np.array(game_data[-1]['state'])
            # if np.max(final_state) < 8:  # 2^8 = 256, bad game
            #     continue
            for move in game_data[30:]:
                state = np.array(move['state'])
                action = move['action']

                current_state, current_action = state.flatten(), action
                for _ in range(4):
                    all_states.append(current_state)
                    all_actions.append(current_action)
                    current_state, current_action = rotate_90_degrees(current_state, current_action)

                reflected_state, reflected_action = reflect_horizontal(state, action)
                current_state, current_action = reflected_state, reflected_action
                for _ in range(4):
                    all_states.append(current_state)
                    all_actions.append(current_action)
                    current_state, current_action = rotate_90_degrees(current_state, current_action)

    return np.array(all_states), np.array(all_actions)
 
def train_model(model, states, actions, epochs=20, batch_size=32):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters())

    best_model_path = 'simple_bc_best_model.pth'
    best_performance = 0

    for epoch in range(epochs):
        indices = np.arange(len(states))
        np.random.shuffle(indices)
        states = states[indices]
        actions = actions[indices]

        total_loss = 0
        for i in range(0, len(states), batch_size):
            batch_states = torch.FloatTensor(states[i:i+batch_size])
            batch_actions = torch.LongTensor(actions[i:i+batch_size])

            optimizer.zero_grad()
            outputs = model(batch_states)
            loss = criterion(outputs, batch_actions)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        if (epoch) % 1 == 0:
            avg_loss = total_loss / (len(states) // batch_size)
            print(f"Epoch {epoch}, Average Loss: {avg_loss}")
            avg_steps, avg_max_tile, max_tile_reached = evaluate_model(model)
            
            # Use avg_max_tile as the performance metric
            current_performance = avg_max_tile

            # If this is the best model so far, save it
            if current_performance > best_performance:
                best_performance = current_performance
                torch.save(model.state_dict(), best_model_path)

if __name__ == '__main__':
    input_size = 9  # 3x3 grid flattened
    output_size = 4  # 4 possible actions

    # Load and preprocess data
    states, actions = load_and_preprocess_data('expert_3x3/')

    # Create the model
    model = BehaviorNetwork(input_size=input_size, output_size=output_size)

    # Train the model
    train_model(model, states, actions, epochs=100, batch_size=32)
