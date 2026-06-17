import os
import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

BASE_URL = "https://api.adzuna.com/v1/api/jobs/in/search/1"


def get_jobs(keyword):

    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": 20,
        "what": keyword,
        "where": "India"
    }

    response = requests.get(BASE_URL, params=params)

    print("APP_ID:", APP_ID)
    print("APP_KEY:", APP_KEY)
    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text[:500])

    if response.status_code != 200:
        return []

    data = response.json()

    jobs = []

    for job in data.get("results", []):
        jobs.append({
            "title": job.get("title"),
            "company": job.get("company", {}).get("display_name"),
            "location": job.get("location", {}).get("display_name"),
            "url": job.get("redirect_url")
        })

    return jobs