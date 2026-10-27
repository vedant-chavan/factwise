# Team Project Planner

A team project planner built with **Django**. It provides APIs to manage **users**, **teams** and **project boards with tasks**.

Every API takes a JSON string as input and returns a JSON string, as defined in the base classes `UserBase`, `TeamBase` and `ProjectBoardBase`. The concrete implementations are `UserService`, `TeamService` and `ProjectBoardService` in `planner/services/`.

## How to run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate            # creates the database in db/
python manage.py test planner       # runs the 23 automated tests
python manage.py runserver          # starts the HTTP API on http://localhost:8000/api/
```

### Using the APIs from Python
```bash
python manage.py shell
```
```python
from planner.services.user_service import UserService
from planner.services.team_service import TeamService
from planner.services.board_service import ProjectBoardService

UserService().create_user('{"name": "alice", "display_name": "Alice"}')   # '{"id": "1"}'
TeamService().create_team('{"name": "core", "description": "Core team", "admin": "1"}')
ProjectBoardService().create_board('{"name": "Sprint 1", "team_id": "1"}')
ProjectBoardService().add_task('{"title": "Build APIs", "board_id": "1", "user_id": "1"}')
ProjectBoardService().export_board('{"id": "1"}')                         # '{"out_file": "board_sprint-1_....txt"}'
```

### Using the APIs over HTTP
The request body is the same JSON string the method takes.
```bash
curl -X POST localhost:8000/api/users/create -d '{"name": "alice", "display_name": "Alice"}'
curl localhost:8000/api/users/list
```

| Users | Teams | Boards and tasks |
|---|---|---|
| `POST /api/users/create` | `POST /api/teams/create` | `POST /api/boards/create` |
| `GET /api/users/list` | `GET /api/teams/list` | `POST /api/boards/close` |
| `POST /api/users/describe` | `POST /api/teams/describe` | `POST /api/boards/list` |
| `POST /api/users/update` | `POST /api/teams/update` | `POST /api/boards/export` |
| `POST /api/users/teams` | `POST /api/teams/add-users` | `POST /api/tasks/add` |
| | `POST /api/teams/remove-users` | `POST /api/tasks/update-status` |
| | `POST /api/teams/users` | |

Errors are returned as `{"error": "<type>", "message": "<details>"}` with these status codes:

| Error | Status | Example |
|---|---|---|
| `ValidationError` | 400 | invalid JSON, missing field, name too long |
| `NotFoundError` | 404 | user id does not exist |
| `ConflictError` | 409 | user name already taken |
| `InvalidStateError` | 422 | closing a board that still has unfinished tasks |

## Project structure

```
planner/
├── models.py              User, Team, Board, Task (database tables)
├── exceptions.py          custom error types
├── validators.py          reusable input checks (JSON, required text, max length, ids)
├── services/
│   ├── user_service.py    UserService(UserBase)
│   ├── team_service.py    TeamService(TeamBase)
│   ├── board_service.py   ProjectBoardService(ProjectBoardBase)
│   ├── board_exporter.py  builds the text report for export_board
│   └── helpers.py         shared helpers (load by id, time format)
├── views.py, urls.py      HTTP layer
└── tests.py               automated tests
```

## Design choices

- **SQLite for storage.** The data is stored in one local file, `db/planner.sqlite3`. I chose SQLite over plain JSON files because it is still local file storage, but it also gives safe writes, unique constraints enforced by the database, and fast lookups without loading all the data on every call. Django supports it out of the box.
- **Business logic in services, not in views.** All rules live in the service classes, which extend the given base classes. The views only pass the JSON string to the service and convert errors to HTTP status codes. So the APIs behave the same whether they are called from Python or over HTTP.
- **Custom exceptions.** Different error types let the caller tell what went wrong, and each type maps to its own HTTP status code.
- **Reusable validators.** Input checks are written once in `validators.py` and used by all 18 APIs, so every API reports bad input the same way.
- **Database constraints as a backup.** Unique names and "unique per team / per board" rules are also declared on the models, so the database rejects duplicates even if a check were missed.
- **Performance.** Membership checks load all ids in one query, the export loads tasks together with their users (`select_related`) to avoid one query per task, and counts use `count()` / `exists()` instead of loading rows.
- **Readable export.** `export_board` writes `out/board_<name>_<timestamp>.txt` with board details, a progress bar and the tasks grouped by status. Each export creates a new file, so older reports are never overwritten.

## Assumptions

1. `add_task` requires a `board_id`. The docstring does not include it, but a task must belong to a board.
2. A task can only be assigned to a user who is a member of the board's team.
3. `describe_user` returns the `display_name` as `description`, because users have no separate description field.
4. List and describe responses also include `id`, so the caller can use it in the next request.
5. APIs whose docstring has no return value return `{"id": "<id>"}` (status updates also return the new `status`).
6. Ids are numbers created by the database and returned as strings. Requests accept both `1` and `"1"`.
7. Names (user, team, board, task title) are unique ignoring upper/lower case, and spaces around them are removed.
8. `display_name` can be up to 64 characters on create and 128 on update, as written in the docstrings. A user's `name` cannot be changed; sending the current name is allowed.
9. The limit of 50 applies to each add/remove request **and** to the total size of a team.
10. The team admin is automatically a member of the team and cannot be removed. A new admin set by `update_team` joins the team.
11. Adding a user who is already a member is ignored. If any user id in the list does not exist, the whole request fails and nothing is changed.
12. `creation_time` sent by the client is ignored; the server records the real time in UTC.
13. A closed board is read-only: tasks cannot be added or change status, and it cannot be closed again. `list_boards` returns only open boards. A board with no tasks can be closed.

## Submission

The zip excludes the virtual environment, the database file and exported reports:
```bash
zip -r factwise-python.zip . -x ".venv/*" ".git/*" "db/*.sqlite3" "out/*.txt" "*__pycache__*"
```
