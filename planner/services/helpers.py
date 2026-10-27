from planner.exceptions import NotFoundError


def get_object(model, obj_id, label):
    """Load one row by id, or raise NotFoundError if it does not exist."""
    try:
        return model.objects.get(id=obj_id)
    except model.DoesNotExist:
        raise NotFoundError(f"{label} with id '{obj_id}' does not exist")


def format_time(value):
    """Convert a datetime to text for JSON, e.g. 2026-10-27T10:00:00+00:00."""
    if value is None:
        return None
    return value.isoformat(timespec="seconds")
