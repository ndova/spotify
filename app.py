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
    page_title="Music Downloader",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Debug panel sementara untuk membantu tracing klik tombol
with st.sidebar.expander("Debug (dev)", expanded=False):
    debug_info = {
        "modal_artist_id": st.session_state.get("modal_artist_id"),
        "modal_artist_name": st.session_state.get("modal_artist_name"),
        "modal_album_id": st.session_state.get("modal_album_id"),
        "modal_album_name": st.session_state.get("modal_album_name"),
        "artist_results_len": len(st.session_state.get("artist_results", [])),
    }
    
    # show last preview debug info if available (but don't expose raw bytes)
    last_preview = st.session_state.get("last_preview_info")
    if last_preview:
        debug_info["last_preview_url"] = last_preview.get("url")
        debug_info["last_preview_len"] = last_preview.get("len")
    last_err = st.session_state.get("last_preview_error")
    
    # render structured debug info
    # include last clicked album for debugging
    last_clicked = st.session_state.get("last_clicked_album")
    if last_clicked:
        debug_info['last_clicked_album_keys'] = list(last_clicked.keys())
    
    debug_info['last_album_fetch_info'] = st.session_state.get('last_album_fetch_info')
    debug_info['last_album_fetch_error'] = st.session_state.get('last_album_fetch_error')
    
    debug_info['last_top_songs_error'] = st.session_state.get('last_top_songs_error')
    debug_info['last_top_songs_diag'] = st.session_state.get('last_top_songs_diag')
    
    st.json(debug_info)
    
    # render preview error separately and user-friendly
    if last_err:
        err_msg = str(last_err)
        if len(err_msg) > 300:
            err_msg = err_msg[:300] + "..."
        st.error(f"Preview error: {err_msg}")
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


# Download format options
if "download_format" not in st.session_state:
    st.session_state.download_format = "mp3"
if "download_bitrate" not in st.session_state:
    st.session_state.download_bitrate = "256"

with st.sidebar:
    st.markdown("**Download options**")
    st.selectbox("Format", ["mp3", "m4a"], key="download_format")
    # Support common bitrates; fixed typo to 256
    st.selectbox("Bitrate (kbps)", ["128", "256"], key="download_bitrate")
    
    st.divider()
    
    if st.button("Perbaiki metadata semua", key="fix_all_metadata"):
        with st.spinner('Memperbaiki metadata...'):
            try:
                # force=True to rewrite metadata even if basic tags exist
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

@st.cache_data(ttl=600, show_spinner="Memuat album artis...")
def get_artist_albums(artist_id: str, limit: int) -> list[dict]:
    return get_itunes_client().get_artist_albums(artist_id, limit)

@st.cache_data(ttl=600, show_spinner="Memuat tangga lagu...")
def get_top_songs(country: str, limit: int) -> list[dict]:
    return get_itunes_client().get_top_songs(country=country, limit=limit)


# --------------------------------------------------------------------------- #
# Komponen bantu
# --------------------------------------------------------------------------- #

def download_via_youtube(track: dict) -> None:
    """Jalankan unduhan YouTube dan tampilkan statusnya."""
    label = f"{track['artist']} - {track['title']}"
    with st.spinner(f"Mengunduh {label}..."):
        fmt = st.session_state.get("download_format", "mp3")
        br = st.session_state.get("download_bitrate", "256")
        
        # pass format and bitrate in track_info for downstream use
        track_copy = dict(track)
        track_copy['format'] = fmt
        track_copy['bitrate'] = br
        
        ok = get_downloader().download_track(track_copy, source='youtube')

    if ok:
        st.success(f"Berhasil diunduh: {label}")
    else:
        st.error(
            f"Gagal mengunduh {label}. "
            "Pastikan FFmpeg terpasang dan koneksi internet stabil."
        )

def render_track_row(track: dict, key_suffix: str) -> None:
    """Tampilkan satu baris lagu: sampul, info, preview, dan tombol unduh."""
    cover, info, action = st.columns([0.7, 3.0, 1.3], vertical_alignment="center")

    with cover:
        if track.get("cover_url"):
            st.image(track["cover_url"], width=160)

    with info:
        st.markdown(f"**{track['title']}**")
        caption = track.get("artist", "")
        if track.get("album"):
            caption += f" — {track['album']}"

        meta = []
        if track.get("duration"):
            meta.append(f"{track['duration'] // 60}:{track['duration'] % 60:02d}")
        if track.get("genre"):
            meta.append(track["genre"])
        if track.get("track_price"):
            meta.append(f"${track['track_price']:.2f}")

        if meta:
            caption += "  |  " + " • ".join(meta)
        st.caption(caption)

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
            on_click=download_via_youtube,
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
    """Tampilkan satu baris album: sampul, info, dan tombol lihat lagu.

    view_prefix:
        'album_search' untuk menu Cari album, kosong untuk penggunaan lain.
        Dipakai untuk membedakan handler tombol.
    """
    cover, info, action = st.columns([0.7, 3.0, 1.3], vertical_alignment="center")

    with cover:
        if album.get("cover_url"):
            st.image(album["cover_url"], width=140)

    with info:
        st.markdown(f"**{album['album']}**")
        st.caption(
            f"{album['artist']} • {album.get('track_count', 0)} lagu"
            f" • {album.get('genre', '')}"
        )

    with action:
        # try multiple possible album id keys for robustness
        album_id = album.get("album_id") or album.get("collectionId") or album.get("collectionId") or album.get("id") or album.get("albumId") or ""
        album_name = album.get("album") or album.get("collectionName") or ""
        str_album_id = str(album_id)
        str_album_name = album_name

        if view_prefix == "album_search":
            st.button(
                "Lihat lagu",
                key=key,
                icon=":material/queue_music:",
                width="stretch",
                on_click=_show_album_search_tracks,
                args=(str_album_id, str_album_name),
            )
        else:
            st.button(
                "Lihat lagu",
                key=key,
                icon=":material/queue_music:",
                width="stretch",
                on_click=_show_album_tracks,
                args=(str_album_id, str_album_name),
            )


def render_tracks(tracks: list[dict], key_prefix: str) -> None:
    """Tampilkan daftar lagu."""
    for i, track in enumerate(tracks):
        with st.container(border=True):
            render_track_row(track, f"{key_prefix}_{i}_{track.get('track_id', '')}")


# --------------------------------------------------------------------------- #
# Navigasi
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.title("🎵 Music Downloader")
    st.caption("Cari & unduh musik dari iTunes dan Spotify.")
    menu = st.radio(
        "Menu",
        ["Cari lagu", "Cari album", "Cari artis", "Tangga lagu"],
        label_visibility="collapsed",
    )

st.title("Music Downloader")
st.caption("Cari lagu, dengarkan cuplikan 30 detik, lalu unduh versi audio.")


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

    # ARTISTS VIEW: tampilkan daftar artis
    if st.session_state.get("current_view", "artists") == "artists":
        artists = st.session_state.get("artist_results", [])
        if artists:
            st.write(f"Ditemukan {len(artists)} artis:")
            for artist in artists:
                with st.container(border=True):
                    c1, c2 = st.columns([3.0, 1.3], vertical_alignment="center")
                    with c1:
                        st.markdown(f"**{artist['artist']}**")
                        if artist.get("genre"):
                            st.caption(artist["genre"])
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