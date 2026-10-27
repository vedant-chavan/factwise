from django.urls import path

from planner.services.board_service import ProjectBoardService
from planner.services.team_service import TeamService
from planner.services.user_service import UserService
from planner.views import api_view

users = UserService()
teams = TeamService()
boards = ProjectBoardService()

urlpatterns = [
    # Users
    path("users/create", api_view(users.create_user)),
    path("users/list", api_view(users.list_users, method="GET")),
    path("users/describe", api_view(users.describe_user)),
    path("users/update", api_view(users.update_user)),
    path("users/teams", api_view(users.get_user_teams)),

    # Teams
    path("teams/create", api_view(teams.create_team)),
    path("teams/list", api_view(teams.list_teams, method="GET")),
    path("teams/describe", api_view(teams.describe_team)),
    path("teams/update", api_view(teams.update_team)),
    path("teams/add-users", api_view(teams.add_users_to_team)),
    path("teams/remove-users", api_view(teams.remove_users_from_team)),
    path("teams/users", api_view(teams.list_team_users)),

    # Boards and tasks
    path("boards/create", api_view(boards.create_board)),
    path("boards/close", api_view(boards.close_board)),
    path("boards/list", api_view(boards.list_boards)),
    path("boards/export", api_view(boards.export_board)),
    path("tasks/add", api_view(boards.add_task)),
    path("tasks/update-status", api_view(boards.update_task_status)),
]
