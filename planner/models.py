from django.db import models


class User(models.Model):
    name = models.CharField(max_length=64, unique=True)
    display_name = models.CharField(max_length=128, blank=True, default="")
    creation_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=128, blank=True, default="")
    admin = models.ForeignKey(User, on_delete=models.PROTECT, related_name="admin_of_teams")
    members = models.ManyToManyField(User, related_name="teams", blank=True)
    creation_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Board(models.Model):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    STATUS_CHOICES = [(OPEN, "Open"), (CLOSED, "Closed")]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="boards")
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=128, blank=True, default="")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=OPEN)
    creation_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("team", "name")]

    def __str__(self):
        return self.name


class Task(models.Model):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    STATUS_CHOICES = [(OPEN, "Open"), (IN_PROGRESS, "In progress"), (COMPLETE, "Complete")]

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="tasks")
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="tasks")
    title = models.CharField(max_length=64)
    description = models.CharField(max_length=128, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=OPEN)
    creation_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("board", "title")]

    def __str__(self):
        return self.title
