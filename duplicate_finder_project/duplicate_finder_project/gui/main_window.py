from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
    QTextEdit,
    QLabel
)

from reports.report_generator import generate_reports
from scanner.file_scanner import scan_directories
from scanner.duplicate_detector import find_duplicates

class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Duplicate Project Finder")
        self.resize(900, 600)

        self.layout = QVBoxLayout()

        self.label = QLabel("Select folders to scan")

        self.scan_btn = QPushButton("Scan")
        self.scan_btn.clicked.connect(self.select_folder)

        self.output = QTextEdit()

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.scan_btn)
        self.layout.addWidget(self.output)

        self.setLayout(self.layout)

    def select_folder(self):

        folder = QFileDialog.getExistingDirectory(self)

        if not folder:
            return

        self.output.append(f"Scanning: {folder}")

        files = scan_directories([folder])
        duplicates = find_duplicates(files)

        generate_reports(duplicates)

        for group in duplicates:

            self.output.append("\n====================")

            for file in group["files"]:
                self.output.append(file["path"])

        self.output.append("\nReports generated.")