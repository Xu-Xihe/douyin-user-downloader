from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, DownloadColumn, SpinnerColumn, TimeElapsedColumn, TransferSpeedColumn
from rich.console import Group
from rich.live import Live
from rich.console import Console
import sys
import atexit

console = Console()
atexit.register(console.show_cursor)

_progress_list = [None, None, None]
_live = None
_isatty = False

if sys.stdout.isatty():
    _isatty = True

class pg:
    # Rquest new porgress
    def new(id: int) -> Progress:
        global _live, _progress_list
        # Stop progress
        if _progress_list[id] is not None:
            _progress_list[id].stop()
        
        # User progress
        if id == 0: 
            progress = Progress(
                SpinnerColumn(spinner_name="simpleDotsScrolling", finished_text="[green]✔"),
                "[purple]Downloading user [white]{task.description}",
                BarColumn(),
                "[bold green]{task.completed}/{task.total}",
                TimeElapsedColumn(),
                transient=False
            )
            _progress_list[0] = progress
        # Post progress
        if id == 1: 
            progress = Progress(
                "    ",
                SpinnerColumn(spinner_name="line", finished_text="✅"),
                "[cyan]Downloading post [white]{task.description}",
                BarColumn(),
                "[bold green]{task.completed}/{task.total}",
                TimeElapsedColumn(),
                "{task.fields[status]}",
                transient=False
            )
            _progress_list[1] = progress
        # Download progress
        if id == 2:
            progress = Progress(
                SpinnerColumn(spinner_name="dots", finished_text=""),
                "[yellow]{task.description}",
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.2f}%",
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                transient=True
            )
            _progress_list[2] = progress

        progress.add_task("", total=1, visible=False)
        # Update _live
        if _live is not None:
            _live.update(pg.get_group())
        return progress
    
    # Progress execute
    def execute(id: int) -> Progress:
        global _progress_list
        return _progress_list[id]
    
    def live() -> Live:
        global _live
        if _live is None:
            _live = Live(pg.get_group(), refresh_per_second=5, vertical_overflow="visible")
        return _live
    
    def stop(id: int):
        global _progress_list
        if _progress_list[id] is not None:
            _progress_list[id].stop()

    def isatty():
        global _isatty
        return _isatty
    
    def get_group() -> Group:
        global _progress_list
        return Group(*[p for p in _progress_list if p is not None])