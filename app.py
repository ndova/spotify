"""Music Downloader - antarmuka web berbasis Streamlit. Menjalankan aplikasi: streamlit run app.py"""

import streamlit as st
import requests
import time
import urllib.parse
from config import Config
from downloader import AudioDownloader
from itunes_client import iTunesClient
from spotify_client import SpotifyClient
from lyrics_client import LyricsClient

st.set_page_config(
    page_title="Spotify — Music Downloader",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Spotify-inspired theme ---
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Montserrat:wght@600;700;800&display=swap');
:root {
  --sp-green: #1DB954;
  --sp-green-hover: #1ED760;
  --sp-black: #000000;
  --sp-dark: #121212;
  --sp-card: #181818;
  --sp-card-hover: #282828;
  --sp-elevated: #242424;
  --sp-border: rgba(255,255,255,0.10);
  --sp-muted: #B3B3B3;
  --sp-subtle: #727272;
  --sp-text: #FFFFFF;
}
html, body, [class*="css"] { font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
h1, h2, h3 { font-family: Montserrat, Inter, sans-serif; letter-spacing: -0.02em; }
.block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1180px; }
a { color: var(--sp-green); }
.material-symbols-rounded { font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24; vertical-align: middle; }

/* App background — Spotify dark gradient */
.stApp {
  background: linear-gradient(180deg, #1a1a1a 0%, #121212 40%, #000000 100%) !important;
}

/* Hero — playlist header ala Spotify */
.sv-hero {
  background: linear-gradient(180deg, rgba(29,185,84,0.18) 0%, rgba(18,18,18,0.0) 70%),
              linear-gradient(135deg, #2a2a2a, #181818);
  border: 1px solid var(--sp-border);
  border-radius: 8px;
  padding: 24px 24px 20px 24px;
  margin-bottom: 16px;
  display: flex; gap: 20px; align-items: center;
}
.sv-hero-cover {
  width: 132px; height: 132px; border-radius: 4px; flex-shrink: 0;
  background: linear-gradient(135deg, #3a3a3a, #1a1a1a);
  box-shadow: 0 16px 40px rgba(0,0,0,0.6);
  display:flex; align-items:center; justify-content:center;
  font-size: 52px; color: #fff;
}
.sv-hero-text h1 { font-size: 30px; margin: 0 0 6px 0; color: #fff; font-weight: 800; line-height: 1.1; }
.sv-hero-text .sv-sub { color: var(--sp-muted); font-size: 13px; }
.sv-badge {
  display:inline-flex; align-items:center; gap:6px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
  color: #fff; padding:5px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
}

/* Cards — Spotify card style */
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--sp-card) !important;
  border: 1px solid transparent !important;
  border-radius: 8px !important;
  transition: background 0.2s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
  background: var(--sp-card-hover) !important;
}

/* Sidebar — Spotify left nav (black) */
section[data-testid="stSidebar"] {
  background: #000000 !important;
  border-right: none !important;
}
section[data-testid="stSidebar"] .stRadio label, section[data-testid="stSidebar"] .stSelectbox label { color: #B3B3B3 !important; }
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #B3B3B3; }

/* Buttons — Spotify green primary */
.stButton>button {
  border-radius: 999px !important;
  font-weight: 700 !important;
  font-size: 13px !important;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border: none !important;
  background: var(--sp-green) !important;
  color: #000 !important;
  padding: 10px 20px !important;
  box-shadow: none !important;
}
.stButton>button:hover {
  background: var(--sp-green-hover) !important;
  transform: scale(1.02);
}
.stButton>button:active { transform: scale(0.99); }

/* Secondary buttons (Previous etc) — dark pill */
button[kind="secondary"] {
  background: rgba(255,255,255,0.08) !important;
  color: #fff !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
}

/* Inputs */
div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div[data-baseweb="select"] {
  background: #242424 !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  color: #fff !important;
  border-radius: 8px !important;
}
div[data-testid="stSlider"] { color: #fff; }

/* Table / header row like Spotify tracklist header */
.sp-tracklist-header {
  display:grid; grid-template-columns: 36px 52px 1fr 140px 80px 120px;
  gap: 12px; align-items:center;
  padding: 8px 12px; margin-bottom: 6px;
  border-bottom: 1px solid rgba(255,255,255,0.10);
  color: var(--sp-muted); font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase;
}

[data-testid="stMetric"] { background: var(--sp-card); border: 1px solid var(--sp-border); border-radius: 8px; padding: 10px 12px; color: #fff; }
hr { border-color: rgba(255,255,255,0.08) !important; }
div[data-testid="stExpander"] { background: var(--sp-card); border: 1px solid var(--sp-border); border-radius: 8px; }

/* Chips — Spotify pill subdued */
.sv-chip { display:inline-flex; align-items:center; gap:6px; background: rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.10); color:#fff; padding:4px 10px; border-radius:999px; font-size:11px; font-weight:600; }
.sv-chip-accent { background: var(--sp-green); border-color: var(--sp-green); color:#000; }

/* Hide Streamlit chrome */
header[data-testid="stHeader"] { display: none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDeployButton"] { display: none !important; }
</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,300..700,0..1,-50..200" />
""", unsafe_allow_html=True)
# Klien (di-cache agar tidak dibuat ulang setiap rerun)
@st.cache_resource(show_spinner=False)
def get_itunes_client() -> iTunesClient:
    return iTunesClient()

@st.cache_resource(show_spinner=False)
def get_downloader() -> AudioDownloader:
    return AudioDownloader(Config.DOWNLOAD_PATH)

@st.cache_resource(show_spinner=False)
def get_spotify_client() -> SpotifyClient | None:
    client_id = Config.SPOTIFY_CLIENT_ID or st.secrets.get("SPOTIFY_CLIENT_ID", "")
    client_secret = Config.SPOTIFY_CLIENT_SECRET or st.secrets.get(
        "SPOTIFY_CLIENT_SECRET", ""
    )
    if client_id and client_secret:
        return SpotifyClient(client_id, client_secret)
    return None

@st.cache_resource(show_spinner=False)
def get_lyrics_client() -> LyricsClient:
    return LyricsClient()


# Sidebar minimal — no download options here (moved to per-track dialog)
with st.sidebar:
    if st.button("Perbaiki metadata semua", key="fix_all_metadata"):
        with st.spinner('Memperbaiki metadata...'):
            try:
                res = get_downloader().fix_all_metadata(force=True)
                written = [r['file'] for r in res if r.get('status') == 'written']
                failed = [r for r in res if r.get('status') == 'error']
                skipped = [r['file'] for r in res if r.get('status') == 'skipped']
                st.success(f"Menulis metadata untuk {len(written)} file.")
                if written:
                    st.write('\n'.join(written))
                if skipped:
                    st.info(f"File yang dilewati (sudah lengkap): {len(skipped)}")
                if failed:
                    st.warning(f"Gagal untuk {len(failed)} file; cek log.")
            except Exception as e:
                st.error(f"Perbaikan metadata gagal: {e}")


# --------------------------------------------------------------------------- #
# Klien (di-cache agar tidak dibuat ulang setiap rerun)
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner=False)
def get_itunes_client() -> iTunesClient:
    return iTunesClient()

@st.cache_resource(show_spinner=False)
def get_downloader() -> AudioDownloader:
    return AudioDownloader(Config.DOWNLOAD_PATH)

@st.cache_resource(show_spinner=False)
def get_spotify_client() -> SpotifyClient | None:
    client_id = Config.SPOTIFY_CLIENT_ID or st.secrets.get("SPOTIFY_CLIENT_ID", "")
    client_secret = Config.SPOTIFY_CLIENT_SECRET or st.secrets.get(
        "SPOTIFY_CLIENT_SECRET", ""
    )
    if client_id and client_secret:
        return SpotifyClient(client_id, client_secret)
    return None

@st.cache_resource(show_spinner=False)
def get_lyrics_client() -> LyricsClient:
    return LyricsClient()


# --------------------------------------------------------------------------- #
# Pencarian (di-cache dengan TTL agar cepat untuk query yang sama)
# --------------------------------------------------------------------------- #
@st.cache_data(ttl=600, show_spinner="Mencari di iTunes...")
def search_tracks(query: str, limit: int) -> list[dict]:
    return get_itunes_client().search_tracks(query, limit)

@st.cache_data(ttl=600, show_spinner="Mencari album di iTunes...")
def search_albums(query: str, limit: int) -> list[dict]:
    return get_itunes_client().search_albums(query, limit)

@st.cache_data(ttl=600, show_spinner="Memuat lagu dari album...")
def get_album_tracks(album_id: str) -> list[dict]:
    return get_itunes_client().get_album_tracks(album_id)

@st.cache_data(ttl=600, show_spinner="Mencari artis di iTunes...")
def search_artists(query: str, limit: int) -> list[dict]:
    return get_itunes_client().search_artists(query, limit)

def clear_artist_cache():
    """Clear cached search_artists so updated cover logic takes effect."""
    try:
        search_artists.clear()
    except Exception:
        pass

@st.cache_data(ttl=600, show_spinner="Memuat album artis...")
def get_artist_albums(artist_id: str, limit: int) -> list[dict]:
    return get_itunes_client().get_artist_albums(artist_id, limit)

@st.cache_data(ttl=600, show_spinner="Memuat tangga lagu...")
def get_top_songs(country: str, limit: int) -> list[dict]:
    return get_itunes_client().get_top_songs(country=country, limit=limit)


# --------------------------------------------------------------------------- #
# Komponen bantu
# --------------------------------------------------------------------------- #

def _open_download_dialog(track: dict) -> None:
    """Buka dialog pilihan format/bitrate untuk track yang akan diunduh."""
    # store a copy without mutating original track dict
    st.session_state.pending_download = dict(track)

@st.dialog("Download — pilih format")
def _download_dialog():
    track = st.session_state.get("pending_download")
    if not track:
        st.info("Tidak ada lagu yang dipilih.")
        return
    st.markdown(f"**{track.get('artist','')} — {track.get('title','')}**")
    if track.get("album"):
        st.caption(track.get("album"))

    fmt = st.selectbox("Format", ["mp3", "m4a"], key="dlg_download_format", index=0)
    br = st.selectbox("Bitrate (kbps)", ["128", "256"], key="dlg_download_bitrate", index=1)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Mulai download", width="stretch", icon=":material/download:"):
            title = track.get('title','')
            artist = track.get('artist','')
            with st.spinner(f"Mengunduh {artist} — {title}..."):
                track_copy = dict(track)
                track_copy["format"] = fmt
                track_copy["bitrate"] = br
                ok = get_downloader().download_track(track_copy, source="youtube")
            # close dialog first so popup tidak menggantung
            st.session_state.pending_download = None
            if ok:
                st.session_state.download_toast = f"Berhasil diunduh: {artist} — {title}"
            else:
                st.session_state.download_toast = None
                st.session_state.download_error = f"Gagal mengunduh {artist} — {title}. Pastikan FFmpeg terpasang dan koneksi stabil."
            st.rerun()
    with c2:
        if st.button("Batal", width="stretch"):
            st.session_state.pending_download = None
            st.rerun()

# Auto-open dialog when a track is selected
if st.session_state.get("pending_download"):
    _download_dialog()

def download_via_youtube(track: dict) -> None:
    """Jalankan unduhan dengan opsi dari dialog (dipanggil hanya dari dialog)."""
    label = f"{track['artist']} - {track['title']}"
    with st.spinner(f"Mengunduh {label}..."):
        fmt = track.get("format") or st.session_state.get("dlg_download_format", "mp3")
        br = track.get("bitrate") or st.session_state.get("dlg_download_bitrate", "256")
        track_copy = dict(track)
        track_copy["format"] = fmt
        track_copy["bitrate"] = br
        ok = get_downloader().download_track(track_copy, source="youtube")
    if ok:
        st.success(f"Berhasil diunduh: {label}")
    else:
        st.error(f"Gagal mengunduh {label}. Pastikan FFmpeg terpasang dan koneksi internet stabil.")

def render_track_row(track: dict, key_suffix: str) -> None:
    """Spotify track row — dark card, muted meta, green play affordance."""
    cover, info, action = st.columns([0.7, 3.0, 1.3], vertical_alignment="center")
    with cover:
        if track.get("cover_url"):
            st.markdown(
                f'<div style="width:56px;height:56px;border-radius:4px;overflow:hidden;background:#181818;box-shadow:0 4px 16px rgba(0,0,0,0.4)"><img src="{track["cover_url"]}" style="width:100%;height:100%;object-fit:cover; display:block;" /></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div style="width:56px;height:56px;border-radius:4px;background:#282828;display:flex;align-items:center;justify-content:center;color:#727272"><span class="material-symbols-rounded" style="font-size:28px;">music_note</span></div>', unsafe_allow_html=True)
    with info:
        st.markdown(f"<div style='font-weight:600; font-size:14px; line-height:1.25; color:#FFFFFF; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{track['title']}</div>", unsafe_allow_html=True)
        caption = track.get("artist", "")
        if track.get("album"):
            caption += f" <span style='color:#727272'>•</span> <span style='color:#B3B3B3'>{track['album']}</span>"
        st.markdown(f"<div style='color:#B3B3B3; font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{caption}</div>", unsafe_allow_html=True)
        meta = []
        if track.get("duration"):
            meta.append(f"{track['duration'] // 60}:{track['duration'] % 60:02d}")
        if track.get("genre"):
            meta.append(track["genre"])
        if meta:
            chips = " ".join([f"<span class='sv-chip'>{m}</span>" for m in meta])
            st.markdown(f"<div style='margin-top:6px'>{chips}</div>", unsafe_allow_html=True)

        if track.get("preview_url"):
            preview_bytes, preview_err = _fetch_preview_bytes(track["preview_url"])
            st.session_state.last_preview_info = {"url": track.get("preview_url"), "len": len(preview_bytes) if preview_bytes else 0}
            st.session_state.last_preview_error = preview_err
            
            if preview_bytes:
                st.audio(preview_bytes, format="audio/mp4")
            else:
                st.caption("Preview tidak tersedia")
                if preview_err:
                    st.caption(f"Preview error: {preview_err}")
                    
        # Lirik: tampilkan jika tersedia atau ambil via provider
        with st.expander("Lirik", expanded=False):
            lyrics = track.get('lyrics')
            if not lyrics:
                with st.spinner('Mencari lirik...'):
                    lc = get_lyrics_client()
                    l = lc.fetch_lyrics(track.get('artist', ''), track.get('title', ''))
                    if l:
                        track['lyrics'] = l
                        lyrics = l
            if lyrics:
                st.text(lyrics)
            else:
                st.caption('Lirik tidak ditemukan')

    with action:
        st.button(
            "Download",
            key=f"dl_{key_suffix}",
            icon=":material/download:",
            width="stretch",
            on_click=_open_download_dialog,
            args=(track,),
        )

def _select_artist(artist_id: str, artist_name: str) -> None:
    """Simpan artis terpilih dan reset album terpilih."""
    st.session_state.selected_artist = artist_id
    st.session_state.selected_artist_name = artist_name
    st.session_state.selected_album = ""

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_preview_bytes(url: str) -> tuple[bytes | None, str | None]:
    """Fetch preview audio bytes server-side and cache them.
    Returns tuple (content_bytes or None, error_message or None).
    """
    if not url:
        return None, "no url"
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116 Safari/537.36",
        "Referer": "https://music.apple.com/",
    }
    try:
        resp = requests.get(url, timeout=10, headers=headers, stream=True)
        resp.raise_for_status()
        content = resp.content
        if not content:
            return None, "empty content"
        if len(content) > 5_000_000:
            return None, "content too large"
        return content, None
    except Exception as e:
        return None, str(e)

def _open_artist_modal(artist_id: str, artist_name: str) -> None:
    """Tandai agar modal album artis dibuka pada rerun berikutnya."""
    st.session_state.modal_artist_id = artist_id
    st.session_state.modal_artist_name = artist_name


def _open_album_modal(album_id: str, album_name: str) -> None:
    """Tandai agar modal lagu album dibuka pada rerun berikutnya."""
    st.session_state.modal_album_id = album_id
    st.session_state.modal_album_name = album_name


def _clear_artist_selection() -> None:
    """Reset artis & album terpilih saat kueri pencarian berubah."""
    st.session_state.selected_artist = ""
    st.session_state.selected_artist_name = ""
    st.session_state.selected_album = ""
    st.session_state.artist_results = []


def _perform_artist_search() -> None:
    """Execute artist search and store results in session state."""
    query = st.session_state.get("artist_query", "")
    limit = st.session_state.get("artist_limit", 5)
    if not query:
        st.session_state.artist_results = []
        return
    st.session_state.artist_results = search_artists(query, limit)
    st.session_state.selected_artist = ""
    st.session_state.selected_artist_name = ""
    st.session_state.selected_album = ""


def _push_view(state: dict) -> None:
    """Push current view state to stack for Previous navigation."""
    stack = st.session_state.get("view_stack", [])
    # store a shallow copy of state
    stack.append(state)
    st.session_state.view_stack = stack

def _pop_view() -> None:
    """Pop previous view state and restore it."""
    stack = st.session_state.get("view_stack", [])
    if not stack:
        # fallback: reset both navigations
        st.session_state.current_view = "artists"
        st.session_state.album_search_view = "album_results"
        return
    last = stack.pop()
    st.session_state.view_stack = stack

    # restore depending on saved type
    view_type = last.get("view", "artists")
    st.session_state.current_view = view_type

    if view_type == "artists":
        st.session_state.artist_results = last.get("artist_results", [])
        st.session_state.artist_query = last.get("artist_query", "")
    elif view_type == "albums":
        st.session_state.current_artist_id = last.get("artist_id", "")
        st.session_state.current_artist_name = last.get("artist_name", "")
        st.session_state.artist_albums = last.get("artist_albums", [])
    elif view_type == "album_tracks":
        st.session_state.current_album_id = last.get("album_id", "")
        st.session_state.current_album_name = last.get("album_name", "")
        st.session_state.album_tracks = last.get("album_tracks", [])
    elif view_type == "album_results":
        st.session_state.album_search_view = "album_results"
        st.session_state.album_results = last.get("album_results", [])
        st.session_state.album_query = last.get("album_query", "")
    elif view_type == "album_search_tracks":
        st.session_state.album_search_view = "album_search_tracks"
        st.session_state.album_search_album_id = last.get("album_id", "")
        st.session_state.album_search_album_name = last.get("album_name", "")
        st.session_state.album_search_tracks = last.get("album_tracks", [])


def _show_artist_albums(artist_id: str, artist_name: str) -> None:
    """Tampilkan album artis menggantikan daftar artis (push previous)."""
    # push current artists view
    _push_view(
        {
            "view": "artists",
            "artist_results": st.session_state.get("artist_results", []),
            "artist_query": st.session_state.get("artist_query", ""),
        }
    )
    
    st.session_state.current_view = "albums"
    st.session_state.current_artist_id = artist_id
    st.session_state.current_artist_name = artist_name
    st.session_state.artist_albums = get_artist_albums(artist_id, 50)


def _show_album_tracks(album_id: str, album_name: str) -> None:
    """Tampilkan lagu album menggantikan daftar album (push previous)."""
    _push_view(
        {
            "view": "albums",
            "artist_id": st.session_state.get("current_artist_id", ""),
            "artist_name": st.session_state.get("current_artist_name", ""),
            "artist_albums": st.session_state.get("artist_albums", []),
        }
    )
    
    st.session_state.current_view = "album_tracks"
    st.session_state.current_album_id = album_id
    st.session_state.current_album_name = album_name
    
    # try cached fetch first
    tracks = get_album_tracks(album_id)
    
    # if cached fetch returned empty, try direct client call (fallback)
    if not tracks:
        try:
            client = get_itunes_client()
            direct = client.get_album_tracks(album_id)
            if direct:
                tracks = direct
        except Exception as e:
            # store debug info for investigation
            st.session_state.last_album_fetch_error = str(e)
            
    # additional fallback: search tracks by album name and filter
    if not tracks and album_name:
        try:
            candidates = search_tracks(album_name, limit=200)
            filtered = []
            for t in candidates:
                # match by album name or collection id if available
                if (t.get('album') and album_name.lower() in t.get('album','').lower()) or str(t.get('collectionId','')) == str(album_id):
                    filtered.append(t)
            if filtered:
                tracks = filtered
        except Exception as e:
            st.session_state.last_album_search_fallback_error = str(e)

    st.session_state.album_tracks = tracks or []
    # also record debug info about album fetch
    st.session_state.last_album_fetch_info = {"album_id": album_id, "len": len(st.session_state.album_tracks)}


def _open_album_and_show(album: dict) -> None:
    """Store clicked album for debugging and call _show_album_tracks with a robust id."""
    st.session_state.last_clicked_album = album
    # determine album id from common keys
    album_id = album.get("album_id") or album.get("collectionId") or album.get("id") or album.get("albumId") or ""
    album_name = album.get("album") or album.get("collectionName") or ""
    _show_album_tracks(str(album_id), album_name)


# Handler dedicated untuk menu "Cari album" — view terpisah (menggantikan daftar album)
def _show_album_search_tracks(album_id: str, album_name: str) -> None:
    # push view album_results
    _push_view(
        {
            "view": "album_results",
            "album_results": st.session_state.get("album_results", []),
            "album_query": st.session_state.get("album_query", ""),
        }
    )
    st.session_state.album_search_view = "album_search_tracks"
    st.session_state.album_search_album_id = str(album_id)
    st.session_state.album_search_album_name = album_name

    # fetch tracks (reuse logic: cached + fallback)
    tracks = get_album_tracks(str(album_id))
    if not tracks:
        try:
            client = get_itunes_client()
            direct = client.get_album_tracks(str(album_id))
            if direct:
                tracks = direct
        except Exception as e:
            st.session_state.last_album_fetch_error = str(e)
    if not tracks and album_name:
        try:
            candidates = search_tracks(album_name, limit=200)
            filtered = []
            for t in candidates:
                if (t.get("album") and album_name.lower() in t.get("album", "").lower()) or str(t.get("collectionId", "")) == str(album_id):
                    filtered.append(t)
            if filtered:
                tracks = filtered
        except Exception as e:
            st.session_state.last_album_search_fallback_error = str(e)

    st.session_state.album_search_tracks = tracks or []
    st.session_state.last_album_fetch_info = {"album_id": str(album_id), "len": len(st.session_state.album_search_tracks)}

    # sinkronkan juga ke selected_* untuk kompatibilitas lama
    st.session_state.selected_album = str(album_id)
    st.session_state.selected_album_name = album_name


def _pop_album_search_view() -> None:
    """Kembali dari album_search_tracks ke album_results."""
    stack = st.session_state.get("view_stack", [])
    # cari entry album_results terakhir dari stack
    for idx in range(len(stack) - 1, -1, -1):
        if stack[idx].get("view") == "album_results":
            last = stack.pop(idx)
            st.session_state.view_stack = stack
            st.session_state.album_search_view = "album_results"
            st.session_state.album_results = last.get("album_results", [])
            st.session_state.album_query = last.get("album_query", "")
            return
    # fallback: gunakan _pop_view
    _pop_view()
    if st.session_state.get("album_search_view") != "album_search_tracks":
        return
    st.session_state.album_search_view = "album_results"


def render_album_row(album: dict, key: str, *, view_prefix: str = "") -> None:
    """Spotify album row — square cover, subtle meta."""
    cover, info, action = st.columns([0.7, 3.0, 1.3], vertical_alignment="center")
    with cover:
        if album.get("cover_url"):
            st.markdown(
                f'<div style="width:56px;height:56px;border-radius:4px;overflow:hidden;background:#181818;box-shadow:0 4px 16px rgba(0,0,0,0.4)"><img src="{album["cover_url"]}" style="width:100%;height:100%;object-fit:cover;display:block;" /></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div style="width:56px;height:56px;border-radius:4px;background:#282828;display:flex;align-items:center;justify-content:center;color:#727272"><span class="material-symbols-rounded">album</span></div>', unsafe_allow_html=True)
    with info:
        st.markdown(f"<div style='font-weight:600; font-size:14px; color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{album['album']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='color:#B3B3B3; font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{album['artist']} <span style='color:#727272'>•</span> {album.get('track_count', 0)} lagu <span style='color:#727272'>•</span> {album.get('genre', '')}</div>", unsafe_allow_html=True)
        if album.get("release_year"):
            st.markdown(f"<div style='margin-top:4px'><span class='sv-chip'>{album['release_year']}</span></div>", unsafe_allow_html=True)
    with action:
        album_id = album.get("album_id") or album.get("collectionId") or album.get("collectionId") or album.get("id") or album.get("albumId") or ""
        album_name = album.get("album") or album.get("collectionName") or ""
        str_album_id = str(album_id)
        str_album_name = album_name
        if view_prefix == "album_search":
            st.button("Lihat lagu", key=key, icon=":material/queue_music:", width="stretch", on_click=_show_album_search_tracks, args=(str_album_id, str_album_name))
        else:
            st.button("Lihat lagu", key=key, icon=":material/queue_music:", width="stretch", on_click=_show_album_tracks, args=(str_album_id, str_album_name))


def render_tracks(tracks: list[dict], key_prefix: str) -> None:
    """Tampilkan daftar lagu."""
    for i, track in enumerate(tracks):
        with st.container(border=True):
            render_track_row(track, f"{key_prefix}_{i}_{track.get('track_id', '')}")


# --------------------------------------------------------------------------- #
# Navigasi
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
            <div style="width:32px;height:32px;border-radius:50%;background:#1DB954;display:flex;align-items:center;justify-content:center;color:#000;font-weight:900; font-size:16px;">♫</div>
            <div>
                <div style="font-weight:800; font-size:15px; line-height:1; color:#fff; letter-spacing:-0.02em;">Spotify</div>
                <div style="font-size:10px; color:#B3B3B3; letter-spacing:0.12em; text-transform:uppercase;">Downloader</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    menu = st.radio(
        "Menu",
        ["Cari lagu", "Cari album", "Cari artis", "Tangga lagu"],
        label_visibility="collapsed",
    )
    st.markdown("<div style='margin-top:10px; padding:10px 12px; background:#181818; border-radius:8px; border:1px solid rgba(255,255,255,0.06);'><div style='color:#fff; font-weight:600; font-size:12px; margin-bottom:4px;'><span class='material-symbols-rounded' style='font-size:14px; vertical-align:middle;'>lightbulb</span> Tips</div><div style='font-size:11px; color:#B3B3B3; line-height:1.4;'>Gunakan kata kunci spesifik untuk hasil lebih akurat.</div></div>", unsafe_allow_html=True)
    st.divider()
    if st.button("🧹 Bersihkan cache", key="clear_cache_btn"):
        try:
            search_tracks.clear()
            search_albums.clear()
            get_album_tracks.clear()
            search_artists.clear()
            get_artist_albums.clear()
            get_top_songs.clear()
            st.cache_data.clear()
            st.cache_resource.clear()
        except Exception:
            pass
        st.success("Cache dibersihkan — silakan cari lagi.")
        st.rerun()

HERO_TITLE = {
    "Cari lagu": ("Cari Lagu", "Temukan track favorit, preview 30 detik, dan unduh instan.", "search"),
    "Cari album": ("Jelajahi Album", "Buka album untuk melihat daftar lagu.", "album"),
    "Cari artis": ("Telusuri Artis", "Lihat diskografi artis dan buka albumnya.", "person_search"),
    "Tangga lagu": ("Tangga Lagu", "Lagu terpopuler — segarkan untuk update terbaru.", "leaderboard"),
}
hero_title, hero_desc, hero_icon = HERO_TITLE.get(menu, ("Spotify", "Cari & unduh musik lebih cepat.", "music_note"))
st.markdown(f"""
<div class="sv-hero">
  <div class="sv-hero-cover"><span class="material-symbols-rounded" style="font-size:56px;">{hero_icon}</span></div>
  <div class="sv-hero-text">
    <div class="sv-badge"><span class="material-symbols-rounded" style="font-size:14px;">graphic_eq</span> Spotify • Playlist</div>
    <h1>{hero_title}</h1>
    <div class="sv-sub">{hero_desc}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Toast after download (dialog auto-closed): show success/error outside dialog
if st.session_state.get("download_toast"):
    st.toast(st.session_state.download_toast, icon="✅")
    st.success(st.session_state.download_toast)
    st.session_state.download_toast = None
if st.session_state.get("download_error"):
    st.error(st.session_state.download_error)
    st.session_state.download_error = None


# --------------------------------------------------------------------------- #
# 1) Cari lagu di iTunes
# --------------------------------------------------------------------------- #
if menu == "Cari lagu":
    st.subheader("Cari lagu di iTunes")
    q_col, l_col = st.columns([3, 1])
    with q_col:
        query = st.text_input("Judul lagu atau artis", placeholder="mis. The Beatles")
    with l_col:
        limit = st.slider("Jumlah hasil", 5, 50, 10)

    if query:
        tracks = search_tracks(query, limit)
        if tracks:
            st.write(f"Ditemukan {len(tracks)} lagu:")
            for i, track in enumerate(tracks):
                with st.container(border=True):
                    render_track_row(track, f"track_{i}_{track.get('track_id', '')}")
        else:
            st.info("Tidak ada hasil untuk pencarian tersebut.")


# --------------------------------------------------------------------------- #
# 2) Cari album di iTunes — view terpisah seperti Cari artis
# --------------------------------------------------------------------------- #
elif menu == "Cari album":
    st.subheader("Cari album di iTunes")

    # handler untuk sync hasil pencarian album tanpa memodifikasi widget key langsung
    def _perform_album_search() -> None:
        q = st.session_state.get("album_query", "")
        lim = st.session_state.get("album_limit", 5)
        if not q:
            st.session_state.album_results = []
            return
        st.session_state.album_results = search_albums(q, lim)
        # reset view ke hasil
        st.session_state.album_search_view = "album_results"

    q_col, l_col = st.columns([3, 1])
    with q_col:
        st.text_input(
            "Nama album atau artis",
            key="album_query",
            on_change=_perform_album_search,
            placeholder="Ketik nama album lalu tekan Enter",
        )
    with l_col:
        st.slider("Jumlah album", 3, 20, 5, key="album_limit", on_change=_perform_album_search)

    # pastikan view default
    if "album_search_view" not in st.session_state:
        st.session_state.album_search_view = "album_results"
    if "album_results" not in st.session_state:
        st.session_state.album_results = []

    # VIEW: daftar album (menggantikan dropdown lama)
    if st.session_state.get("album_search_view", "album_results") == "album_results":
        albums = st.session_state.get("album_results", [])

        if albums:
            st.write(f"Ditemukan {len(albums)} album:")
            for album in albums:
                with st.container(border=True):
                    render_album_row(
                        album,
                        f"album_{album.get('album_id', '')}",
                        view_prefix="album_search",
                    )
        else:
            if st.session_state.get("album_query"):
                st.info("Tidak ada album untuk pencarian tersebut.")
            else:
                st.info("Ketik kata kunci untuk mencari album.")

    # VIEW: lagu dalam album (menggantikan daftar album)
    elif st.session_state.get("album_search_view") == "album_search_tracks":
        st.button("Previous", on_click=_pop_album_search_view, icon=":material/arrow_back:", key="back_to_albums_new")
        album_name = st.session_state.get("album_search_album_name", "Album")
        st.subheader(f"Lagu dalam {album_name}")

        album_tracks = st.session_state.get("album_search_tracks", [])
        # fallback fetch jika state kosong (mis. direct navigation)
        if not album_tracks and st.session_state.get("album_search_album_id"):
            album_tracks = get_album_tracks(st.session_state.album_search_album_id)
            st.session_state.album_search_tracks = album_tracks or []

        if album_tracks:
            render_tracks(album_tracks, "alb_search_track")
        else:
            st.info("Tidak ada lagu ditemukan untuk album ini.")
            last_err = st.session_state.get("last_album_fetch_error")
            if last_err:
                st.caption(f"Info: {str(last_err)[:200]}")


# --------------------------------------------------------------------------- #
# 3) Cari artis di iTunes
# --------------------------------------------------------------------------- #
elif menu == "Cari artis":
    st.subheader("Cari artis di iTunes")

    q_col, l_col = st.columns([3, 1])
    with q_col:
        query = st.text_input(
            "Nama artis",
            key="artist_query",
            on_change=_perform_artist_search,
            placeholder="Ketik nama artis lalu tekan Enter",
        )
    with l_col:
        limit = st.slider("Jumlah artis", 3, 20, 5, key="artist_limit")

    # Pastikan view default
    if "current_view" not in st.session_state:
        st.session_state.current_view = "artists"

    # ARTISTS VIEW: tampilkan artis sebagai kartu ala Spotify (dengan thumbnail)
    if st.session_state.get("current_view", "artists") == "artists":
        artists = st.session_state.get("artist_results", [])
        if artists:
            st.write(f"Ditemukan {len(artists)} artis:")
            for artist in artists:
                with st.container(border=True):
                    c0, c1, c2 = st.columns([0.7, 3.0, 1.3], vertical_alignment="center")
                    with c0:
                        cover = artist.get("cover_url")
                        if cover:
                            st.markdown(
                                f'<div style="width:56px;height:56px;border-radius:4px;overflow:hidden;background:#181818;box-shadow:0 4px 16px rgba(0,0,0,0.4)"><img src="{cover}" style="width:100%;height:100%;object-fit:cover;display:block;" /></div>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                '<div style="width:56px;height:56px;border-radius:4px;background:#282828;display:flex;align-items:center;justify-content:center;color:#727272"><span class="material-symbols-rounded" style="font-size:28px;">person</span></div>',
                                unsafe_allow_html=True,
                            )
                    with c1:
                        st.markdown(f"<div style='font-weight:700; font-size:14px; color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{artist['artist']}</div>", unsafe_allow_html=True)
                        if artist.get("genre"):
                            st.markdown(f"<div style='color:#B3B3B3; font-size:12px;'><span class='sv-chip'>{artist['genre']}</span></div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='color:#727272; font-size:12px;'>Artis</div>", unsafe_allow_html=True)
                    with c2:
                        st.button(
                            "Lihat album",
                            key=f"artist_{artist.get('artist_id', '')}",
                            icon=":material/album:",
                            width="stretch",
                            on_click=_show_artist_albums,
                            args=(artist.get("artist_id", ""), artist.get("artist", "")),
                        )
        else:
            st.info("Tidak ada artis untuk pencarian tersebut.")

    # ALBUMS VIEW: menggantikan hasil artis
    elif st.session_state.get("current_view") == "albums":
        st.button("Previous", on_click=_pop_view, icon=":material/arrow_back:")
        st.subheader(f"Album dari {st.session_state.get('current_artist_name', '')}")
        
        artist_albums = st.session_state.get("artist_albums", [])
        if artist_albums:
            for album in artist_albums:
                with st.container(border=True):
                    render_album_row(album, f"artist_album_{album.get('album_id', '')}")
        else:
            st.info("Tidak ada album ditemukan untuk artis ini.")

    # ALBUM TRACKS VIEW: menggantikan daftar album
    elif st.session_state.get("current_view") == "album_tracks":
        st.button("Previous", on_click=_pop_view, icon=":material/arrow_back:")
        st.subheader(f"Lagu dalam {st.session_state.get('current_album_name', '')}")
        
        album_tracks = st.session_state.get("album_tracks", [])
        if album_tracks:
            render_tracks(album_tracks, "artist_album_track")
        else:
            st.info("Tidak ada lagu ditemukan untuk album ini.")

# --------------------------------------------------------------------------- #
# 4) Tangga lagu
# --------------------------------------------------------------------------- #
elif menu == "Tangga lagu":
    st.subheader("Tangga lagu terpopuler")
    c_col, l_col = st.columns([1, 1])
    with c_col:
        country = st.selectbox("Negara", ["US", "ID", "GB", "JP", "AU"], index=0)
    with l_col:
        limit = st.slider("Jumlah lagu", 5, 50, 10, key="top_limit")

    if st.button("Muat tangga lagu", icon=":material/refresh:", width="stretch"):
        max_retries = 3
        base_delay = 1
        diagnostics = {}
        
        st.session_state.top_songs = []
        client = get_itunes_client()
        
        for attempt in range(1, max_retries + 1):
            try:
                # call client directly to bypass cached wrapper so retries actually hit the network
                st.session_state.top_songs = client.get_top_songs(country=country, limit=limit)
                print(f"[top_songs] attempt={attempt} fetched_len={len(st.session_state.top_songs)}")
                
                st.session_state.last_top_songs_error = None
                
                # if we got results, break out early
                if st.session_state.top_songs:
                    diagnostics['attempts'] = attempt
                    st.session_state.last_top_songs_diag = diagnostics
                    break
                
                # empty result -> collect per-attempt diag
                diag = {}
                try:
                    primary = f"https://rss.itunes.apple.com/api/v1/{country}/itunes/top-songs/{limit}/explicit.json"
                    r = requests.get(primary, timeout=8)
                    diag['primary_status'] = r.status_code
                    try:
                        diag['primary_len'] = len(r.json().get('feed', {}).get('results', []))
                    except Exception:
                        diag['primary_len'] = None
                except Exception as e:
                    diag['primary_error'] = str(e)
                    
                try:
                    alt = f"https://itunes.apple.com/{country.lower()}/rss/topsongs/limit={limit}/json"
                    r2 = requests.get(alt, timeout=8)
                    diag['alt_status'] = r2.status_code
                    try:
                        diag['alt_len'] = len(r2.json().get('feed', {}).get('entry', []))
                    except Exception:
                        diag['alt_len'] = None
                except Exception as e:
                    diag['alt_error'] = str(e)
                    
                diagnostics[f'attempt_{attempt}'] = diag
                print(f"[top_songs] attempt={attempt} diag={diag}")
                
                # if not last attempt, wait with exponential backoff
                if attempt < max_retries:
                    wait = base_delay * (2 ** (attempt - 1))
                    st.info(f"Retrying ({attempt}/{max_retries}) in {wait}s...")
                    time.sleep(wait)
                    
            except Exception as e:
                st.session_state.top_songs = []
                st.session_state.last_top_songs_error = str(e)
                diagnostics[f'error_attempt_{attempt}'] = str(e)
                print(f"[top_songs] attempt={attempt} error={e}")
                
                if attempt < max_retries:
                    wait = base_delay * (2 ** (attempt - 1))
                    st.info(f"Error on attempt {attempt}, retrying in {wait}s...")
                    time.sleep(wait)
                    
        # after retries, if still empty, surface diagnostic
        if not st.session_state.top_songs:
            st.session_state.last_top_songs_diag = diagnostics
            st.warning("Tidak ada lagu ditemukan. API mungkin sedang tidak tersedia. Lihat Debug -> last_top_songs_diag untuk detail.")

    if st.session_state.get("top_songs"):
        tracks = st.session_state.top_songs
        st.write(f"Menampilkan {len(tracks)} lagu teratas:")
        for i, track in enumerate(tracks):
            # Tangga lagu tidak menyertakan URL preview; ambil saat dibutuhkan.
            if not track.get("preview_url") and track.get("track_id"):
                track["preview_url"] = get_itunes_client().get_track_preview(
                    track["track_id"]
                )
            with st.container(border=True):
                render_track_row(track, f"top_{i}_{track.get('track_id', '')}")


# --------------------------------------------------------------------------- #
# Sidebar panel: tampilkan album/artis atau lagu (fallback jika modal tidak tersedia)
# --------------------------------------------------------------------------- #
if st.session_state.get("modal_artist_id"):
    with st.sidebar.expander(f"Album dari {st.session_state.get('modal_artist_name','')}", expanded=True):
        artist_albums = get_artist_albums(st.session_state.modal_artist_id, 50)
        if artist_albums:
            for album in artist_albums:
                with st.container(border=True):
                    render_album_row(album, f"side_artist_album_{album.get('album_id','')}")
        else:
            st.info("Tidak ada album ditemukan untuk artis ini.")
    st.session_state.pop("modal_artist_id", None)
    st.session_state.pop("modal_artist_name", None)


if st.session_state.get("modal_album_id"):
    with st.sidebar.expander(
        f"Lagu dalam {st.session_state.get('modal_album_name','')}", expanded=True
    ):
        album_tracks = get_album_tracks(st.session_state.get("modal_album_id"))
        if album_tracks:
            for track in album_tracks:
                with st.container(border=True):
                    render_track_row(track, f"side_album_track_{track.get('track_id','')}")
        else:
            st.info("Tidak ada lagu ditemukan untuk album ini.")
    st.session_state.pop("modal_album_id", None)
    st.session_state.pop("modal_album_name", None)