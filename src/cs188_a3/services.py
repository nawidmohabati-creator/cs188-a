from pathlib import Path

from datetime import date
import requests

from . import db

GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

class NotFound(Exception):
    """Indicate that a requested trip does not exist."""

class Forbidden(Exception):
    """Indicate that a user does not own the requested trip."""

class ValidationError(Exception):
    """Indicate that submitted trip data is invalid."""


def validate_trip_id(trip_id: int) -> None:
    """Validate that a trip ID fits within SQLite's integer range."""
    if trip_id < 1 or trip_id > 2**63 - 1:
        raise NotFound("Trip not found")


def validate_new_trip(data: dict) -> dict:
    """Validate and return data for a new trip."""
    required_fields = {
        "city",
        "start_date",
        "end_date",
        "budget",
        "notes",
    }

    for field in data:
        if field not in required_fields:
            raise ValidationError(f"Unrecognized field: {field}")

    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")

    city = data["city"]
    start_date = data["start_date"]
    end_date = data["end_date"]
    budget = data["budget"]
    notes = data["notes"]

    if not isinstance(city, str) or not city.strip():
        raise ValidationError("City must be a non-blank string")

    if len(city.strip()) > 100:
        raise ValidationError("City cannot exceed 100 characters")

    if not isinstance(start_date, str) or not start_date.strip():
        raise ValidationError("Start date must be a non-blank string")

    if not isinstance(end_date, str) or not end_date.strip():
        raise ValidationError("End date must be a non-blank string")

    try:
        start = date.fromisoformat(start_date.strip())
        end = date.fromisoformat(end_date.strip())
    except ValueError:
        raise ValidationError("Dates must use YYYY-MM-DD format")

    if end < start:
        raise ValidationError("End date cannot be before start date")

    if not isinstance(budget, (int, float)) or isinstance(budget, bool):
        raise ValidationError("Budget must be a number")

    if budget < 0:
        raise ValidationError("Budget cannot be negative")

    if not isinstance(notes, str):
        raise ValidationError("Notes must be a string")

    if len(notes) > 1000:
        raise ValidationError("Notes cannot exceed 1000 characters")

    return {
        "city": city.strip(),
        "start_date": start_date.strip(),
        "end_date": end_date.strip(),
        "budget": float(budget),
        "notes": notes.strip(),
    }


def create_trip(
    db_path: str | Path,
    owner_id: int,
    data: dict,
) -> dict:
    """Validate, create, and return a new trip."""
    trip_data = validate_new_trip(data)

    trip_id = db.create_trip(
        db_path,
        owner_id,
        trip_data["city"],
        trip_data["start_date"],
        trip_data["end_date"],
        trip_data["budget"],
        trip_data["notes"],
    )

    trip = db.get_trip(db_path, trip_id)

    if trip is None:
        raise NotFound("Trip was not found after creation")

    trip.pop("owner_id", None)
    return trip


def list_trips(
    db_path: str | Path,
    city: str | None = None,
) -> list[dict]:
    """Return all trips, optionally filtered by city."""
    return db.get_trips(db_path, city)


def get_trip(
    db_path: str | Path,
    trip_id: int,
) -> dict:
    """Return one trip or raise NotFound if it does not exist."""
    validate_trip_id(trip_id)

    trip = db.get_trip(db_path, trip_id)

    if trip is None:
        raise NotFound("Trip not found")

    trip.pop("owner_id", None)
    return trip


def delete_trip(
    db_path: str | Path,
    user_id: int,
    trip_id: int,
) -> None:
    """Delete a trip if it exists and belongs to the user."""
    validate_trip_id(trip_id)

    trip = db.get_trip(db_path, trip_id)

    if trip is None:
        raise NotFound("Trip not found")

    if trip["owner_id"] != user_id:
        raise Forbidden("You do not own this trip")

    db.delete_trip(db_path, trip_id)


