import torch.nn as nn

class DQN(nn.Module):
    def __init__(self, hidden_size=128, dropout_rate=0.2):
        super(DQN, self).__init__()
        
        # First layer
        self.layer1 = nn.Linear(16, hidden_size)
        
        # Dropout layer
        self.dropout = nn.Dropout(dropout_rate)
        
        # Second layer (output layer)
        self.layer2 = nn.Linear(hidden_size, 4)
        
        # Activation function
        self.activation = nn.ReLU()

    def forward(self, x):
        # First layer
        x = self.layer1(x)
        x = self.activation(x)
        
        # Dropout
        x = self.dropout(x)
        
        # Second layer (output layer)
        x = self.layer2(x)
        
        return x