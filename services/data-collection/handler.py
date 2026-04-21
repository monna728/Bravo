"""Dispatcher handler for bravo-data-collection Lambda.

Routes to the correct collector based on the 'source' field in the event:
  - "weather"       → collectWeather.lambda_handler  (default)
  - "tlc"           → collectNYCTaxi.lambda_handler
  - "ticketmaster"  → collectTicketmaster.lambda_handler

Example test event:
  { "source": "weather", "lat": -33.8688, "lng": 151.2093,
    "use_forecast_only": true, "return_raw": true }
  { "source": "tlc" }
  { "source": "ticketmaster" }
"""

import json

from collectWeather import lambda_handler as _weather
from collectNYCTaxi import lambda_handler as _tlc
from collectTicketmaster import lambda_handler as _ticketmaster

_ROUTES = {
    "weather": _weather,
    "tlc": _tlc,
    "ticketmaster": _ticketmaster,
}


def lambda_handler(event, context):
    source = (event or {}).get("source", "weather")
    handler = _ROUTES.get(source)
    if handler is None:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": f"Unknown source '{source}'. Valid values: {list(_ROUTES)}"
            }),
        }
    return handler(event, context)
