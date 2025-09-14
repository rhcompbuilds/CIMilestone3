from django.http import JsonResponse

class JsonErrorMiddleware:
    """
    Converts Django error responses into JSON if the path starts with /api/
    and the response is not already JSON.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only adjust API requests
        if request.path.startswith("/bookings/api/") or request.path.startswith("/api/"):
            content_type = response.get("Content-Type", "")
            if not content_type.startswith("application/json"):
                status_code = response.status_code
                # Replace HTML with JSON
                response = JsonResponse(
                    {"error": response.reason_phrase or "Server error"},
                    status=status_code,
                )

        return response
