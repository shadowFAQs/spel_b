import sys
from pathlib import Path

from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QFont, QFontMetrics, QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout
)


# GLOBALS
DICTIONARY = None


class ScrollLabel(QScrollArea):

    def __init__(self, label: QLabel) -> None:
        super().__init__()

        self.textArea = label

        self.textArea.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.textArea.setWordWrap(True)

        self.setWidgetResizable(True)
        self.setWidget(self.textArea)
        layout = QVBoxLayout()
        layout.addWidget(self.textArea)

    def setText(self, text: str) -> None:
        self.textArea.setText(text)


class InputBox(QLineEdit):

    def __init__(self, puzzle_pos: int, parent=None) -> None:
        super().__init__()

        self.puzzle_pos = puzzle_pos
        self.font = QFont('monospace')
        self.font.setPointSize(36)
        self.setFont(self.font)
        self.setMaxLength(1)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setPlaceholderText('?')
        self.setFixedWidth(self.fontMetrics().averageCharWidth() * 2)
        self.textChanged.connect(self.check_select_next_box)

        if self.puzzle_pos == 3:
            self.setStyleSheet("background: #f7da21;")
        else:
            self.setStyleSheet("background: #e6e6e6;")

    def check_select_next_box(self) -> None:
        '''
        Instructs parent's parent (Window) to advance to the next input
        box if the user types a character, but not if they delete one.
        The call to blockSignals prevents setText() from emitting
        another "textChanged" event.
        '''
        if self.text():
            self.blockSignals(True)
            self.setText(self.text().upper())
            self.blockSignals(False)
            self.parent().parent().select_next_box()

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        self.selectAll()


class Window(QDialog):

    def __init__(self) -> None:
        super().__init__(parent=None)

        self.setWindowTitle('Spel B')
        self.setGeometry(400, 400, 450, 300)  # Left, top, w, h
        self.setFixedSize(450, 300)
        self.input_boxes = []

        regex = QRegularExpression("[a-zA-Z]")  # Only accept alpha chars
        self.validator = QRegularExpressionValidator(regex)

        main_layout = QVBoxLayout()

        letters = QGroupBox('Add letters')
        col0 = QVBoxLayout()
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        for pos in range(7):
            box = InputBox(pos)
            box.setValidator(self.validator)

            if box.puzzle_pos < 2:
                col0.addWidget(box)
            elif box.puzzle_pos < 5:
                col1.addWidget(box)
            else:
                col2.addWidget(box)

            self.input_boxes.append(box)

        columns = QHBoxLayout()
        columns.addLayout(col0)
        columns.addLayout(col1)
        columns.addLayout(col2)

        letters.setLayout(columns)
        container = QGridLayout()
        container.setColumnStretch(0, 1)
        container.setColumnStretch(1, 1)
        container.setRowStretch(0, 1)
        container.setRowStretch(1, 1)
        container.addWidget(letters, 0, 0)

        word_list = QGroupBox('Solutions')
        solutions = QLabel()
        self.solutions = ScrollLabel(solutions)
        self.solutions.setStyleSheet('padding: 2px;')
        solutions_layout = QVBoxLayout()
        solutions_layout.addWidget(self.solutions)
        word_list.setLayout(solutions_layout)
        container.addWidget(word_list, 0, 1)

        self.btn_go = QPushButton()
        container.addWidget(self.btn_go, 1, 0)

        main_layout.addLayout(container)

        self.setLayout(main_layout)

        self.clear()

    def clear(self) -> None:
        for box in self.input_boxes:
            box.setText('')

        self.solutions.setText(
            'Enter Spelling Bee letters and click "Bee up your life"')
        self.btn_go.setText('Bee up your life')

        try:
            self.btn_go.clicked.disconnect(self.clear)
        except TypeError:  # Button will not be connected to anything
            pass           # at load time
        self.btn_go.clicked.connect(self.submit_letters)

        self.input_boxes[0].setFocus()

    def get_empty_input_boxes(self) -> list[InputBox]:
        return [i for i in self.input_boxes if not i.text()]

    def get_letter_at_pos(self, pos: str) -> str:
        for box in self.input_boxes:
            if box.puzzle_pos == pos:
                return box.text()
        return ''

    def select_next_box(self) -> None:
        if not self.get_empty_input_boxes():
            self.btn_go.setFocus()
        else:
            self.focusNextChild()

            if isinstance(self.focusWidget(), ScrollLabel):
                self.focusNextChild()

            if self.btn_go.hasFocus() and \
                any([not i.text() for i in self.input_boxes]):
                self.get_empty_input_boxes()[0].setFocus()

    def submit_letters(self) -> None:
        if self.get_empty_input_boxes():
            self.get_empty_input_boxes()[0].setFocus()
            return

        letters = [self.get_letter_at_pos(n).lower() for n in range(7)]
        required_letter = letters[3]
        words = search_dictionary(letters, required_letter)
        if words:
            text = f'Found {len(words)} words:\n\n'
            self.solutions.setText(text + '\n'.join(words))
        else:
            self.solutions.setText('No words found for the letters provided')

        self.btn_go.clicked.disconnect(self.submit_letters)
        self.btn_go.clicked.connect(self.clear)
        self.btn_go.setText('Clear')


def load_dictionary() -> None:
    global DICTIONARY

    filepath = Path(__file__).parent / 'dictionary.txt'

    with open(filepath) as file:
        DICTIONARY = file.read().split('\n')


def search_dictionary(letters: list[str], required_letter: str) -> list[str]:
    words = [w for w in DICTIONARY if required_letter in w]
    return [w for w in words if all([l in letters for l in w])]


if __name__ == '__main__':
    app = QApplication([])
    load_dictionary()
    window = Window()
    window.show()
    sys.exit(app.exec())
