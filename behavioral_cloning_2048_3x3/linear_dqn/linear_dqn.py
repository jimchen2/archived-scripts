import torch.nn as nn

class DQN(nn.Module):
    def __init__(self, COL_ROW_2048=3, hidden_size=128, dropout_rate=0.2):
        super(DQN, self).__init__()
        
        self.input_size = COL_ROW_2048 * COL_ROW_2048
        
        # First layer
        self.layer1 = nn.Linear(self.input_size, hidden_size)
        
        # Dropout layer
        self.dropout = nn.Dropout(dropout_rate)
        
        # Second layer (output layer)
        self.layer2 = nn.Linear(hidden_size, 4)  # 4 possible actions: up, down, left, right
        
        # Activation function
        self.activation = nn.ReLU()

    def forward(self, x):
        # Ensure input is correctly shaped
        x = x.view(-1, self.input_size)
        
        # First layer
        x = self.layer1(x)
        x = self.activation(x)
        
        # Dropout
        x = self.dropout(x)
        
        # Second layer (output layer)
        x = self.layer2(x)
        
        return x