import json

from django.utils import timezone

from planner.exceptions import ConflictError, InvalidStateError, ValidationError
from planner.models import Board, Task, Team, User
from planner.services.board_exporter import export_board_to_file
from planner.services.helpers import get_object
from planner.validators import get_id, get_optional_str, get_required_str, parse_request
from project_board_base import ProjectBoardBase


class ProjectBoardService(ProjectBoardBase):

    def create_board(self, request: str):
        data = parse_request(request)
        name = get_required_str(data, "name", 64)
        description = get_optional_str(data, "description", 128)
        team = get_object(Team, get_id(data, "team_id"), "Team")

        if team.boards.filter(name__iexact=name).exists():
            raise ConflictError(f"Team '{team.name}' already has a board named '{name}'")

        board = Board.objects.create(team=team, name=name, description=description)
        return json.dumps({"id": str(board.id)})

    def close_board(self, request: str) -> str:
        data = parse_request(request)
        board = get_object(Board, get_id(data, "id"), "Board")

        if board.status == Board.CLOSED:
            raise InvalidStateError(f"Board '{board.name}' is already closed")

        unfinished = board.tasks.exclude(status=Task.COMPLETE).count()
        if unfinished > 0:
            raise InvalidStateError(
                f"Board '{board.name}' has {unfinished} task(s) that are not COMPLETE"
            )

        board.status = Board.CLOSED
        board.end_time = timezone.now()
        board.save()
        return json.dumps({"id": str(board.id), "status": board.status})

    def add_task(self, request: str) -> str:
        data = parse_request(request)
        title = get_required_str(data, "title", 64)
        description = get_optional_str(data, "description", 128)
        board = get_object(Board, get_id(data, "board_id"), "Board")
        user = get_object(User, get_id(data, "user_id"), "User")

        if board.status != Board.OPEN:
            raise InvalidStateError(f"Tasks can only be added to an OPEN board; '{board.name}' is closed")

        if not board.team.members.filter(id=user.id).exists():
            raise InvalidStateError(f"User '{user.name}' is not a member of team '{board.team.name}'")

        if board.tasks.filter(title__iexact=title).exists():
            raise ConflictError(f"Board '{board.name}' already has a task titled '{title}'")

        task = Task.objects.create(board=board, user=user, title=title, description=description)
        return json.dumps({"id": str(task.id)})

    def update_task_status(self, request: str):
        data = parse_request(request)
        task = get_object(Task, get_id(data, "id"), "Task")

        allowed = [Task.OPEN, Task.IN_PROGRESS, Task.COMPLETE]
        status = data.get("status")
        if status not in allowed:
            raise ValidationError(f"'status' must be one of: {', '.join(allowed)}")

        if task.board.status == Board.CLOSED:
            raise InvalidStateError(f"Tasks on the closed board '{task.board.name}' cannot be changed")

        task.status = status
        task.save()
        return json.dumps({"id": str(task.id), "status": task.status})

    def list_boards(self, request: str) -> str:
        data = parse_request(request)
        team = get_object(Team, get_id(data, "id"), "Team")

        boards = []
        for board in team.boards.filter(status=Board.OPEN):
            boards.append({"id": str(board.id), "name": board.name})
        return json.dumps(boards)

    def export_board(self, request: str) -> str:
        data = parse_request(request)
        board = get_object(Board, get_id(data, "id"), "Board")

        file_name = export_board_to_file(board)
        return json.dumps({"out_file": file_name})
