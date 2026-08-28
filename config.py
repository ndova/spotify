"""Configuration for the Music Downloader application."""


class Config:
    """Central configuration for the app."""

    # Spotify API credentials.
    # Leave empty to disable Spotify features (the app will still work for iTunes).
    # Get them from: https://developer.spotify.com/dashboard
    SPOTIFY_CLIENT_ID = ""
    SPOTIFY_CLIENT_SECRET = ""

    # Folder where downloaded audio files are saved.
    DOWNLOAD_PATH = "./downloads"
