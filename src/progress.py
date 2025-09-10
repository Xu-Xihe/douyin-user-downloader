import rich.progress as pg
from rich.console import Group
from rich.live import Live
import sys

class FakeProgress:
    @staticmethod
    def add_task(*args, **kwargs):
        return None
    @staticmethod
    def update(*args, **kwargs):
        return None

class Progress:
    # Value
    _isatty = False
    _progress_list = [None, None, None]
    _task_id = [None, None, None]
    _live = None

    def stop(self):
        if self._isatty:
            self._live.stop()

    def __new__(cls):
        if sys.stdout.isatty():
            cls._isatty = True
            cls._live = Live(cls._get_group(), refresh_per_second=5, vertical_overflow="visible")
            cls._live.start()
        return super().__new__(cls)

    # Rquest new porgress
    @classmethod
    def new(cls, id: int):
        # TTY Check
        if not cls._isatty:
            return
        
        # Stop progress
        if cls._progress_list[id] is not None:
            cls._progress_list[id].stop()
        
        # User progress
        if id == 0: 
            progress = pg.Progress(
                pg.SpinnerColumn(spinner_name="simpleDotsScrolling", finished_text="[green]✔"),
                "[purple]Downloading user [white]{task.description}",
                pg.BarColumn(),
                "[bold green]{task.completed}/{task.total}",
                pg.TimeElapsedColumn(),
                "{task.fields[status]}",
                transient=False
            )
            cls._progress_list[0] = progress
        # Post progress
        if id == 1: 
            progress = pg.Progress(
                "    ",
                pg.SpinnerColumn(spinner_name="line", finished_text="✅"),
                "[cyan]Downloading post [white]{task.description}",
                pg.BarColumn(),
                "[bold green]{task.completed}/{task.total}",
                pg.TimeElapsedColumn(),
                "{task.fields[status]}",
                transient=False
            )
            cls._progress_list[1] = progress
        # Download progress
        if id == 2:
            progress = pg.Progress(
                pg.SpinnerColumn(spinner_name="dots", finished_text=""),
                "[yellow]{task.description}",
                pg.BarColumn(),
                "[progress.percentage]{task.percentage:>3.2f}%",
                pg.DownloadColumn(),
                pg.TransferSpeedColumn(),
                pg.TimeRemainingColumn(),
                transient=True
            )
            cls._progress_list[2] = progress

        # End exe
        progress.add_task("", total=1, visible=False)
        cls.update()
    
    # Progress execute
    @classmethod
    def execute(cls, id: int) -> pg.Progress:
        if cls._isatty:
            return cls._progress_list[id]
        else:
            return FakeProgress
    
    @classmethod
    def update(cls):
        if cls._isatty:
            cls._live.update(cls._get_group())
    
    @classmethod
    def _get_group(cls) -> Group:
        return Group(*[p for p in cls._progress_list if p is not None])