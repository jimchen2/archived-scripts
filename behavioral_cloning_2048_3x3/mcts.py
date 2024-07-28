import math
import random
import numpy as np
import torch
from framework import Game2048Env
import torch.nn.functional as F
import torch.nn as nn



class PolicyNetwork(nn.Module):
    def __init__(self, input_size, output_size):
        super(PolicyNetwork, self).__init__()
        
        self.conv1x2 = nn.Conv2d(1, 32, (1, 2), padding=(0, 0))
        self.conv2x1 = nn.Conv2d(1, 32, (2, 1), padding=(0, 0))
        self.conv2x2 = nn.Conv2d(1, 32, (2, 2), padding=0)
        
        self.fc1 = nn.Linear(32 * 2 * 2 * 3, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, output_size)

    def forward(self, x):
        x = x.view(-1, 1, 3, 3)
        
        x1 = F.relu(self.conv1x2(x))  # Output: 32 x 3 x 2
        x2 = F.relu(self.conv2x1(x))  # Output: 32 x 2 x 3
        x3 = F.relu(self.conv2x2(x))  # Output: 32 x 2 x 2
        
        # Ensure all tensors have the same spatial dimensions (2x2)
        x1 = x1[:, :, :2, :]
        x2 = x2[:, :, :, :2]
        
        x = torch.cat((x1, x2, x3), dim=1)
        x = x.view(x.size(0), -1)
        
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return F.softmax(self.fc3(x), dim=1)

class ValueNetwork(nn.Module):
    def __init__(self, input_size):
        super(ValueNetwork, self).__init__()
        
        self.conv1x2 = nn.Conv2d(1, 32, (1, 2), padding=(0, 0))
        self.conv2x1 = nn.Conv2d(1, 32, (2, 1), padding=(0, 0))
        self.conv2x2 = nn.Conv2d(1, 32, (2, 2), padding=0)
        
        self.fc1 = nn.Linear(32 * 2 * 2 * 3, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 1)

    def forward(self, x):
        x = x.view(-1, 1, 3, 3)
        
        x1 = F.relu(self.conv1x2(x))  # Output: 32 x 3 x 2
        x2 = F.relu(self.conv2x1(x))  # Output: 32 x 2 x 3
        x3 = F.relu(self.conv2x2(x))  # Output: 32 x 2 x 2
        
        # Ensure all tensors have the same spatial dimensions (2x2)
        x1 = x1[:, :, :2, :]
        x2 = x2[:, :, :, :2]
        
        x = torch.cat((x1, x2, x3), dim=1)
        x = x.view(x.size(0), -1)
        
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return torch.tanh(self.fc3(x))
    
class MCTSNode:
    def __init__(self, state, parent=None, action=None):
        self.state = state
        self.parent = parent
        self.action = action
        self.children = []
        self.visits = 0
        self.value = 0
        self.prior = 0

    def is_fully_expanded(self):
        return len(self.children) == len(Game2048Env(n=3).get_legal_actions())

    def best_child(self, c_param=1.4):
        choices_weights = [
            (c.value / (c.visits + 1)) + c_param * c.prior * math.sqrt(self.visits) / (c.visits + 1)
            for c in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]

    def backpropagate(self, result):
        self.visits += 1
        self.value += result
        if self.parent:
            self.parent.backpropagate(result)

def mcts(root_state, policy_net, value_net, num_iterations=1000, exploration_weight=1.4):
    root = MCTSNode(root_state)
    env = Game2048Env(n=3)

    for _ in range(num_iterations):
        node = root
        env.board = root_state.copy()

        # Selection
        while node.is_fully_expanded() and node.children:
            node = node.best_child(exploration_weight)
            env.step(node.action)

        # Expansion
        actions = env.get_legal_actions()
        
        if actions:
            if not node.is_fully_expanded():
                # Use np.ascontiguousarray to ensure the array is contiguous
                state_tensor = torch.FloatTensor(np.ascontiguousarray(env.board)).unsqueeze(0)
                action_probs = policy_net(state_tensor).detach().numpy().flatten()
                
                unvisited_actions = [a for a in actions if a not in [c.action for c in node.children]]
                if unvisited_actions:
                    action = max(unvisited_actions, key=lambda a: action_probs[a])
                    env.step(action)
                    child = MCTSNode(env.board.copy(), parent=node, action=action)
                    child.prior = action_probs[action]
                    node.children.append(child)
                    node = child
            else:
                node = random.choice(node.children)
        
        # Evaluation
        # Use np.ascontiguousarray here as well
        state_tensor = torch.FloatTensor(np.ascontiguousarray(node.state)).unsqueeze(0)
        value = value_net(state_tensor).item()

        # Backpropagation
        node.backpropagate(value)

    return max(root.children, key=lambda c: c.visits).action if root.children else random.choice(env.get_legal_actions())


def train(num_episodes=10, mcts_iterations=100):
    env = Game2048Env(n=3)
    policy_net = PolicyNetwork(9, 4)
    value_net = ValueNetwork(9)
    optimizer_policy = torch.optim.Adam(policy_net.parameters())
    optimizer_value = torch.optim.Adam(value_net.parameters())
    
    for episode in range(num_episodes):
        state = env.reset()
        done = False
        states, actions, rewards = [], [], []

        while not done:
            action = mcts(state, policy_net, value_net, num_iterations=mcts_iterations)
            next_state, done, _ = env.step(action)
            
            states.append(state)
            actions.append(action)
            rewards.append(np.sum(next_state))  # Use max tile as reward
            
            state = next_state

        # Train policy network
        state_tensors = torch.FloatTensor(np.ascontiguousarray(np.array(states)))
        action_tensors = torch.LongTensor(actions)
        
        action_probs = policy_net(state_tensors)
        loss_policy = torch.nn.CrossEntropyLoss()(action_probs, action_tensors)
        
        optimizer_policy.zero_grad()
        loss_policy.backward()
        optimizer_policy.step()

        # Train value network
        value_preds = value_net(state_tensors).squeeze()
        returns = torch.FloatTensor(rewards)
        loss_value = torch.nn.MSELoss()(value_preds, returns)
        
        optimizer_value.zero_grad()
        loss_value.backward()
        optimizer_value.step()

        if (episode + 1) % 1 == 0:
            print(f"Episode {episode + 1}, Max tile: {env.get_max_tile()}")

    return policy_net, value_net

if __name__ == "__main__":
    policy_net, value_net = train()

    env = Game2048Env(n=3)
    state = env.reset()
    done = False

    print("Initial state:")
    env.render()
    print()

    actions = ["Left", "Right", "Up", "Down"]
    while not done:
        action = mcts(state, policy_net, value_net)
        state, done, _ = env.step(action)

        print(f"Chosen action: {actions[action]}")
        print(f"New state:")
        env.render()
        print(f"Max tile: {env.get_max_tile()}")
        print()

    print("Game Over!")
    print(f"Final max tile: {env.get_max_tile()}")