import os
import requests
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

BASE_URL = "https://www.googleapis.com/youtube/v3/search"


@lru_cache(maxsize=128)
def search_youtube_playlist(query: str):
    """
    Search for a relevant YouTube playlist.

    - Safe against missing API key
    - Safe against network / quota errors
    - Cached to reduce API usage
    - Returns None or { title, url }
    """

    if not YOUTUBE_API_KEY:
        return None

    if not query or len(query.strip()) < 5:
        return None

    params = {
        "part": "snippet",
        "q": query.strip(),
        "type": "playlist",
        "maxResults": 1,
        "key": YOUTUBE_API_KEY
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=6)

        # Non-200 responses (quota, auth, etc.)
        if response.status_code != 200:
            return None

        data = response.json()

    except Exception:
        return None

    items = data.get("items", [])
    if not items:
        return None

    item = items[0]
    playlist_id = item.get("id", {}).get("playlistId")
    title = item.get("snippet", {}).get("title")

    if not playlist_id or not title:
        return None

    return {
        "title": title,
        "url": f"https://www.youtube.com/playlist?list={playlist_id}"
    }