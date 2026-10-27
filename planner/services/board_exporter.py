from pathlib import Path

from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify

from planner.models import Task

OUT_DIR = Path(settings.BASE_DIR) / "out"
LINE = "=" * 70


def format_date(value):
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M UTC")


def progress_bar(done, total, width=30):
    """Example: [##########....................] 33%"""
    percent = int(done * 100 / total) if total else 0
    filled = int(width * percent / 100)
    return "[" + "#" * filled + "." * (width - filled) + f"] {percent}%"


def build_report(board):
    """Return the whole board as a text report."""
    tasks = list(board.tasks.select_related("user").order_by("id"))
    completed = [task for task in tasks if task.status == Task.COMPLETE]

    lines = [
        LINE,
        f"  PROJECT BOARD : {board.name}",
        f"  STATUS        : {board.status}",
        LINE,
        f"  Team          : {board.team.name}",
        f"  Description   : {board.description or '-'}",
        f"  Created       : {format_date(board.creation_time)}",
        f"  Closed        : {format_date(board.end_time)}",
        f"  Progress      : {progress_bar(len(completed), len(tasks))}  ({len(completed)}/{len(tasks)} tasks done)",
        "",
    ]

    if not tasks:
        lines.append("  No tasks on this board yet.")

    for status, label in Task.STATUS_CHOICES:
        group = [task for task in tasks if task.status == status]
        if not group:
            continue

        lines.append(f"--- {label.upper()} ({len(group)}) ".ljust(70, "-"))
        lines.append(f"  {'#':<4}{'Task':<25}{'Assignee':<15}Description")
        for number, task in enumerate(group, start=1):
            lines.append(f"  {number:<4}{task.title[:24]:<25}{task.user.name[:14]:<15}{task.description or '-'}")
        lines.append("")

    lines.append(LINE)
    lines.append(f"  Exported on {format_date(timezone.now())}")
    return "\n".join(lines) + "\n"


def export_board_to_file(board):
    """Write the report to the out/ folder and return the file name."""
    OUT_DIR.mkdir(exist_ok=True)
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"board_{slugify(board.name) or board.id}_{timestamp}"

    # Two exports in the same second would get the same name, so add a number instead of overwriting.
    path = OUT_DIR / f"{base_name}.txt"
    number = 1
    while path.exists():
        number += 1
        path = OUT_DIR / f"{base_name}_{number}.txt"

    path.write_text(build_report(board), encoding="utf-8")
    return path.name
