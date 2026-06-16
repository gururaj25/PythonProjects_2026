from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):

    def on_modified(self, event):
        print(f"Changed: {event.src_path}")

def start_monitoring(path):

    event_handler = ChangeHandler()

    observer = Observer()

    observer.schedule(event_handler, path, recursive=True)

    observer.start()