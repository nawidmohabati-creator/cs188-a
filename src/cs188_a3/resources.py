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