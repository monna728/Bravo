"""Lambda handler for data collection service.

Orchestrates collection from all three sources:
  - NYC TLC (taxi trips)
  - Ticketmaster (events)
  - Open-Meteo (weather)

Each source is collected independently so a failure in one
does not block the others. Results are summarised in the response.
"""

import json
import os

import collectNYCTaxi as taxi
import collectTicketmaster as ticketmaster
import collectWeather as weather


def lambda_handler(event: dict, context) -> dict:
    """AWS Lambda entry point for data collection.

    Runs all three collectors and returns a combined summary.
    A per-source error is captured and reported without failing the whole run.
    """
    results = {}

    # --- NYC TLC ---
    try:
        response = taxi.lambda_handler(event, context)
        results["nyc_tlc"] = json.loads(response["body"])
        results["nyc_tlc"]["status"] = "success"
    except Exception as e:
        results["nyc_tlc"] = {"status": "error", "error": str(e)}

    # --- Ticketmaster ---
    try:
        response = ticketmaster.lambda_handler(event, context)
        results["ticketmaster"] = json.loads(response["body"])
        results["ticketmaster"]["status"] = "success"
    except Exception as e:
        results["ticketmaster"] = {"status": "error", "error": str(e)}

    # --- Weather ---
    try:
        response = weather.lambda_handler(event, context)
        results["weather"] = json.loads(response["body"])
        results["weather"]["status"] = "success"
    except Exception as e:
        results["weather"] = {"status": "error", "error": str(e)}

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