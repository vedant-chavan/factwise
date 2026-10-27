import json

from planner.exceptions import ConflictError, ValidationError
from planner.models import User
from planner.services.helpers import format_time, get_object
from planner.validators import get_id, get_optional_str, get_required_str, parse_request
from user_base import UserBase


class UserService(UserBase):

    def create_user(self, request: str) -> str:
        data = parse_request(request)
        name = get_required_str(data, "name", 64)
        display_name = get_optional_str(data, "display_name", 64)

        if User.objects.filter(name__iexact=name).exists():
            raise ConflictError(f"User name '{name}' is already taken")

        user = User.objects.create(name=name, display_name=display_name)
        return json.dumps({"id": str(user.id)})

    def list_users(self) -> str:
        users = []
        for user in User.objects.all():
            users.append({
                "id": str(user.id),
                "name": user.name,
                "display_name": user.display_name,
                "creation_time": format_time(user.creation_time),
            })
        return json.dumps(users)

    def describe_user(self, request: str) -> str:
        data = parse_request(request)
        user = get_object(User, get_id(data, "id"), "User")

        return json.dumps({
            "id": str(user.id),
            "name": user.name,
            "description": user.display_name,
            "creation_time": format_time(user.creation_time),
        })

    def update_user(self, request: str) -> str:
        data = parse_request(request)
        user = get_object(User, get_id(data, "id"), "User")

        changes = data.get("user")
        if not isinstance(changes, dict):
            raise ValidationError("'user' must be a JSON object")

        if "name" in changes:
            new_name = get_required_str(changes, "name", 64)
            if new_name != user.name:
                raise ValidationError("User name cannot be updated")

        if "display_name" in changes:
            user.display_name = get_optional_str(changes, "display_name", 128)
            user.save()

        return json.dumps({"id": str(user.id)})

    def get_user_teams(self, request: str) -> str:
        data = parse_request(request)
        user = get_object(User, get_id(data, "id"), "User")

        teams = []
        for team in user.teams.all():
            teams.append({
                "id": str(team.id),
                "name": team.name,
                "description": team.description,
                "creation_time": format_time(team.creation_time),
            })
        return json.dumps(teams)
