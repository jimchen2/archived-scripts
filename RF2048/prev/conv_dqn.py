import torch
import torch.nn as nn
import torch.nn.functional as F

class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(ConvBlock, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)
        self.bn = nn.BatchNorm2d(out_channels)

    def forward(self, x):
        return F.leaky_relu(self.bn(self.conv(x)), negative_slope=0.01)

class ConvDQN(nn.Module):
    def __init__(self, output_size, dropout_rate=0.5, col_row_2048=4):
        super(ConvDQN, self).__init__()
        self.output_size = output_size
        self.col_row_2048 = col_row_2048

        self.conv1 = ConvBlock(1, 64)
        self.conv2 = ConvBlock(64, 128)
        self.conv3 = ConvBlock(128, 256)

        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        
        self.fc1 = nn.Linear(256, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, output_size)
        
        self.dropout = nn.Dropout(dropout_rate)

    def forward(self, x):
        x = x.view(-1, 1, self.col_row_2048, self.col_row_2048)
        
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        
        x = F.leaky_relu(self.fc1(x), negative_slope=0.01)
        x = self.dropout(x)
        x = F.leaky_relu(self.fc2(x), negative_slope=0.01)
        x = self.dropout(x)
        x = self.fc3(x)
        
        return x