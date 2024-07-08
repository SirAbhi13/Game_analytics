# Game Analytics: A CSV Analyzer


Deployed at : http://13.233.124.135:8000/api/games/query/ (EC2 Deployment)

## Table of Contents
1. [Estimated Running Cost](#estimated-running-cost)
1. [Local Setup](#local-setup)
    - [Virtual Environment](#virtual-environment)
    - [Install Dependencies](#install-dependencies)
    - [Database Setup](#database-setup)
2. [Run the Server and Celery Task](#run-the-server-and-celery-task)
3. [Optimisations Made](#optimisations-made)
4. [Key Features](#key-features)
5. [API Spec](#api-spec)

### Estimated Running cost:
If we ignore the free tier benefits, since I am simply running the containers on the ec2 instance, the costs to run this app aren't much.

1. EC2 Instance:
I am using a t2.micro instance (to stay within the free tier if possible):
]
Cost: $0.0116 per hour (if beyond free tier)
Monthly cost: $0.0116 * 24 * 30 = $8.35


2. EBS Storage:
Assuming 8 GB gp2 storage (minimum for most AMIs):
Cost: $0.10 per GB-month
Monthly cost: 8 * $0.10 = $0.80


3. Data Transfer:
Assuming minimal outbound traffic, let's estimate 5 GB per month:
Cost: $0.09 per GB (first 10 TB/month)
Monthly cost: 5 * $0.09 = $0.45

Total estimated monthly cost: $9.60

## Local Setup

### Virtual Environment
1. Clone repo and navigate to project root.

    ```bash
    python3 -m pip install poetry
    python3 -m venv .venv
    ```
2. activate the virtual environment
```
source .venv/bin/activate
```
### Install Dependencies
We will be using poetry to install the packages.

4. Navigate to the project directory (if not already) and Run

    ```bash
	poetry install
    cp .env.example .env

    ```
    to install dependencies and packages and create .env file from .env.example
    NOTE: You need to have [RabbitMQ](https://www.rabbitmq.com/docs/download) installed in order for this app to work.

### Database Setup
1. Previous command should have created `.env` file, populate it with relevant fields. No need to change `SECRET_KEY`.
2. Setup the db credentials in the `.env` following the example in `.env.example`. I'm using redditMQ for my celery broker and results of celery can be stored in table of choice.
3. Run `make db` to migrate changes to db.

### Run the server and celery task

You will need to open two terminals, after that
- start django server using `python3 manage.py runserver`
- start celery broker using `celery -A game_analytics worker -l info  --pool=solo`

## Optimisations made

- Used bulk create when storing data in db obtained from the csv file recieved. refer `api.tasks.process_csv_file`
- stores 10,000 entries at once.
- Used celery to make the application asynchronous, so as to prevent high loading time when csv is uploaded.

## Key Features

### Processing of CSV happens asynchronously
Utilised celery worker to execute the task of storing data from csv to DB asynchronously.
### Api with proper filters.
The `localhost:8000/api/games/query` is configured to accept params that can be used to filter the data. Helpful for using in dashboard.

### API Endpoint to check the status of csv task.
- Special API endpoint to check the status of the task which uses celery.result to give an update if the csv processing was successful.

### Easy User Sign-Up and Login
- Uses User model of django and JWT token authentication to for user signup and login before using the API (Change value of AUTHENTICATION to True in .env to enable this)
## API Spec

### Sign-Up (POST)
- endpoint = `http://localhost:8000/accounts/signup/`
- takes username and password params and creates a user.

    Example Request:
    ```bash
    curl --location 'http://127.0.0.1:8000/accounts/signup/' ^
    --header 'Content-Type: application/x-www-form-urlencoded' ^
    --data-urlencode 'username=testuser' ^
    --data-urlencode 'password=anewpass'
    ```

- Response:
    Simply returns:

    ```json

    {"detail":"Signup successful."}
    ```

### Login (POST)
- endpoint = `http://localhost:8000/accounts/login/`
- takes username and password params and returns auth token

    Example Request
    ```bash
    curl --location 'http://127.0.0.1:8000/accounts/login/' ^
    --form 'username="testuser"' ^
    --form 'password="anewpass"'
    ```
- Response:
    Returns:
    ```json
    {
        "detail": "User verified, login successful.",
        "refresh": "token here",
        "access": "token here"
    }
    ```

### Upload CSV to the app (POST)
- endpoint = `localhost:8000/api/games/upload_csv/`
- takes a url param as an input in the body of the request

    Example of a curl request
    ```bash
    curl --location 'http://localhost:8000/api/games/upload_csv/' ^
    --header 'Authorization: Bearer {your token}' ^
    --header 'Content-Type: application/json' ^
    --data '{
        "url": "https://docs.google.com/spreadsheets/d/1ShbFMzRUuIJY8amTA58UuEHwsc3UmAnd_LzduBwcBhE/export?format=csv"
    }'
    ```
    - need to use Authorization head if authentication is enabled.
    - can use form-data for sending url too.

- Response:

        Example
    ```json
    {
    "message": "CSV processing started",
    "task_id": "9c71402f-4706-41d2-83b7-6ae3294ae204"
    }
    ```

### Check status of task processing CSV (GET)
- endpoint = `localhost:8000/api/trigger-fetch-yt/`
- simply queries celery worker to check if the csv has been processed

- Example of curl request
    ```bash
    curl --location 'http://localhost:8000/api/games/check_csv_status?task_id=c2a2f317-1db3-47d3-bc6e-7e051bac3812' ^
    --header 'Authorization: Bearer {your token}'
    ```
    - need to use Authorization head if authentication is enabled.

- Response

    ```json
    {
    "status": "completed",
    "result": {
        "message": "CSV file processed successfully"
    }
    }
    ```

### Query the database with different filters (GET)
- endpoint = `http://localhost:8000/api/games/query/`
- built to spec as desired.
- has exact matching for numerical columns
- has substring matching for string columns
- has max, min and avg calculation support for Price, dlc_count, postive, negative
- Example curl request

    ```bash
    curl --location 'localhost:8000/api/games/query/?date_release_to=2020-12-31&date_release_from=2020-01-01'
    ```

    Some more examples

    Games released in a specific year:
    GET /api/games/query/?date_release_from=2020-01-01&date_release_to=2020-12-31

    Free games:
    GET /api/games/query/?price=0

    Games with a specific developer:
    GET /api/games/query/?developers=Team17%20Digital%20Ltd

    Games supporting multiple languages:
    GET /api/games/query/?supported_languages=English,French,German

    Games with Steam Achievements:
    GET /api/games/query/?categories=Steam%20Achievements

    Games in a specific genre:
    GET /api/games/query/?genres=RPG

    Games with specific tags:
    GET /api/games/query/?tags=Indie,Action

    Games released after a certain date with a maximum price:
    GET /api/games/query/?date_release_from=2019-01-01&price=15

    Games with a specific required age:
    GET /api/games/query/?required_age=0

    Games with DLC:
    GET /api/games/query/?dlc_count=1

    Games supporting specific platforms:
    GET /api/games/query/?windows=TRUE&mac=TRUE&linux=TRUE

    Games with a minimum number of positive reviews:
    GET /api/games/query/?positive=50

    Combination query:
    GET /api/games/query/?genres=Indie&price=5&date_release_from=2018-01-01&supported_languages=English

    Query for a specific game by name:
    GET /api/games/query/?name=Alien%20Breed%203:%20Descent

    Games with multiplayer support:
    GET /api/games/query/?categories=Multi-player
