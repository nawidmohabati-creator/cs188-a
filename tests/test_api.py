import pytest

from cs188_a3.app import create_app


@pytest.fixture
def client(tmp_path):
    """Create a test client that uses a temporary database."""
    app = create_app(db_path=tmp_path / "test.db")
    app.testing = True

    with app.test_client() as test_client:
        yield test_client


def make_user(client, name: str = "alice") -> tuple[str, str]:
    """Register a user and return their username and password."""
    password = "hunter2hunter2"

    client.post(
        "/register",
        json={"username": name, "password": password},
    )

    return name, password


def test_register_user(client) -> None:
    """Test that a new user can register successfully."""
    response = client.post(
        "/register",
        json={
            "username": "nawid",
            "password": "password123",
        },
    )

    assert response.status_code == 201
    assert response.get_json()["username"] == "nawid"


def test_create_trip(client) -> None:
    """Test that an authenticated user can create a trip."""
    username, password = make_user(client, "alice")

    response = client.post(
    "/trips",
    json={
        "city": "Chicago",
        "start_date": "2026-11-10",
        "end_date": "2026-11-15",
        "budget": 1500,
        "notes": "Vacation trip",
    },
)

    assert response.status_code == 401
    assert response.get_json()["message"] == "Authentication required"


    response = client.post(
        "/trips",
        auth=(username, password),
        json={
            "city": "Chicago",
            "start_date": "2026-11-10",
            "end_date": "2026-11-15",
            "budget": 1500,
            "notes": "Vacation trip",
        },
    )

    assert response.status_code == 201
    assert response.get_json()["city"] == "Chicago"
    assert response.get_json()["budget"] == 1500.0
    assert response.headers["Location"].startswith("/trips/")


def test_filter_trips_by_city(client) -> None:
    """Test that trips can be filtered by city."""
    username, password = make_user(client, "alice")

    client.post(
        "/trips",
        auth=(username, password),
        json={
            "city": "Chicago",
            "start_date": "2026-11-10",
            "end_date": "2026-11-15",
            "budget": 1500,
            "notes": "Chicago trip",
        },
    )

    client.post(
        "/trips",
        auth=(username, password),
        json={
            "city": "Boston",
            "start_date": "2026-12-01",
            "end_date": "2026-12-05",
            "budget": 1200,
            "notes": "Boston trip",
        },
    )

    response = client.get("/trips?city=Chicago")

    assert response.status_code == 200
    assert len(response.get_json()) == 1
    assert response.get_json()[0]["city"] == "Chicago"


def test_update_trip(client) -> None:
    """Test that a trip owner can update their trip."""
    username, password = make_user(client, "alice")

    create_response = client.post(
        "/trips",
        auth=(username, password),
        json={
            "city": "Chicago",
            "start_date": "2026-11-10",
            "end_date": "2026-11-15",
            "budget": 1500,
            "notes": "Vacation trip",
        },
    )

    trip_id = create_response.get_json()["id"]

    response = client.patch(
        f"/trips/{trip_id}",
        auth=(username, password),
        json={"budget": 2000},
    )

    assert response.status_code == 200
    assert response.get_json()["budget"] == 2000.0
    assert response.get_json()["city"] == "Chicago"


def test_delete_trip(client) -> None:
    """Test that a trip owner can delete their trip."""
    username, password = make_user(client, "alice")

    create_response = client.post(
        "/trips",
        auth=(username, password),
        json={
            "city": "Chicago",
            "start_date": "2026-11-10",
            "end_date": "2026-11-15",
            "budget": 1500,
            "notes": "Vacation trip",
        },
    )

    trip_id = create_response.get_json()["id"]

    response = client.delete(
        f"/trips/{trip_id}",
        auth=(username, password),
    )

    assert response.status_code == 200
    assert response.get_json()["message"] == "Trip deleted successfully"

    get_response = client.get(f"/trips/{trip_id}")
    assert get_response.status_code == 404


def test_trip_ownership(client) -> None:
    """Test that another user can read a trip but cannot modify or delete it."""
    alice_username, alice_password = make_user(client, "alice")
    bob_username, bob_password = make_user(client, "bob")

    create_response = client.post(
        "/trips",
        auth=(alice_username, alice_password),
        json={
            "city": "Chicago",
            "start_date": "2026-11-10",
            "end_date": "2026-11-15",
            "budget": 1500,
            "notes": "Alice's trip",
        },
    )

    trip_id = create_response.get_json()["id"]

    read_response = client.get(f"/trips/{trip_id}")

    assert read_response.status_code == 200

    update_response = client.patch(
        f"/trips/{trip_id}",
        auth=(bob_username, bob_password),
        json={"budget": 2000},
    )

    assert update_response.status_code == 403
    assert update_response.get_json()["message"] == "You do not own this trip"

    delete_response = client.delete(
        f"/trips/{trip_id}",
        auth=(bob_username, bob_password),
    )

    assert delete_response.status_code == 403
    assert delete_response.get_json()["message"] == "You do not own this trip"


def test_create_trip_wrong_type(client) -> None:
    """Test that a trip with the wrong field type returns 400."""
    username, password = make_user(client, "alice")

    response = client.post(
        "/trips",
        auth=(username, password),
        json={
            "city": "Chicago",
            "start_date": "2026-11-10",
            "end_date": "2026-11-15",
            "budget": "fifteen hundred",
            "notes": "Vacation trip",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Budget must be a number"

    response = client.post(
    "/trips",
    auth=(username, password),
    json=["Chicago", "Vacation"],
)

    assert response.status_code == 400
    assert response.get_json()["message"] == "A JSON object is required"


# This code runs the same test with zero, a negative ID, and a very large ID.
# It also tells pytest to run the test function multiple times with different values for the trip_id parameter.
@pytest.mark.parametrize(
    "trip_id",
    [
        0,
        -1,
        2**63,
    ],
)


def test_invalid_trip_ids(client, trip_id: int) -> None:
    """Test that invalid trip IDs return 404."""
    response = client.get(f"/trips/{trip_id}")

    assert response.status_code == 404
    assert response.get_json()["message"] == "Trip not found"