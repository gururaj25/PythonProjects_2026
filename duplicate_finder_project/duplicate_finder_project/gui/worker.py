from PySide6.QtCore import QObject, Signal

from scanner.file_scanner import scan_directories
from scanner.duplicate_detector import find_duplicates

class ScanWorker(QObject):

    finished = Signal(list)

    def run(self, paths):

        files = scan_directories(paths)
        duplicates = find_duplicates(files)

        self.finished.emit(duplicates)