def validate_trip_changes(data: dict) -> dict:
    """Validate fields provided for a trip update."""
    allowed_fields = {
        "city",
        "start_date",
        "end_date",
        "budget",
        "notes",
    }

    if not data:
        raise ValidationError("At least one field is required")

    for field in data:
        if field not in allowed_fields:
            raise ValidationError(f"Unrecognized field: {field}")

    if "city" in data:
        if not isinstance(data["city"], str) or not data["city"].strip():
            raise ValidationError("City must be a non-blank string")
        if len(data["city"].strip()) > 100:
            raise ValidationError("City cannot exceed 100 characters")

    if "start_date" in data:
        if not isinstance(data["start_date"], str) or not data["start_date"].strip():
            raise ValidationError("Start date must be a non-blank string")

    if "end_date" in data:
        if not isinstance(data["end_date"], str) or not data["end_date"].strip():
            raise ValidationError("End date must be a non-blank string")

    try:
        if "start_date" in data:
            date.fromisoformat(data["start_date"].strip())

        if "end_date" in data:
            date.fromisoformat(data["end_date"].strip())
    except ValueError:
        raise ValidationError("Dates must use YYYY-MM-DD format")

    if "budget" in data:
        if not isinstance(data["budget"], (int, float)) or isinstance(data["budget"], bool):
            raise ValidationError("Budget must be a number")

        if data["budget"] < 0:
            raise ValidationError("Budget cannot be negative")

    if "notes" in data and not isinstance(data["notes"], str):
        raise ValidationError("Notes must be a string")
    
    if "notes" in data and len(data["notes"]) > 1000:
        raise ValidationError("Notes cannot exceed 1000 characters")

    changes = data.copy()

    if "city" in changes:
        changes["city"] = changes["city"].strip()

    if "start_date" in changes:
        changes["start_date"] = changes["start_date"].strip()

    if "end_date" in changes:
        changes["end_date"] = changes["end_date"].strip()

    if "budget" in changes:
        changes["budget"] = float(changes["budget"])

    if "notes" in changes:
        changes["notes"] = changes["notes"].strip()

    return changes


def update_trip(
    db_path: str | Path,
    user_id: int,
    trip_id: int,
    changes: dict,
) -> dict:
    """Update a trip if it exists and belongs to the user."""
    validate_trip_id(trip_id)
    changes = validate_trip_changes(changes)

    trip = db.get_trip(db_path, trip_id)

    if trip is None:
        raise NotFound("Trip not found")

    if trip["owner_id"] != user_id:
        raise Forbidden("You do not own this trip")

    start_date = changes.get("start_date", trip["start_date"])
    end_date = changes.get("end_date", trip["end_date"])

    if date.fromisoformat(end_date) < date.fromisoformat(start_date):
        raise ValidationError("End date cannot be before start date")

    db.update_trip(db_path, trip_id, changes)

    updated_trip = db.get_trip(db_path, trip_id)

    if updated_trip is None:
        raise NotFound("Trip not found")

    updated_trip.pop("owner_id", None)
    return updated_trip



def search_destination(city: str) -> dict:
    """Search for a destination and return its location information."""
    if not isinstance(city, str) or not city.strip():
        raise ValidationError("City must be a non-blank string")

    response = requests.get(
        GEOCODING_API_URL,
        params={
            "name": city.strip(),
            "count": 1,
            "language": "en",
            "format": "json",
        },
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()

    if not data.get("results"):
        raise NotFound("Destination not found")

    result = data["results"][0]

    return {
        "name": result["name"],
        "latitude": result["latitude"],
        "longitude": result["longitude"],
        "country": result.get("country"),
    }


def get_destination_weather(latitude: float, longitude: float) -> dict:
    """Return current weather for a destination."""
    response = requests.get(
        WEATHER_API_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,wind_speed_10m",
        },
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()

    return {
        "temperature": data["current"]["temperature_2m"],
        "temperature_unit": data["current_units"]["temperature_2m"],
        "wind_speed": data["current"]["wind_speed_10m"],
        "wind_speed_unit": data["current_units"]["wind_speed_10m"],
    }