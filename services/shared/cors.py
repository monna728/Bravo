"""CORS headers shared across all Lambda handlers.

API Gateway requires these on every response (including error responses) for
browser clients (Swagger UI, React frontend, partner integrations) to receive
the response without being blocked by the browser's same-origin policy.
"""

CORS_HEADERS: dict[str, str] = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": (
        "Content-Type,X-Amz-Date,Authorization,"
        "X-Api-Key,X-Amz-Security-Token"
    ),
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}
