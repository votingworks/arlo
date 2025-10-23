import os
import time
import subprocess
from typing_extensions import override
from watchdog.observers import Observer
from watchdog.events import DirModifiedEvent, FileModifiedEvent, FileSystemEventHandler
import fnmatch


class RunDevWorkerEventHandler(FileSystemEventHandler):
    def __init__(self, command: list[str], patterns: list[str]):
        super().__init__()
        self.command: list[str] = command
        self.patterns: list[str] = patterns
        self.process: subprocess.Popen[bytes] | None = None
        self.start_process()

    def start_process(self):
        if self.process:
            self.process.terminate()
            _ = self.process.wait()
        print(f"Starting process: {' '.join(self.command)}")
        self.process = subprocess.Popen(self.command)

    @override
    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent):
        if not event.is_directory:
            for pattern in self.patterns:
                if not isinstance(event.src_path, str):
                    raise TypeError(
                        f"event.src_path is not a string: {event.src_path!r}"
                    )
                if fnmatch.fnmatch(event.src_path, pattern):
                    print(f"File changed: {event.src_path}. Restarting process...")
                    self.start_process()
                    break


if __name__ == "__main__":
    command_to_run = ["python", "-m", "server.worker.worker"]
    patterns_to_watch = ["*.py"]
    path_to_watch = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "../server"
    )

    event_handler = RunDevWorkerEventHandler(command_to_run, patterns_to_watch)
    observer = Observer()
    _ = observer.schedule(event_handler, path_to_watch, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
