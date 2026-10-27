import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import Client, TestCase

from planner.exceptions import ConflictError, InvalidStateError, NotFoundError, ValidationError
from planner.models import User
from planner.services.board_service import ProjectBoardService
from planner.services.team_service import TeamService
from planner.services.user_service import UserService


class PlannerTestCase(TestCase):
    """Shared setup: the three services plus small shortcuts to create test data."""

    def setUp(self):
        self.users = UserService()
        self.teams = TeamService()
        self.boards = ProjectBoardService()

    def call(self, method, payload=None):
        """Call an API with a dict (converted to a JSON string) and return the decoded response."""
        if payload is None:
            return json.loads(method())
        return json.loads(method(json.dumps(payload)))

    def create_user(self, name):
        return self.call(self.users.create_user, {"name": name})["id"]

    def create_team(self, name, admin_id):
        return self.call(self.teams.create_team, {"name": name, "admin": admin_id})["id"]

    def create_board(self, name, team_id):
        return self.call(self.boards.create_board, {"name": name, "team_id": team_id})["id"]

    def add_task(self, title, board_id, user_id):
        return self.call(self.boards.add_task, {"title": title, "board_id": board_id, "user_id": user_id})["id"]


class UserServiceTests(PlannerTestCase):

    def test_create_and_describe_user(self):
        user_id = self.call(self.users.create_user, {"name": "alice", "display_name": "Alice"})["id"]
        user = self.call(self.users.describe_user, {"id": user_id})
        self.assertEqual(user["name"], "alice")
        self.assertEqual(user["description"], "Alice")

    def test_user_name_must_be_unique(self):
        self.create_user("alice")
        with self.assertRaises(ConflictError):
            self.create_user("ALICE")

    def test_name_length_limit(self):
        with self.assertRaises(ValidationError):
            self.create_user("a" * 65)

    def test_invalid_json(self):
        with self.assertRaises(ValidationError):
            self.users.create_user("{not json")

    def test_describe_unknown_user(self):
        with self.assertRaises(NotFoundError):
            self.call(self.users.describe_user, {"id": 999})

    def test_user_name_cannot_be_updated(self):
        user_id = self.create_user("alice")
        with self.assertRaises(ValidationError):
            self.call(self.users.update_user, {"id": user_id, "user": {"name": "alicia"}})

    def test_display_name_can_be_128_on_update(self):
        user_id = self.create_user("alice")
        self.call(self.users.update_user, {"id": user_id, "user": {"display_name": "d" * 128}})
        with self.assertRaises(ValidationError):
            self.call(self.users.update_user, {"id": user_id, "user": {"display_name": "d" * 129}})


class TeamServiceTests(PlannerTestCase):

    def setUp(self):
        super().setUp()
        self.alice = self.create_user("alice")
        self.bob = self.create_user("bob")
        self.team = self.create_team("core", self.alice)

    def member_names(self):
        return [u["name"] for u in self.call(self.teams.list_team_users, {"id": self.team})]

    def test_admin_is_added_as_member(self):
        self.assertEqual(self.member_names(), ["alice"])

    def test_team_name_must_be_unique(self):
        with self.assertRaises(ConflictError):
            self.create_team("Core", self.bob)

    def test_add_and_remove_users(self):
        self.call(self.teams.add_users_to_team, {"id": self.team, "users": [self.bob]})
        self.assertEqual(self.member_names(), ["alice", "bob"])
        self.call(self.teams.remove_users_from_team, {"id": self.team, "users": [self.bob]})
        self.assertEqual(self.member_names(), ["alice"])

    def test_admin_cannot_be_removed(self):
        with self.assertRaises(InvalidStateError):
            self.call(self.teams.remove_users_from_team, {"id": self.team, "users": [self.alice]})

    def test_max_50_users_per_request(self):
        with self.assertRaises(ValidationError):
            self.call(self.teams.add_users_to_team, {"id": self.team, "users": list(range(1, 52))})

    def test_team_cannot_exceed_50_users(self):
        extra = [User.objects.create(name=f"user{i}").id for i in range(50)]
        self.call(self.teams.add_users_to_team, {"id": self.team, "users": extra[:49]})
        with self.assertRaises(InvalidStateError):
            self.call(self.teams.add_users_to_team, {"id": self.team, "users": extra[49:]})

    def test_unknown_user_adds_nobody(self):
        with self.assertRaises(NotFoundError):
            self.call(self.teams.add_users_to_team, {"id": self.team, "users": [self.bob, 999]})
        self.assertEqual(self.member_names(), ["alice"])

    def test_get_user_teams(self):
        teams = self.call(self.users.get_user_teams, {"id": self.alice})
        self.assertEqual([t["name"] for t in teams], ["core"])


