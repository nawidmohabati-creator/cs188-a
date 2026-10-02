from . import db, services

import sqlite3

from flask import current_app, g, request
from flask_restful import Resource
from flask_bcrypt import Bcrypt

from . import db

from .auth import auth_required

bcrypt = Bcrypt()


# Adding class Register
class Register(Resource):
    """Handle new user registration."""

    def post(self) -> tuple[dict, int]:
        """Register a user with a username and password."""
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return {"message": "A JSON object is required"}, 400

        username = data.get("username")
        password = data.get("password")

        if not isinstance(username, str) or not username.strip():
            return {"message": "A valid username is required"}, 400

        if not isinstance(password, str) or len(password) < 8:
            return {"message": "Password must be at least 8 characters"}, 400

        username = username.strip()
        db_path = current_app.config["DB_PATH"]

        password_hash = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        try:
            user_id = db.create_user(db_path, username, password_hash)
        except sqlite3.IntegrityError:
            return {"message": "Username already exists"}, 409

        return {
            "id": user_id,
            "username": username
        }, 201


class Profile(Resource):
    """Handle requests for the authenticated user's profile."""

    @auth_required
    def get(self) -> tuple[dict, int]:
        """Return information about the authenticated user."""
        return {
            "id": g.user_id,
            "username": g.username
        }, 200



class TripList(Resource):
    """Handle requests for the trip collection."""

    @auth_required
    def post(self) -> tuple[dict, int, dict]:
        """Create a trip owned by the authenticated user."""
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return {"message": "A JSON object is required"}, 400

        try:
            trip = services.create_trip(
                current_app.config["DB_PATH"],
                g.user_id,
                data,
            )
        except services.ValidationError as error:
            return {"message": str(error)}, 400

        return trip, 201, {"Location": f"/trips/{trip['id']}"}

    def get(self) -> tuple[list[dict], int]:
        """Return all trips, optionally filtered by city."""
        city = request.args.get("city")

        trips = services.list_trips(
            current_app.config["DB_PATH"],
            city,
        )

        return trips, 200


class TripDetail(Resource):
    """Handle requests for one trip."""

    def get(self, trip_id: int) -> tuple[dict, int]:
        """Return one trip by its ID."""
        try:
            trip = services.get_trip(
                current_app.config["DB_PATH"],
                trip_id,
            )
        except services.NotFound:
            return {"message": "Trip not found"}, 404

        return trip, 200

    @auth_required
    def patch(self, trip_id: int) -> tuple[dict, int]:
        """Update a trip owned by the authenticated user."""
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return {"message": "A JSON object is required"}, 400

        try:
            trip = services.update_trip(
                current_app.config["DB_PATH"],
                g.user_id,
                trip_id,
                data,
            )
        except services.NotFound:
            return {"message": "Trip not found"}, 404
        except services.Forbidden:
            return {"message": "You do not own this trip"}, 403
        except services.ValidationError as error:
            return {"message": str(error)}, 400

        return trip, 200

    @auth_required
    def delete(self, trip_id: int) -> tuple[dict, int]:
        """Delete a trip owned by the authenticated user."""
        try:
            services.delete_trip(
                current_app.config["DB_PATH"],
                g.user_id,
                trip_id,
            )
        except services.NotFound:
            return {"message": "Trip not found"}, 404
        except services.Forbidden:
            return {"message": "You do not own this trip"}, 403

        return {"message": "Trip deleted successfully"}, 200