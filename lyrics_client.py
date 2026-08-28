import requests
import urllib.parse


class LyricsClient:
    """Simple lyrics fetcher using lyrics.ovh as fallback."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (MusicDownloader/1.0)'
        })

    def fetch_lyrics(self, artist: str, title: str) -> str | None:
        if not artist or not title:
            return None
        try:
            a = urllib.parse.quote_plus(artist)
            t = urllib.parse.quote_plus(title)
            url = f"https://api.lyrics.ovh/v1/{a}/{t}"
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data and data.get('lyrics'):
                    return data.get('lyrics')
            return None
        except Exception:
            return None