class BoardServiceTests(PlannerTestCase):

    def setUp(self):
        super().setUp()
        self.alice = self.create_user("alice")
        self.outsider = self.create_user("dave")
        self.team = self.create_team("core", self.alice)
        self.board = self.create_board("Sprint 1", self.team)

    def test_board_name_unique_per_team(self):
        with self.assertRaises(ConflictError):
            self.create_board("sprint 1", self.team)
        other_team = self.create_team("infra", self.outsider)
        self.create_board("Sprint 1", other_team)  # same name in another team is fine

    def test_task_title_unique_per_board(self):
        self.add_task("Build APIs", self.board, self.alice)
        with self.assertRaises(ConflictError):
            self.add_task("build apis", self.board, self.alice)

    def test_task_user_must_be_team_member(self):
        with self.assertRaises(InvalidStateError):
            self.add_task("Build APIs", self.board, self.outsider)

    def test_invalid_task_status(self):
        task = self.add_task("Build APIs", self.board, self.alice)
        with self.assertRaises(ValidationError):
            self.call(self.boards.update_task_status, {"id": task, "status": "DONE"})

    def test_close_board_needs_all_tasks_complete(self):
        task = self.add_task("Build APIs", self.board, self.alice)
        with self.assertRaises(InvalidStateError):
            self.call(self.boards.close_board, {"id": self.board})

        self.call(self.boards.update_task_status, {"id": task, "status": "COMPLETE"})
        result = self.call(self.boards.close_board, {"id": self.board})
        self.assertEqual(result["status"], "CLOSED")

    def test_closed_board_rules(self):
        self.call(self.boards.close_board, {"id": self.board})
        with self.assertRaises(InvalidStateError):
            self.add_task("Late task", self.board, self.alice)
        with self.assertRaises(InvalidStateError):
            self.call(self.boards.close_board, {"id": self.board})
        self.assertEqual(self.call(self.boards.list_boards, {"id": self.team}), [])

    def test_export_board(self):
        self.add_task("Build APIs", self.board, self.alice)
        temp_dir = Path(tempfile.mkdtemp())
        try:
            with patch("planner.services.board_exporter.OUT_DIR", temp_dir):
                file_name = self.call(self.boards.export_board, {"id": self.board})["out_file"]
            report = (temp_dir / file_name).read_text()
        finally:
            shutil.rmtree(temp_dir)

        self.assertIn("PROJECT BOARD : Sprint 1", report)
        self.assertIn("Build APIs", report)


class HttpApiTests(PlannerTestCase):

    def test_endpoints_and_status_codes(self):
        client = Client()

        response = client.post("/api/users/create", '{"name": "alice"}', content_type="application/json")
        self.assertEqual(response.status_code, 200)

        response = client.post("/api/users/create", '{"name": "alice"}', content_type="application/json")
        self.assertEqual(response.status_code, 409)

        response = client.post("/api/users/create", "{bad", content_type="application/json")
        self.assertEqual(response.status_code, 400)

        response = client.post("/api/users/describe", '{"id": 999}', content_type="application/json")
        self.assertEqual(response.status_code, 404)

        self.assertEqual(client.get("/api/users/list").status_code, 200)
        self.assertEqual(client.get("/api/users/create").status_code, 405)
