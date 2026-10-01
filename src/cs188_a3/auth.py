from functools import wraps
from typing import Callable

from flask import current_app, g, request
from flask_bcrypt import Bcrypt

from . import db

bcrypt = Bcrypt()


def auth_required(func: Callable) -> Callable:
    """Require valid HTTP Basic authentication for an endpoint."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth = request.authorization

        if auth is None or not auth.username or not auth.password:
            return {"message": "Authentication required"}, 401

        user = db.get_user(
            current_app.config["DB_PATH"],
            auth.username
        )

        if user is None:
            return {"message": "Invalid username or password"}, 401

        user_id, password_hash = user

        if not bcrypt.check_password_hash(password_hash, auth.password):
            return {"message": "Invalid username or password"}, 401

        g.user_id = user_id
        g.username = auth.username

        return func(*args, **kwargs)

    return wrapper