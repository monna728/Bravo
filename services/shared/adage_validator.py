"""ADAGE 3.0 schema validation for all data pipeline outputs."""

from jsonschema import validate, ValidationError

ADAGE3_SCHEMA = {
    "type": "object",
    "properties": {
        "data_source": {"type": "string"},
        "dataset_type": {"type": "string"},
        "dataset_id": {"type": "string"},
        "time_object": {
            "type": "object",
            "properties": {
                "timestamp": {"type": "string"},
                "timezone": {"type": "string"},
            },
            "required": ["timestamp", "timezone"],
        },
        "events": {
            "type": "array",
            "items": {"$ref": "#/$defs/events"},
            "minItems": 1,
        },
    },
    "required": ["data_source", "dataset_id", "dataset_type", "time_object", "events"],
    "$defs": {
        "events": {
            "type": "object",
            "properties": {
                "time_object": {
                    "type": "object",
                    "properties": {
                        "timestamp": {"type": "string"},
                        "duration": {"type": "number"},
                        "timezone": {"type": "string"},
                        "duration_unit": {"type": "string"},
                    },
                    "required": ["timestamp", "duration", "duration_unit", "timezone"],
                },
                "event_type": {"type": "string"},
                "attribute": {"type": "object"},
            },
            "required": ["time_object", "event_type", "attribute"],
        },
    },
}


def validate_adage3(data: dict) -> tuple[bool, str]:
    """Validate a dict against the ADAGE 3.0 schema.

    Returns (True, 'Valid data') on success or (False, error_message) on failure.
    """
    try:
        validate(instance=data, schema=ADAGE3_SCHEMA)
        return True, "Valid data"
    except ValidationError as e:
        return False, f"Validation error at {list(e.absolute_path)}: {e.message}"


def validate_adage3_file(filepath: str) -> tuple[bool, str]:
    """Load a JSON file and validate it against the ADAGE 3.0 schema."""
    import json

    with open(filepath, "r") as f:
        data = json.load(f)
    return validate_adage3(data)
