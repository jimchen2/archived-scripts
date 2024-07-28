# utils.py

import torch
import torch.nn as nn
import numpy as np

def optimize_model(policy_net, target_net, optimizer, memory, batch_size, device, gamma):
    if len(memory) < batch_size:
        return
    transitions = memory.sample(batch_size)
    batch = list(zip(*transitions))

    state_batch = torch.tensor(np.array(batch[0]), dtype=torch.float32).to(device)
    action_batch = torch.tensor(batch[1], dtype=torch.long).to(device)
    reward_batch = torch.tensor(batch[2], dtype=torch.float32).to(device)
    next_state_batch = torch.tensor(np.array(batch[3]), dtype=torch.float32).to(device)
    done_batch = torch.tensor(batch[4], dtype=torch.float32).to(device)

    q_values = policy_net(state_batch).gather(1, action_batch.unsqueeze(1))
    next_q_values = target_net(next_state_batch).max(1)[0].detach()
    expected_q_values = reward_batch + gamma * next_q_values * (1 - done_batch)

    loss = nn.MSELoss()(q_values, expected_q_values.unsqueeze(1))
    optimizer.zero_grad()
    loss.backward()

    # Add gradient clipping 
    torch.nn.utils.clip_grad_norm_(policy_net.parameters(), max_norm=1.0)

    optimizer.step()

def soft_update(target_net, policy_net, tau):
    for target_param, policy_param in zip(target_net.parameters(), policy_net.parameters()):
        target_param.data.copy_(tau * policy_param.data + (1.0 - tau) * target_param.data)