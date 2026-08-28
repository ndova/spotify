import yt_dlp
import os
import json
import requests
from typing import Dict, Optional
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TCON, TDRC
from mutagen.id3 import ID3NoHeaderError, USLT
from mutagen.mp4 import MP4, MP4Cover, MP4Tags
from itunes_client import iTunesClient
from lyrics_client import LyricsClient
import shutil


def _resolve_ffmpeg_location() -> Optional[str]:
    """Return the directory containing ffmpeg/ffprobe, or None to use PATH."""
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return None
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg")
    if os.path.isdir(base):
        for root, _dirs, files in os.walk(base):
            if "ffmpeg.exe" in files and "ffprobe.exe" in files:
                return root
    return None


class AudioDownloader:
    def __init__(self, download_path: str = './downloads'):
        """Initialize downloader with download path"""
        self.download_path = download_path
        os.makedirs(download_path, exist_ok=True)
        
        # YouTube download options
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'ffmpeg_location': _resolve_ffmpeg_location(),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'noplaylist': True,
            'cachedir': False,
            'socket_timeout': 30,
            'retries': 5,
        }
    
    def download_track(self, track_info: Dict, source: str = 'youtube') -> bool:
        """Download a single track from various sources"""
        if source == 'itunes_preview':
            return self.download_itunes_preview(track_info)
        else:
            # default format/bitrate can be overridden by passing in track_info keys
            fmt = track_info.get('format', 'mp3')
            bitrate = track_info.get('bitrate', '256')
            return self.download_from_youtube(track_info, fmt=fmt, bitrate=bitrate)
    
    def download_from_youtube(self, track_info: Dict, fmt: str = 'mp3', bitrate: str = '256') -> bool:
        """Download a track from YouTube"""
        try:
            # Search for the track on YouTube
            search_query = f"{track_info['artist']} - {track_info['title']} audio"
            print(f"\n🔍 Searching YouTube: {search_query}")
            
            # Get the best matching YouTube video
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                try:
                    info = ydl.extract_info(f"ytsearch1:{search_query}", download=False)
                    if 'entries' in info and info['entries']:
                        video = info['entries'][0]
                    else:
                        video = info
                except Exception:
                    # Try without artist name
                    info = ydl.extract_info(f"ytsearch1:{track_info['title']} audio", download=False)
                    if 'entries' in info and info['entries']:
                        video = info['entries'][0]
                    else:
                        video = info
            
            video_url = video['webpage_url']
            video_title = video.get('title', track_info['title'])
            
            # Update download options for this specific track (copy base opts)
            safe_title = self._safe_filename(track_info['title'])
            opts = dict(self.ydl_opts)
            # create a deep copy of postprocessors to mutate per-download
            post = []
            for p in self.ydl_opts.get('postprocessors', []):
                post.append(dict(p))
            # set codec/quality according to requested fmt and bitrate
            if post:
                post[0]['preferredcodec'] = fmt
                post[0]['preferredquality'] = str(bitrate)
            opts['postprocessors'] = post
            # set ffmpeg postprocessor args to force bitrate
            # yt-dlp expects a list of args for `postprocessor_args` (not a dict)
            # e.g. ['-b:a', '256k']
            try:
                br_value = int(bitrate)
            except Exception:
                br_value = int(str(bitrate).strip() or 256)
            opts['postprocessor_args'] = ['-b:a', f"{br_value}k"]
            opts['outtmpl'] = os.path.join(self.download_path, f'{safe_title}.%(ext)s')
            
            print(f"⬇️  Downloading: {video_title}")
            print(f"  -> outtmpl: {opts['outtmpl']}")
            print(f"  -> safe_title: {safe_title}")
            
            # Download the audio
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([video_url])
            
            # After download, find the actual output file produced by yt-dlp
            possible_exts = ['mp3', 'm4a', 'm4b', 'aac', 'wav', 'ogg', 'opus']
            out_path = None
            for ext in possible_exts:
                candidate = os.path.join(self.download_path, f"{safe_title}.{ext}")
                print(f"    checking candidate: {candidate}")
                if os.path.exists(candidate):
                    print(f"    found -> {candidate}")
                    out_path = candidate
                    break

            if out_path is None:
                # try to find any file starting with the safe_title
                print("    no explicit candidate found, scanning download dir for matching files")
                for fname in os.listdir(self.download_path):
                    print(f"      scan -> {fname}")
                    if fname.startswith(safe_title):
                        out_path = os.path.join(self.download_path, fname)
                        print(f"      matched -> {out_path}")
                        break

            if out_path and os.path.exists(out_path):
                # If metadata is missing, try to enrich it from iTunes
                try:
                    missing_keys = any(
                        not track_info.get(k) for k in ('cover_url', 'album', 'genre')
                    )
                    if missing_keys:
                        try:
                            itc = iTunesClient()
                            q = f"{track_info.get('artist','')} {track_info.get('title','')}".strip()
                            if q:
                                results = itc.search_tracks(q, limit=3)
                                if results:
                                    meta = results[0]
                                    for key in ('album', 'cover_url', 'genre', 'release_date'):
                                        if not track_info.get(key) and meta.get(key):
                                            track_info[key] = meta.get(key)
                        except Exception:
                            pass
                    # fetch lyrics if missing
                    try:
                        if not track_info.get('lyrics'):
                            lc = LyricsClient()
                            l = lc.fetch_lyrics(track_info.get('artist', ''), track_info.get('title', ''))
                            if l:
                                track_info['lyrics'] = l
                    except Exception:
                        pass

                    # add metadata for supported container types
                    try:
                        self._add_metadata(out_path, track_info)
                    except Exception as e:
                        print(f"  ⚠️  Could not add metadata: {e}")
                    # ensure metadata completed by running focused fixer for the file
                    try:
                        fixer_res = self.fix_metadata_for_file(out_path)
                        if fixer_res.get('status') != 'written':
                            print(f"  ⚠️  fix_metadata_for_file reported: {fixer_res}")
                    except Exception:
                        pass
                except Exception as e:
                    print(f"  ⚠️  Error enriching metadata: {e}")
                print(f"✅ Downloaded: {track_info.get('artist','unknown')} - {track_info.get('title','unknown')}")
                return True

            print(f"❌ Download failed: {track_info.get('title','unknown')}")
            return False
            
        except Exception as e:
            print(f"❌ Error downloading {track_info.get('title', 'unknown')}: {e}")
            return False
    
    def download_itunes_preview(self, track_info: Dict) -> bool:
        """Download 30-second preview from iTunes"""
        try:
            if not track_info.get('preview_url'):
                print(f"❌ No preview available for: {track_info['title']}")
                return False
            
            print(f"🎵 Downloading iTunes preview: {track_info['artist']} - {track_info['title']}")
            
            # Download the preview
            response = requests.get(track_info['preview_url'], timeout=30)
            if response.status_code != 200:
                print(f"❌ Failed to download preview: HTTP {response.status_code}")
                return False
            
            # Create filename
            safe_title = self._safe_filename(track_info['title'])
            file_path = os.path.join(self.download_path, f'{safe_title}_preview.m4a')
            
            # Save the preview
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Downloaded preview: {track_info['artist']} - {track_info['title']}")
            print(f"📝 Note: This is a 30-second preview from iTunes")
            # attempt to enrich metadata for preview file
            try:
                self.fix_metadata_for_file(file_path)
            except Exception:
                pass
            return True
            
        except Exception as e:
            print(f"❌ Error downloading preview: {e}")
            return False
    
    def download_audio_from_url(self, url: str, track_info: Dict) -> bool:
        """Download audio from a direct URL"""
        try:
            response = requests.get(url, timeout=30, stream=True)
            if response.status_code != 200:
                return False
            
            safe_title = self._safe_filename(track_info['title'])
            file_path = os.path.join(self.download_path, f'{safe_title}.m4a')
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"✅ Downloaded: {track_info['artist']} - {track_info['title']}")
            try:
                self.fix_metadata_for_file(file_path)
            except Exception:
                pass
            return True
            
        except Exception as e:
            print(f"❌ Error downloading audio: {e}")
            return False
    
    def _add_metadata(self, file_path: str, track_info: Dict):
        """Add metadata to MP3 file"""
        # Determine file type by extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip('.')

        title = track_info.get('title', '')
        artist = track_info.get('artist', '')
        album = track_info.get('album', '')
        genre = track_info.get('genre', '')
        release = track_info.get('release_date', '')
        cover_url = track_info.get('cover_url')

        try:
            print(f"Adding metadata -> file: {file_path} ext: {ext}")
            if ext == 'mp3':
                try:
                    audio = ID3(file_path)
                except ID3NoHeaderError:
                    audio = ID3()

                audio.add(TIT2(encoding=3, text=title))
                audio.add(TPE1(encoding=3, text=artist))
                audio.add(TALB(encoding=3, text=album))
                if genre:
                    audio.add(TCON(encoding=3, text=genre))
                if release:
                    try:
                        audio.add(TDRC(encoding=3, text=release[:4]))
                    except Exception:
                        pass
                if cover_url:
                    try:
                        resp = requests.get(cover_url, timeout=10)
                        if resp.status_code == 200:
                            mime = resp.headers.get('Content-Type', 'image/jpeg')
                            audio.add(APIC(encoding=3, mime=mime, type=3, desc='Cover', data=resp.content))
                    except Exception:
                        pass
                # add unsynchronized lyrics if available
                lyrics = track_info.get('lyrics')
                if lyrics:
                    try:
                        audio.add(USLT(encoding=3, lang='eng', desc='', text=lyrics))
                    except Exception:
                        pass
                try:
                    audio.save(file_path, v2_version=3)
                except TypeError:
                    # older mutagen may not accept v2_version param
                    audio.save(file_path)
                print(f"  -> MP3 tags written: {list(audio.keys())}")

            elif ext in ('m4a', 'm4b', 'mp4'):
                mp4 = MP4(file_path)
                # ensure tags object exists
                if mp4.tags is None:
                    mp4.tags = MP4Tags()

                if title:
                    mp4.tags['\xa9nam'] = [title]
                if artist:
                    mp4.tags['\xa9ART'] = [artist]
                if album:
                    mp4.tags['\xa9alb'] = [album]
                if genre:
                    mp4.tags['\xa9gen'] = [genre]
                if release:
                    mp4.tags['\xa9day'] = [release]
                if cover_url:
                    try:
                        resp = requests.get(cover_url, timeout=10)
                        if resp.status_code == 200:
                            mp4.tags['covr'] = [MP4Cover(resp.content, imageformat=MP4Cover.FORMAT_JPEG)]
                    except Exception:
                        pass
                # add lyrics atom for mp4 if available
                lyrics = track_info.get('lyrics')
                if lyrics:
                    try:
                        mp4.tags['\xa9lyr'] = [lyrics]
                    except Exception:
                        try:
                            mp4.tags['©lyr'] = [lyrics]
                        except Exception:
                            pass
                try:
                    mp4.save()
                    print(f"  -> MP4 tags written: {list(mp4.tags.keys()) if mp4.tags else None}")
                except Exception as e:
                    print(f"  ⚠️  Could not save MP4 tags: {e}")

            else:
                # Unsupported container for metadata — skip
                pass

        except Exception as e:
            print(f"  ⚠️  Could not add metadata: {e}")
    
    def _safe_filename(self, filename: str) -> str:
        """Convert string to safe filename"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        
        # Remove trailing periods and spaces
        filename = filename.rstrip('. ')
        
        return filename

    def fix_all_metadata(self, force: bool = False) -> list:
        """Scan download folder and enrich files missing basic metadata.

        If `force` is True, attempt to write metadata for all files regardless
        of whether basic tags appear present.

        Returns a list of results with filename and status.
        """
        itc = iTunesClient()
        lc = LyricsClient()
        results = []

        try:
            files = [f for f in os.listdir(self.download_path) if os.path.isfile(os.path.join(self.download_path, f))]
        except Exception:
            return results

        for fname in files:
            path = os.path.join(self.download_path, fname)
            name, ext = os.path.splitext(fname)
            ext = ext.lower()
            needs_fix = False
            try:
                if ext == '.mp3':
                    try:
                        tags = ID3(path)
                        has_title = 'TIT2' in tags
                        has_artist = 'TPE1' in tags
                    except Exception:
                        has_title = False
                        has_artist = False
                    if not (has_title and has_artist):
                        needs_fix = True
                elif ext in ('.m4a', '.mp4'):
                    try:
                        mp4 = MP4(path)
                        tags = mp4.tags or {}
                        has_title = '\xa9nam' in tags
                        has_artist = '\xa9ART' in tags
                    except Exception:
                        has_title = False
                        has_artist = False
                    if not (has_title and has_artist):
                        needs_fix = True
            except Exception:
                needs_fix = True

            if not needs_fix and not force:
                # record that file was examined but skipped
                results.append({'file': fname, 'status': 'skipped'})
                continue

            title = os.path.splitext(fname)[0]
            track_info = {'title': title}
            # try iTunes search
            try:
                results_it = itc.search_tracks(title, limit=8)
            except Exception:
                results_it = []
            match = None
            for r in results_it:
                if r.get('title','').lower() == title.lower():
                    match = r
                    break
            if not match and results_it:
                match = results_it[0]
            if match:
                track_info.update({
                    'artist': match.get('artist'),
                    'album': match.get('album'),
                    'cover_url': match.get('cover_url'),
                    'genre': match.get('genre'),
                    'release_date': match.get('release_date'),
                    'preview_url': match.get('preview_url')
                })

            # lyrics
            if track_info.get('artist'):
                try:
                    l = lc.fetch_lyrics(track_info.get('artist'), track_info.get('title'))
                    if l:
                        track_info['lyrics'] = l
                except Exception:
                    pass

            try:
                self._add_metadata(path, track_info)
                results.append({'file': fname, 'status': 'written'})
            except Exception as e:
                results.append({'file': fname, 'status': 'error', 'error': str(e)})

        return results

    def fix_metadata_for_file(self, file_path: str) -> dict:
        """Enrich and write metadata for a single file. Returns result dict."""
        itc = iTunesClient()
        lc = LyricsClient()
        fname = os.path.basename(file_path)
        title = os.path.splitext(fname)[0]
        track_info = {'title': title}

        # try iTunes search
        try:
            results_it = itc.search_tracks(title, limit=6)
        except Exception:
            results_it = []
        match = None
        for r in results_it:
            if r.get('title','').lower() == title.lower():
                match = r
                break
        if not match and results_it:
            match = results_it[0]
        if match:
            track_info.update({
                'artist': match.get('artist'),
                'album': match.get('album'),
                'cover_url': match.get('cover_url'),
                'genre': match.get('genre'),
                'release_date': match.get('release_date'),
                'preview_url': match.get('preview_url')
            })

        # lyrics
        if track_info.get('artist'):
            try:
                l = lc.fetch_lyrics(track_info.get('artist'), track_info.get('title'))
                if l:
                    track_info['lyrics'] = l
            except Exception:
                pass

        try:
            self._add_metadata(file_path, track_info)
            return {'file': fname, 'status': 'written'}
        except Exception as e:
            return {'file': fname, 'status': 'error', 'error': str(e)}