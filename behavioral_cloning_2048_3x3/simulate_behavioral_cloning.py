import torch
import numpy as np
from behavior_cloning_network import BehaviorNetwork
from framework import Game2048Env
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QLabel, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import sys

class SimulatedGame2048GUI(QMainWindow):
    def __init__(self, model):
        super().__init__()
        self.n = 3
        self.model = model
        self.initUI()
        self.new_game()

    def initUI(self):
        self.setWindowTitle('2048 Game Simulation')
        self.setGeometry(300, 300, 400, 450)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        self.grid_layout = QGridLayout()
        main_layout.addLayout(self.grid_layout)

        self.labels = []
        for i in range(self.n):
            row = []
            for j in range(self.n):
                label = QLabel('', self)
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("background-color: #cdc1b4; border: 2px solid #bbada0; font-size: 24px; font-weight: bold;")
                label.setFixedSize(80, 80)
                self.grid_layout.addWidget(label, i, j)
                row.append(label)
            self.labels.append(row)

        self.new_game_button = QPushButton("New Game", self)
        self.new_game_button.clicked.connect(self.new_game)
        main_layout.addWidget(self.new_game_button)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.make_move)
        self.timer.start(200) 
        
    def new_game(self):
        self.env = Game2048Env(self.n)
        self.state = self.env.reset()
        self.update_board()

    def update_board(self):
        for i in range(self.n):
            for j in range(self.n):
                value = self.state[i, j]
                self.labels[i][j].setText(str(2 ** value) if value > 0 else '')
                self.labels[i][j].setStyleSheet(self.get_color_style(value))

    def get_color_style(self, value):
        colors = {
            0: "#cdc1b4", 1: "#eee4da", 2: "#ede0c8", 3: "#f2b179",
            4: "#f59563", 5: "#f67c5f", 6: "#f65e3b", 7: "#edcf72",
            8: "#edcc61", 9: "#edc850", 10: "#edc53f", 11: "#edc22e"
        }
        color = colors.get(value, "#3c3a32")
        return f"background-color: {color}; color: {'#776e65' if value < 3 else '#f9f6f2'}; border: 2px solid #bbada0; font-size: 24px; font-weight: bold;"

    def make_move(self):
        state_tensor = torch.FloatTensor(self.state.flatten()).unsqueeze(0)
        with torch.no_grad():
            action_probs = self.model(state_tensor)
        
        legal_moves = self.env.get_legal_actions()
        legal_action_probs = action_probs[0][legal_moves]
        action = legal_moves[torch.argmax(legal_action_probs).item()]

        self.state, done, _ = self.env.step(action)
        self.update_board()

        if done:
            print("Game Over!")
            self.timer.stop()

def load_best_model():
    input_size = 9  # 3x3 grid flattened
    output_size = 4  # 4 possible actions
    model = BehaviorNetwork(input_size=input_size, output_size=output_size)
    model.load_state_dict(torch.load('simple_bc_best_model_batch_32.pth'))
    model.eval()
    return model

if __name__ == '__main__':
    best_model = load_best_model()
    app = QApplication(sys.argv)
    game = SimulatedGame2048GUI(best_model)
    game.show()
    sys.exit(app.exec_())