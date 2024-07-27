import numpy as np
import random
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt
from framework import Game2048Env
from reward_calculator import RewardCalculator
from linear_dqn import DQN
from replay_buffer import ReplayBuffer
from utils import optimize_model, soft_update

# Set random seed for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# Hyperparameters to finetune
BATCH_SIZE = 64
POLICY_UPDATE_FREQUENCY = 20
GAMMA = 0.9
TAU = 0.005

# Fixed Hyperparamters
LEARNING_RATE = 0.001
EPSILON_START = 1.0
EPSILON_END = 0.001
EPSILON_DECAY = 0.99

MEMORY_SIZE = 1000

LOG_STEP = 50
COL_ROW_2048 = 4

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def train_dqn(env, reward_calc, num_episodes):
    policy_net = DQN().to(device)
    target_net = DQN().to(device)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()

    optimizer = optim.Adam(policy_net.parameters(), lr=LEARNING_RATE)
    memory = ReplayBuffer(MEMORY_SIZE)

    epsilon = EPSILON_START
    episode_rewards = []
    episode_max_tiles = []
    episode_steps = []
    total_steps = 0

    for episode in range(num_episodes):
        state = env.reset()
        old_state = state.copy()
        state = state.flatten()
        episode_reward = 0
        done = False
        episode_step = 0

        while not done:
            legal_actions = env.get_legal_actions()
            if not legal_actions:
                break

            if random.random() < epsilon:
                action = random.choice(legal_actions)
            else:
                with torch.no_grad():
                    q_values = policy_net(torch.tensor(state, dtype=torch.float32).unsqueeze(0).to(device))
                    legal_q_values = q_values[0, legal_actions]
                    action = legal_actions[legal_q_values.argmax().item()]

            next_state, done, _ = env.step(action)
            reward = reward_calc.calculate_reward(old_state, next_state)
            old_state = next_state.copy()
            next_state = next_state.flatten()

            episode_reward += reward
            memory.push(state, action, reward, next_state, done)
            state = next_state

            total_steps += 1
            episode_step += 1

            if total_steps % POLICY_UPDATE_FREQUENCY == 0:
                optimize_model(policy_net, target_net, optimizer, memory, BATCH_SIZE, device, GAMMA)
                soft_update(target_net, policy_net, TAU)

        episode_rewards.append(episode_reward)
        episode_max_tiles.append(2 ** env.get_max_tile())        
        episode_steps.append(episode_step)
        epsilon = max(EPSILON_END, epsilon * EPSILON_DECAY)

        if episode % LOG_STEP == 0:
            recent_max_tiles = episode_max_tiles[-LOG_STEP:]
            print(f"Episode {episode}, Avg Reward: {np.mean(episode_rewards[-LOG_STEP:]):.2f}, "
                  f"Max Tile: {max(recent_max_tiles)}, "
                  f"Mean Max Tile: {(np.mean(recent_max_tiles))}, "
                  f"Avg Steps: {np.mean(episode_steps[-LOG_STEP:]):.2f}, "
                  f"Epsilon: {epsilon:.2f}")
            
    return policy_net, episode_rewards, episode_max_tiles, episode_steps

if __name__ == "__main__":
    env = Game2048Env(n=COL_ROW_2048)
    reward_calc = RewardCalculator()
    num_episodes = 100000
    train_dqn(env, reward_calc, num_episodes)