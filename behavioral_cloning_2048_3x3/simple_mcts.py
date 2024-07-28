import math
import copy
from framework import Game2048Env
import random
import numpy as np 

class MCTSNode:
    def __init__(self, state, parent=None, action=None):
        self.state = state
        self.parent = parent
        self.action = action
        self.children = []
        self.visits = 0
        self.value = 0

    def is_fully_expanded(self):
        return len(self.children) == len(Game2048Env(n=3).get_legal_actions())

    def best_child(self, c_param=1.4):
        choices_weights = [
            (c.value / c.visits) + c_param * math.sqrt((2 * math.log(self.visits) / c.visits))
            for c in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]

    def rollout(self):
        env = Game2048Env(n=3)
        env.board = self.state.copy()
        done = False
        while not done:
            actions = env.get_legal_actions()
            if not actions:
                break
            action = random.choice(actions)
            _, done, _ = env.step(action)
        return np.max(env.board)

    def backpropagate(self, result):
        self.visits += 1
        self.value += result
        if self.parent:
            self.parent.backpropagate(result)

def mcts(root_state, num_iterations=1000, exploration_weight=1.4):
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
                unvisited_actions = [a for a in actions if a not in [c.action for c in node.children]]
                if unvisited_actions:
                    action = random.choice(unvisited_actions)
                    env.step(action)
                    child = MCTSNode(env.board.copy(), parent=node, action=action)
                    node.children.append(child)
                    node = child
            else:
                node = random.choice(node.children)
        
        # Simulation
        result = node.rollout()

        # Backpropagation
        node.backpropagate(result)

    return max(root.children, key=lambda c: c.visits).action if root.children else random.choice(env.get_legal_actions())

# Example usage
if __name__ == "__main__":
    env = Game2048Env(n=3)
    state = env.reset()
    done = False

    print("Initial state:")
    env.render()
    print()

    actions = ["Left", "Right", "Up", "Down"]
    while not done:
        action = mcts(state)
        state, done, _ = env.step(action)

        print(f"Chosen action: {actions[action]}")
        print(f"New state:")
        env.render()
        print(f"Max tile: {env.get_max_tile()}")
        print()

    print("Game Over!")
    print(f"Final max tile: {env.get_max_tile()}")