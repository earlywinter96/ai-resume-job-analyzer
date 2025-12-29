import requests
import os
from dotenv import load_dotenv

load_dotenv()

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")

BASE_URL = "https://api.adzuna.com/v1/api/jobs"

ROLE_QUERY_MAP = {
    "data": "data analyst",
    "marketing": "digital marketing",
    "sales": "business development",
    "product": "product manager",
    "support": "technical support engineer",
}


def fetch_jobs(role: str, country: str = "in", page: int = 1, results_per_page: int = 20):
    """
    Fetch latest jobs from Adzuna based on RESUME role.
    """
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        raise ValueError("Adzuna credentials not set")

    role_query = ROLE_QUERY_MAP.get(role, role)

    url = f"{BASE_URL}/{country}/search/{page}"

    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_API_KEY,
        "what": role_query,
        "results_per_page": results_per_page,
        "sort_by": "date"
    }

    response = requests.get(url, params=params, timeout=10)

    print("🔗 Adzuna URL:", response.url)
    print("📡 Adzuna Status:", response.status_code)

    response.raise_for_status()

    jobs = response.json().get("results", [])
    print("📦 Jobs returned:", len(jobs))

    return jobs
