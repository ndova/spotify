"""Minimal iTunes client used by the Streamlit app.

Provides: iTunesClient with methods used by app.py:
- search_tracks, search_albums, search_artists
- get_album_tracks, get_artist_albums, get_top_songs
- get_track_preview

This is a compact, dependency-light implementation built on `requests`.
"""
from __future__ import annotations

import requests
from typing import List

class iTunesClient:
    def __init__(self, session: requests.Session | None = None) -> None:
        self.s = session or requests.Session()
        self.s.headers.update({
            "User-Agent": "MusicDownloader/1.0",
            "Accept": "application/json",
        })

    def _safe_get_json(self, url: str, params: dict | None = None, timeout: int = 8):
        try:
            r = self.s.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    def search_tracks(self, query: str, limit: int = 25) -> List[dict]:
        q = {"term": query, "entity": "song", "limit": limit}
        data = self._safe_get_json("https://itunes.apple.com/search", params=q)
        if not data:
            return []
        out = []
        for r in data.get("results", []):
            # Prefer a higher-resolution artwork by replacing common size tokens
            art = r.get("artworkUrl100") or r.get("artworkUrl60") or r.get("artworkUrl30")
            if art and "100x100" in art:
                art = art.replace("100x100", "600x600")
            elif art and "60x60" in art:
                art = art.replace("60x60", "600x600")
            elif art and "30x30" in art:
                art = art.replace("30x30", "600x600")

            # Parse release date - extract year for convenience
            release_date = r.get("releaseDate")
            release_year = None
            if release_date:
                try:
                    # releaseDate format: "2020-01-15T08:00:00Z"
                    release_year = release_date[:4]
                except Exception:
                    pass

            out.append({
                "title": r.get("trackName") or r.get("name"),
                "artist": r.get("artistName"),
                "album": r.get("collectionName"),
                "cover_url": art,
                "preview_url": r.get("previewUrl"),
                "track_id": r.get("trackId"),
                "duration": int(r.get("trackTimeMillis", 0) / 1000) if r.get("trackTimeMillis") else None,
                "genre": r.get("primaryGenreName"),
                "release_date": release_date,
                "release_year": release_year,
            })
        return out

    def search_albums(self, query: str, limit: int = 10) -> List[dict]:
        q = {"term": query, "entity": "album", "limit": limit}
        data = self._safe_get_json("https://itunes.apple.com/search", params=q)
        if not data:
            return []
        out = []
        for r in data.get("results", []):
            art = r.get("artworkUrl100") or r.get("artworkUrl60") or r.get("artworkUrl30")
            if art and "100x100" in art:
                art = art.replace("100x100", "600x600")
            elif art and "60x60" in art:
                art = art.replace("60x60", "600x600")
            elif art and "30x30" in art:
                art = art.replace("30x30", "600x600")

            release_date = r.get("releaseDate")
            release_year = None
            if release_date:
                try:
                    release_year = release_date[:4]
                except Exception:
                    pass

            out.append({
                "album": r.get("collectionName"),
                "album_id": r.get("collectionId"),
                "artist": r.get("artistName"),
                "cover_url": art,
                "track_count": r.get("trackCount"),
                "genre": r.get("primaryGenreName"),
                "release_date": release_date,
                "release_year": release_year,
            })
        return out

    def search_artists(self, query: str, limit: int = 10) -> List[dict]:
        q = {"term": query, "entity": "musicArtist", "limit": limit}
        data = self._safe_get_json("https://itunes.apple.com/search", params=q)
        if not data:
            return []
        out = []
        for r in data.get("results", []):
            art = r.get("artworkUrl100") or r.get("artworkUrl60") or r.get("artworkUrl30")
            if art and "100x100" in art:
                art = art.replace("100x100", "600x600")
            elif art and "60x60" in art:
                art = art.replace("60x60", "600x600")
            elif art and "30x30" in art:
                art = art.replace("30x30", "600x600")

            out.append({
                "artist": r.get("artistName"),
                "artist_id": r.get("artistId"),
                "genre": r.get("primaryGenreName"),
                "cover_url": art,
            })
        return out

    def get_album_tracks(self, album_id: str) -> List[dict]:
        try:
            params = {"id": album_id, "entity": "song"}
            data = self._safe_get_json("https://itunes.apple.com/lookup", params=params)
            if not data:
                return []
            results = data.get("results", [])
            # first item is collection info; remaining are tracks
            tracks = []
            for r in results:
                if r.get("wrapperType") == "track":
                    tracks.append(self._map_track(r))
            return tracks
        except Exception:
            return []

    def get_artist_albums(self, artist_id: str, limit: int = 50) -> List[dict]:
        try:
            params = {"id": artist_id, "entity": "album", "limit": limit}
            data = self._safe_get_json("https://itunes.apple.com/lookup", params=params)
            if not data:
                return []
            results = data.get("results", [])
            out = []
            for r in results:
                if r.get("wrapperType") == "collection":
                    art = r.get("artworkUrl100") or r.get("artworkUrl60") or r.get("artworkUrl30")
                    if art and "100x100" in art:
                        art = art.replace("100x100", "600x600")
                    elif art and "60x60" in art:
                        art = art.replace("60x60", "600x600")
                    elif art and "30x30" in art:
                        art = art.replace("30x30", "600x600")

                    release_date = r.get("releaseDate")
                    release_year = None
                    if release_date:
                        try:
                            release_year = release_date[:4]
                        except Exception:
                            pass

                    out.append({
                        "album": r.get("collectionName"),
                        "album_id": r.get("collectionId"),
                        "artist": r.get("artistName"),
                        "cover_url": art,
                        "track_count": r.get("trackCount"),
                        "genre": r.get("primaryGenreName"),
                        "release_date": release_date,
                        "release_year": release_year,
                    })
            return out
        except Exception:
            return []

    def get_top_songs(self, country: str = "US", limit: int = 10) -> List[dict]:
        # Primary modern endpoint
        primary = f"https://rss.itunes.apple.com/api/v1/{country}/itunes/top-songs/{limit}/explicit.json"
        data = self._safe_get_json(primary)
        if data and isinstance(data, dict):
            feed = data.get("feed", {})
            results = feed.get("results") or []
            out = []
            for r in results:
                art = r.get("artworkUrl100") or r.get("artworkUrl60") or r.get("artworkUrl30")
                if art and "100x100" in art:
                    art = art.replace("100x100", "600x600")
                elif art and "60x60" in art:
                    art = art.replace("60x60", "600x600")
                elif art and "30x30" in art:
                    art = art.replace("30x30", "600x600")

                release_date = r.get("releaseDate")
                release_year = None
                if release_date:
                    try:
                        release_year = release_date[:4]
                    except Exception:
                        pass

                out.append({
                    "title": r.get("name"),
                    "artist": r.get("artistName"),
                    "album": r.get("collectionName") or r.get("albumName"),
                    "cover_url": art,
                    "preview_url": None,
                    "track_id": r.get("id"),
                    "release_date": release_date,
                    "release_year": release_year,
                })
            return out

        # Fallback older RSS
        alt = f"https://itunes.apple.com/{country.lower()}/rss/topsongs/limit={limit}/json"
        data2 = self._safe_get_json(alt)
        if data2 and isinstance(data2, dict):
            feed = data2.get("feed", {})
            entries = feed.get("entry") or []
            out = []
            for e in entries:
                # entry structure varies; attempt to extract basic fields
                name = e.get("im:name", {}).get("label")
                artist = e.get("im:artist", {}).get("label")
                image = None
                imgs = e.get("im:image", [])
                if imgs:
                    image = imgs[-1].get("label")
                # try to upsize image if possible
                if image and "100x100" in image:
                    image = image.replace("100x100", "600x600")
                elif image and "60x60" in image:
                    image = image.replace("60x60", "600x600")
                elif image and "30x30" in image:
                    image = image.replace("30x30", "600x600")
                out.append({
                    "title": name,
                    "artist": artist,
                    "album": None,
                    "cover_url": image,
                    "preview_url": None,
                    "track_id": None,
                })
            return out

        return []

    def get_track_preview(self, track_id: str) -> str | None:
        try:
            params = {"id": track_id, "entity": "song"}
            data = self._safe_get_json("https://itunes.apple.com/lookup", params=params)
            if not data:
                return None
            results = data.get("results", [])
            for r in results:
                if r.get("wrapperType") == "track":
                    return r.get("previewUrl")
            return None
        except Exception:
            return None

    def _map_track(self, r: dict) -> dict:
        art = r.get("artworkUrl100") or r.get("artworkUrl60") or r.get("artworkUrl30")
        if art and "100x100" in art:
            art = art.replace("100x100", "600x600")
        elif art and "60x60" in art:
            art = art.replace("60x60", "600x600")
        elif art and "30x30" in art:
            art = art.replace("30x30", "600x600")

        release_date = r.get("releaseDate")
        release_year = None
        if release_date:
            try:
                release_year = release_date[:4]
            except Exception:
                pass

        return {
            "title": r.get("trackName") or r.get("name"),
            "artist": r.get("artistName"),
            "album": r.get("collectionName"),
            "cover_url": art,
            "preview_url": r.get("previewUrl"),
            "track_id": r.get("trackId"),
            "duration": int(r.get("trackTimeMillis", 0) / 1000) if r.get("trackTimeMillis") else None,
            "genre": r.get("primaryGenreName"),
            "release_date": release_date,
            "release_year": release_year,
        }


__all__ = ["iTunesClient"]
