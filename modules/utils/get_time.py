import requests
from datetime import datetime
from data.urls import WORLD_TIME_API_URL


def get_time() -> dict | None:
    response = requests.get(WORLD_TIME_API_URL)

    if response.status_code != 200:
        return None

    data = response.json()

    return {
        "datetime": data["datetime"],
        "abbreviation": data["abbreviation"]
    }


def format_time(datetime_str: str):
    dt = datetime.fromisoformat(datetime_str)
    return dt.strftime("%Y-%m-%d %H-%M-%S")
