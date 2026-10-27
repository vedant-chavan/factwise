import json

from planner.exceptions import ValidationError


def parse_request(request):
    """Turn the JSON request string into a dict."""
    try:
        data = json.loads(request)
    except (json.JSONDecodeError, TypeError):
        raise ValidationError("Request must be a valid JSON string")

    if not isinstance(data, dict):
        raise ValidationError("Request must be a JSON object")
    return data


def get_required_str(data, field, max_length):
    """Return a text field that must be present and not blank."""
    value = data.get(field)
    if value is None:
        raise ValidationError(f"'{field}' is required")
    if not isinstance(value, str):
        raise ValidationError(f"'{field}' must be a string")

    value = value.strip()
    if value == "":
        raise ValidationError(f"'{field}' cannot be empty")
    if len(value) > max_length:
        raise ValidationError(f"'{field}' can be at most {max_length} characters")
    return value


def get_optional_str(data, field, max_length):
    """Return a text field that may be missing (then an empty string is returned)."""
    value = data.get(field)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValidationError(f"'{field}' must be a string")

    value = value.strip()
    if len(value) > max_length:
        raise ValidationError(f"'{field}' can be at most {max_length} characters")
    return value


def to_id(value, field):
    """Convert one value to an int id. Accepts 5 or "5"."""
    if isinstance(value, (bool, float)):
        raise ValidationError(f"'{field}' must be a valid id")
    try:
        return int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"'{field}' must be a valid id")


def get_id(data, field):
    """Return a required id field as an int."""
    value = data.get(field)
    if value is None:
        raise ValidationError(f"'{field}' is required")
    return to_id(value, field)


def get_id_list(data, field, max_items):
    """Return a non-empty list of ids (duplicates removed), with at most max_items ids."""
    values = data.get(field)
    if not isinstance(values, list) or len(values) == 0:
        raise ValidationError(f"'{field}' must be a non-empty list of ids")
    if len(values) > max_items:
        raise ValidationError(f"'{field}' can contain at most {max_items} ids")

    ids = []
    for value in values:
        user_id = to_id(value, field)
        if user_id not in ids:
            ids.append(user_id)
    return ids
