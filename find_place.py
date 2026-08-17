from serpapi import GoogleSearch
import os
from dotenv import load_dotenv

load_dotenv()

params = {
    "engine": "google_maps",
    "q": "GAIL's Bakery Southbank",
    "api_key": os.getenv("SERPAPI_KEY"),
    "hl": "en"
}

results = GoogleSearch(params).get_dict()

print(results)