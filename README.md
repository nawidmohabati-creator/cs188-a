# Trip Planner API

## Purpose

The Trip Planner API is a multi-user REST API that helps users to register accounts and create, view, update, and delete trips. It also uses the Open-Meteo API to search for destinations and retrieve current weather information, helping users get useful information while planning a trip.

## Getting Started

This project uses Python 3.11 or newer and `uv` for managing the project and its dependencies.

Install the project dependencies with:

```bash
uv sync
```
Run the API with:

```bash
uv run cs188-a3
```
The API runs locally using HTTPS and uses `MyCertificate.crt` and `MyKey.pem` for the certificate and private key.

Run the tests with:

```bash
uv run pytest
```
This project does not require any environment variables because the Open-Meteo API does not require an API key.

## Endpoint Reference


### Register a User

**POST `/register`**

Creates a new user account. Authentication is not required.

**Body fields:**
- `username` — string, required. The username for the new account.
- `password` — string, required. The password for the account and must be at least 8 characters long.

**Success:**
- `201 Created` — The user was registered successfully.

**Errors:**
- `400 Bad Request` — The request is not a JSON object, the username is invalid, or the password is less than 8 characters.
- `409 Conflict` — The username already exists.


### View Profile

**GET `/profile`**

Returns information about the currently authenticated user. Basic authentication is required.

**Parameters:** None.

**Success:**
- `200 OK` — Returns the authenticated user's ID and username.

**Errors:**
- `401 Unauthorized` — Authentication is missing or the username or password is incorrect.


### List Trips

**GET `/trips`**

Returns all trips. Authentication is not required. A city can be provided to filter the results.

**Query parameters:**
- `city` — string, optional. Filters the trips by city.

**Success:**
- `200 OK` — Returns the list of trips that match the request.


### Create a Trip

**POST `/trips`**

Creates a new trip for the authenticated user. Basic authentication is required.

**Body fields:**
- `city` — string, required. The city for the trip.
- `start_date` — string, required. The trip start date.
- `end_date` — string, required. The trip end date.
- `budget` — number, required. The budget for the trip.
- `notes` — string, optional. Additional notes about the trip.

**Success:**
- `201 Created` — The trip was created successfully and the response includes the new trip.

**Errors:**
- `400 Bad Request` — The request data or one of the trip fields is invalid.
- `401 Unauthorized` — Authentication is missing or incorrect.


### View a Trip

**GET `/trips/<trip_id>`**

Returns one trip using its ID. Authentication is not required.

**Path parameters:**
- `trip_id` — integer, required. The ID of the trip to retrieve.

**Success:**
- `200 OK` — Returns the requested trip.

**Errors:**
- `404 Not Found` — The trip ID is invalid or the trip does not exist.


### Update a Trip

**PATCH `/trips/<trip_id>`**

Updates a trip owned by the authenticated user. Basic authentication is required. Only the owner of the trip can update it.

**Path parameters:**
- `trip_id` — integer, required. The ID of the trip to update.

**Body fields:**
- `city` — string, optional. Changes the city.
- `start_date` — string, optional. Changes the start date.
- `end_date` — string, optional. Changes the end date.
- `budget` — number, optional. Changes the budget.
- `notes` — string, optional. Changes the trip notes.

**Success:**
- `200 OK` — The trip was updated successfully.

**Errors:**
- `400 Bad Request` — The request data or one of the provided fields is invalid.
- `401 Unauthorized` — Authentication is missing or incorrect.
- `403 Forbidden` — The authenticated user does not own the trip.
- `404 Not Found` — The trip ID is invalid or the trip does not exist.


### Delete a Trip

**DELETE `/trips/<trip_id>`**

Deletes a trip owned by the authenticated user. Basic authentication is required. Only the owner of the trip can delete it.

**Path parameters:**
- `trip_id` — integer, required. The ID of the trip to delete.

**Success:**
- `200 OK` — The trip was deleted successfully.

**Errors:**
- `401 Unauthorized` — Authentication is missing or incorrect.
- `403 Forbidden` — The authenticated user does not own the trip.
- `404 Not Found` — The trip ID is invalid or the trip does not exist.


### Search for a Destination

**GET `/destination`**

Searches for a destination using a city name and the Open-Meteo geocoding API. Authentication is not required.

**Query parameters:**
- `city` — string, required. The name of the city to search for.

**Success:**
- `200 OK` — Returns the destination name, latitude, longitude, and country.

**Errors:**
- `400 Bad Request` — The city value is missing or invalid.
- `404 Not Found` — The destination could not be found.
- `502 Bad Gateway` — The request to the external Open-Meteo API failed.


### Get Destination Weather

**POST `/destination`**

Searches for a city and returns its current weather information using Open-Meteo. Authentication is not required.

**Body fields:**
- `city` — string, required. The name of the city to get weather information for.

**Success:**
- `200 OK` — Returns the destination information, current temperature, and wind speed.

**Errors:**
- `400 Bad Request` — The request is not a JSON object or the city value is missing or invalid.
- `404 Not Found` — The destination could not be found.
- `502 Bad Gateway` — The request to the external Open-Meteo API failed.


## Example Session

The following example shows how to register a user, create a trip, list the trips, and see what happens when another user tries to delete a trip they do not own.


### 1. Register a User

```bash
curl -k -X POST https://127.0.0.1:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"hunter2hunter2"}'
```

### 2. Create a Trip

```bash
curl -k -X POST https://127.0.0.1:5000/trips \
  -u alice:hunter2hunter2 \
  -H "Content-Type: application/json" \
  -d '{"city":"Chicago","start_date":"2026-11-10","end_date":"2026-11-15","budget":1000,"notes":"Vacation trip"}'
```

### 3. List Trips

```bash
curl -k https://127.0.0.1:5000/trips
```

### 4. Register Another User

```bash
curl -k -X POST https://127.0.0.1:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"bob","password":"hunter2hunter2"}'
```

### 5. Try to Delete Another User's Trip

```bash
curl -k -X DELETE https://127.0.0.1:5000/trips/1 \
  -u bob:hunter2hunter2
```

Because Bob does not own Alice's trip, the API returns:

```json
{
  "message": "You do not own this trip"
}
```

with a `403 Forbidden` status.


## Resources

I used the following external resources while working on this project:

- Open-Meteo API and documentation — used for destination searching and current weather data.  
  Link: https://open-meteo.com/en/docs?utm_source=chatgpt.com
  Link: https://open-meteo.com/en/docs/geocoding-api?utm_source=chatgpt.com

- ChatGPT by OpenAI — used to help me understand how to push my assignment to GitHub and set up GitHub Actions. 
    The commands I used were:

```bash
git status
mkdir -p .github/workflows
touch .github/workflows/tests.yml
git add .
git commit -m "Add CI workflow and complete tests"
git push
```
        
- Stack Overflow — used to help me understand code structures and how different parts of the code work.  
  Link: https://stackoverflow.com/questions/70653/python-authentication-api
  Link: https://stackoverflow.com/questions/76177732/how-to-test-api-with-pytest
  Link: https://stackoverflow.com/questions/76872526/what-is-apps-py-in-django
  Link: https://stackoverflow.com/questions/10935127/way-to-access-resource-files-in-python
  Link: https://stackoverflow.com/questions/51063105/error-service-py

- Course examples and class activities — I used as references for Flask, REST APIs, testing, GitHub Actions, and the project structure.


