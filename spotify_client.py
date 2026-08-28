"""Spotify Web API client.

Uses the Client Credentials OAuth flow, which can read public track and
playlist metadata without requiring a user login.
"""

import base64
import re
from typing import Dict, List, Optional

import requests


class SpotifyClient:
    """Minimal Spotify Web API client for reading track/playlist metadata."""

    API_BASE = "https://api.spotify.com/v1"
    TOKEN_URL = "https://accounts.spotify.com/api/token"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = requests.Session()
        self._access_token: Optional[str] = None

    def _authenticate(self) -> str:
        """Obtain (and cache) an access token using client credentials."""
        if self._access_token:
            return self._access_token

        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        response = self.session.post(
            self.TOKEN_URL,
            data={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {credentials}"},
            timeout=15,
        )
        response.raise_for_status()
        self._access_token = response.json()["access_token"]
        return self._access_token

    def _get(self, path: str, params: Optional[Dict] = None) -> Dict:
        token = self._authenticate()
        response = self.session.get(
            f"{self.API_BASE}{path}",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _parse_track(track: Dict) -> Dict:
        """Normalize a Spotify track object into the app's track dict."""
        images = track.get("album", {}).get("images", [])
        return {
            "title": track.get("name", ""),
            "artist": ", ".join(a.get("name", "") for a in track.get("artists", [])),
            "album": track.get("album", {}).get("name", ""),
            "duration": track.get("duration_ms", 0) // 1000,
            "cover_url": images[0].get("url", "") if images else "",
            "track_id": track.get("id", ""),
            "source": "spotify",
        }

    def extract_track_info(self, track_url: str) -> Optional[Dict]:
        """Return track metadata for a Spotify track URL."""
        track_id = self._extract_id(track_url, "track")
        if not track_id:
            return None
        try:
            data = self._get(f"/tracks/{track_id}")
            return self._parse_track(data)
        except requests.RequestException:
            return None

    def extract_playlist_info(self, playlist_url: str) -> List[Dict]:
        """Return a list of track metadata for a Spotify playlist URL."""
        playlist_id = self._extract_id(playlist_url, "playlist")
        if not playlist_id:
            return []

        tracks: List[Dict] = []
        next_url = f"{self.API_BASE}/playlists/{playlist_id}/tracks"
        token = self._authenticate()
        try:
            while next_url:
                response = self.session.get(
                    next_url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=15,
                )
                response.raise_for_status()
                data = response.json()
                for item in data.get("items", []):
                    track = item.get("track")
                    if track:
                        tracks.append(self._parse_track(track))
                next_url = data.get("next")
        except requests.RequestException:
            pass
        return tracks

    @staticmethod
    def _extract_id(url: str, kind: str) -> Optional[str]:
        """Extract a Spotify resource ID from a URL (track/playlist)."""
        match = re.search(rf"/{kind}/([A-Za-z0-9]+)", url)
        return match.group(1) if match else None
