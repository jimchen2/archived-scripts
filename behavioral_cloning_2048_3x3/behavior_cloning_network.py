# model.py
import torch
import torch.nn as nn
import math

class BehaviorNetwork(nn.Module):
    def __init__(self, input_size, hidden_size1=512, hidden_size2=256, output_size=4):
        super(BehaviorNetwork, self).__init__()
        
        self.input_size = input_size
        self.side_length = int(math.sqrt(input_size))

        # Original path
        self.fc1_original = nn.Linear(input_size, hidden_size1)
        
        # 2x1 CNN path
        self.conv2x1 = nn.Conv2d(1, 16, kernel_size=(2, 1), stride=1, padding=0)
        self.fc1_2x1 = nn.Linear(16 * (self.side_length - 1) * self.side_length, hidden_size1)
        
        # 1x2 CNN path
        self.conv1x2 = nn.Conv2d(1, 16, kernel_size=(1, 2), stride=1, padding=0)
        self.fc1_1x2 = nn.Linear(16 * self.side_length * (self.side_length - 1), hidden_size1)

        # 2x2 CNN path
        self.conv2x2 = nn.Conv2d(1, 16, kernel_size=(2, 2), stride=1, padding=0)
        self.fc1_2x2 = nn.Linear(16 * (self.side_length - 1) * (self.side_length - 1), hidden_size1)

        # Combine paths
        self.fc2 = nn.Linear(hidden_size1 * 4, hidden_size2)
        self.fc3 = nn.Linear(hidden_size2, output_size)
        
        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x):
        # Original path
        x_original = self.relu(self.fc1_original(x))
        
        # Reshape input for CNN paths
        x_cnn = x.view(-1, 1, self.side_length, self.side_length)
        
        # 2x1 CNN path
        x_2x1 = self.relu(self.conv2x1(x_cnn))
        x_2x1 = x_2x1.view(x_2x1.size(0), -1)
        x_2x1 = self.relu(self.fc1_2x1(x_2x1))
        
        # 1x2 CNN path
        x_1x2 = self.relu(self.conv1x2(x_cnn))
        x_1x2 = x_1x2.view(x_1x2.size(0), -1)
        x_1x2 = self.relu(self.fc1_1x2(x_1x2))
        
        # 2x2 CNN path
        x_2x2 = self.relu(self.conv2x2(x_cnn))
        x_2x2 = x_2x2.view(x_2x2.size(0), -1)
        x_2x2 = self.relu(self.fc1_2x2(x_2x2))
        
        # Combine paths
        x_combined = torch.cat((x_original, x_2x1, x_1x2, x_2x2), dim=1)
        
        x = self.relu(self.fc2(x_combined))
        x = self.fc3(x)
        return self.softmax(x)