class PlannerError(Exception):
    """Parent of all errors raised by the planner APIs."""
    pass


class ValidationError(PlannerError):
    """The input is wrong: bad JSON, missing field, wrong type or too long."""
    pass


class NotFoundError(PlannerError):
    """A user, team, board or task with the given id does not exist."""
    pass


class ConflictError(PlannerError):
    """The request would create a duplicate, e.g. a user name that is already taken."""
    pass


class InvalidStateError(PlannerError):
    """The input is fine but the action is not allowed right now, e.g. adding a task to a CLOSED board."""
    pass
