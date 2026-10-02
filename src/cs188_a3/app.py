from .auth import bcrypt as auth_bcrypt
from pathlib import Path

from flask import Flask
from flask_restful import Api

from .db import init_db
from .resources import Register, Profile, TripList, TripDetail, bcrypt

def create_app(db_path: str | Path = "trips.db") -> Flask:
    """Create and configure the Trip Planner application."""
    app = Flask(__name__)
    app.config["DB_PATH"] = str(db_path)

    bcrypt.init_app(app)
    auth_bcrypt.init_app(app)
    init_db(app.config["DB_PATH"])

    api = Api(app)
    api.add_resource(Register, "/register")
    api.add_resource(Profile, "/profile")
    api.add_resource(TripList, "/trips")
    api.add_resource(
    TripDetail,
    "/trips/<int:trip_id>",
    "/trips/<int(signed=True):trip_id>",
)

    return app


def run_app() -> None:
    """Start the Trip Planner API over HTTPS."""
    app = create_app()
    app.run(
        debug=False,
        ssl_context=("MyCertificate.crt", "MyKey.pem")
    )