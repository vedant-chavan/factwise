from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from planner.exceptions import (
    ConflictError,
    InvalidStateError,
    NotFoundError,
    PlannerError,
    ValidationError,
)

# Which HTTP status code to send back for each type of error.
ERROR_STATUS_CODES = {
    ValidationError: 400,     # Bad Request
    NotFoundError: 404,       # Not Found
    ConflictError: 409,       # Conflict
    InvalidStateError: 422,   # Unprocessable Entity
}


def api_view(service_method, method="POST"):
    """
    Turn a service method into a Django view.

    POST views pass the request body (a JSON string) to the service method.
    GET views (list_users, list_teams) call the method with no input.
    """

    @csrf_exempt
    def view(request):
        if request.method != method:
            return JsonResponse({"error": f"Use {method} for this endpoint"}, status=405)

        try:
            if method == "POST":
                result = service_method(request.body.decode("utf-8"))
            else:
                result = service_method()
        except PlannerError as error:
            status = ERROR_STATUS_CODES.get(type(error), 400)
            return JsonResponse({"error": type(error).__name__, "message": str(error)}, status=status)

        return HttpResponse(result, content_type="application/json")

    return view
