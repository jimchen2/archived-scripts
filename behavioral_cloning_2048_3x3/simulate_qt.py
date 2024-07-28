import sys
import numpy as np
import json
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QLabel, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QKeyEvent
from framework import Game2048Env

class Game2048GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.n = 3
        self.initUI()
        self.new_game()

    def initUI(self):
        self.setWindowTitle('2048 Game')
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

    def new_game(self):
        self.env = Game2048Env(self.n)
        self.state = self.env.reset()
        self.game_data = []
        self.move_count = 0
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key in (Qt.Key_Left, Qt.Key_A):
            action = 0  # Left
        elif key in (Qt.Key_Right, Qt.Key_D):
            action = 1  # Right
        elif key in (Qt.Key_Up, Qt.Key_W):
            action = 2  # Up
        elif key in (Qt.Key_Down, Qt.Key_S):
            action = 3  # Down
        else:
            return

        if action in self.env.get_legal_actions():
            self.log_state_action(self.state, action)
            new_state, done, _ = self.env.step(action)
            self.state = np.array(new_state)
            self.update_board()
            self.move_count += 1
            self.save_log()

            if done:
                print("Game Over!")

    def log_state_action(self, state, action):
        self.game_data.append({
            "move": self.move_count,
            "state": state.tolist(),
            "action": int(action)
        })

    def save_log(self):
        filename = f"game_log_{self.timestamp}.json"
        with open(filename, "w") as log_file:
            json.dump(self.game_data, log_file, indent=2)

    def closeEvent(self, event):
        self.save_log()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = Game2048GUI()
    game.show()
    sys.exit(app.exec_())