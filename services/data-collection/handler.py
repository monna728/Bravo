"""Dispatcher handler for bravo-data-collection Lambda.

Two invocation modes, selected by the 'source' field in the event:

1. Targeted collection (partner integrations, scheduled feeds):
     { "source": "weather", ... }  -> collectWeather.lambda_handler
     { "source": "tlc", ... }      -> collectNYCTaxi.lambda_handler
     { "source": "ticketmaster" }  -> collectTicketmaster.lambda_handler

2. Full-pipeline collection (default when 'source' is missing or 'all'):
     {} -> runs all three collectors, returns combined summary.
          A per-source error is captured and reported without failing the run.
"""

import json

import collectNYCTaxi as taxi
import collectTicketmaster as ticketmaster
import collectWeather as weather

_ROUTES = {
    "weather": weather.lambda_handler,
    "tlc": taxi.lambda_handler,
    "ticketmaster": ticketmaster.lambda_handler,
}


def lambda_handler(event, context):
    ev = event if isinstance(event, dict) else {}
    source = (ev.get("source") or "").lower()

    if source and source != "all":
        handler = _ROUTES.get(source)
        if handler is None:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": f"Unknown source '{source}'. "
                             f"Valid values: {list(_ROUTES) + ['all']}"
                }),
            }
        return handler(ev, context)

    results = {}
    for key, handler in (("nyc_tlc", taxi.lambda_handler),
                         ("ticketmaster", ticketmaster.lambda_handler),
                         ("weather", weather.lambda_handler)):
        try:
            response = handler(ev, context)
            results[key] = json.loads(response["body"])
            results[key]["status"] = "success"
        except Exception as e:
            results[key] = {"status": "error", "error": str(e)}

    overall_status = (
        "success" if all(r["status"] == "success" for r in results.values())
        else "partial"
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message": "Data collection complete",
            "overall_status": overall_status,
            "sources": results,
        }),
    }
