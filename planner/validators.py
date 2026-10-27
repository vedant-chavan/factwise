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


def get_id(data, field):
    """Return an id field as an int. Accepts 5 or "5"."""
    value = data.get(field)
    if value is None:
        raise ValidationError(f"'{field}' is required")
    if isinstance(value, (bool, float)):
        raise ValidationError(f"'{field}' must be a valid id")

    try:
        return int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"'{field}' must be a valid id")
