import json

from django.db import transaction

from planner.exceptions import ConflictError, InvalidStateError, NotFoundError, ValidationError
from planner.models import Team, User
from planner.services.helpers import format_time, get_object
from planner.validators import get_id, get_id_list, get_optional_str, get_required_str, parse_request
from team_base import TeamBase

MAX_TEAM_USERS = 50


class TeamService(TeamBase):

    def create_team(self, request: str) -> str:
        data = parse_request(request)
        name = get_required_str(data, "name", 64)
        description = get_optional_str(data, "description", 128)
        admin = get_object(User, get_id(data, "admin"), "User")

        if Team.objects.filter(name__iexact=name).exists():
            raise ConflictError(f"Team name '{name}' is already taken")

        with transaction.atomic():
            team = Team.objects.create(name=name, description=description, admin=admin)
            team.members.add(admin)
        return json.dumps({"id": str(team.id)})

    def list_teams(self) -> str:
        teams = [self._team_to_dict(team) for team in Team.objects.all()]
        return json.dumps(teams)

    def describe_team(self, request: str) -> str:
        data = parse_request(request)
        team = get_object(Team, get_id(data, "id"), "Team")
        return json.dumps(self._team_to_dict(team))

    def update_team(self, request: str) -> str:
        data = parse_request(request)
        team = get_object(Team, get_id(data, "id"), "Team")

        changes = data.get("team")
        if not isinstance(changes, dict) or len(changes) == 0:
            raise ValidationError("'team' must be a JSON object with at least one field")

        if "name" in changes:
            new_name = get_required_str(changes, "name", 64)
            if Team.objects.filter(name__iexact=new_name).exclude(id=team.id).exists():
                raise ConflictError(f"Team name '{new_name}' is already taken")
            team.name = new_name

        if "description" in changes:
            team.description = get_optional_str(changes, "description", 128)

        with transaction.atomic():
            if "admin" in changes:
                new_admin = get_object(User, get_id(changes, "admin"), "User")
                if not team.members.filter(id=new_admin.id).exists():
                    self._check_team_size(team, 1)
                    team.members.add(new_admin)
                team.admin = new_admin
            team.save()

        return json.dumps({"id": str(team.id)})

    def add_users_to_team(self, request: str):
        data = parse_request(request)
        team = get_object(Team, get_id(data, "id"), "Team")
        users = self._get_users(data)

        member_ids = set(team.members.values_list("id", flat=True))
        new_users = [user for user in users if user.id not in member_ids]
        self._check_team_size(team, len(new_users))

        team.members.add(*new_users)
        return json.dumps({"id": str(team.id)})

    def remove_users_from_team(self, request: str):
        data = parse_request(request)
        team = get_object(Team, get_id(data, "id"), "Team")
        users = self._get_users(data)

        for user in users:
            if user.id == team.admin_id:
                raise InvalidStateError("The team admin cannot be removed from the team")

        team.members.remove(*users)
        return json.dumps({"id": str(team.id)})

    def list_team_users(self, request: str):
        data = parse_request(request)
        team = get_object(Team, get_id(data, "id"), "Team")

        users = []
        for user in team.members.all():
            users.append({
                "id": str(user.id),
                "name": user.name,
                "display_name": user.display_name,
            })
        return json.dumps(users)

    # ----- helper methods (used only inside this class) -----

    def _team_to_dict(self, team):
        return {
            "id": str(team.id),
            "name": team.name,
            "description": team.description,
            "creation_time": format_time(team.creation_time),
            "admin": str(team.admin_id),
        }

    def _get_users(self, data):
        """Read the 'users' id list and load those users. Fails if any id does not exist."""
        user_ids = get_id_list(data, "users", MAX_TEAM_USERS)
        users = list(User.objects.filter(id__in=user_ids))

        found_ids = [user.id for user in users]
        missing = [user_id for user_id in user_ids if user_id not in found_ids]
        if missing:
            raise NotFoundError(f"Users with these ids do not exist: {missing}")
        return users

    def _check_team_size(self, team, adding):
        current = team.members.count()
        if current + adding > MAX_TEAM_USERS:
            raise InvalidStateError(
                f"A team can have at most {MAX_TEAM_USERS} users "
                f"(it has {current}, trying to add {adding})"
            )
