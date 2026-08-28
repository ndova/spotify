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
import re


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
            # For m4a we want AAC in MP4 container so that MP4 tags (mutagen) work reliably.
            # Opus-in-M4A often fails to write MP4 tags or produces non-standard files.
            fmt_norm = (fmt or 'mp3').lower().strip()
            if fmt_norm in ('m4a', 'mp4', 'aac'):
                # force AAC/M4A
                fmt_norm = 'm4a'
                if post:
                    post[0]['preferredcodec'] = 'm4a'
                    # keep desired quality; FFmpeg will encode AAC at this bitrate
                    post[0]['preferredquality'] = str(bitrate)
            else:
                fmt_norm = 'mp3'
                if post:
                    post[0]['preferredcodec'] = 'mp3'
                    post[0]['preferredquality'] = str(bitrate)
            opts['postprocessors'] = post
            # set ffmpeg postprocessor args to force bitrate + ensure AAC/movflags for m4a
            try:
                br_value = int(bitrate)
            except Exception:
                br_value = int(str(bitrate).strip() or 256)
            if fmt_norm == 'm4a':
                opts['postprocessor_args'] = ['-c:a', 'aac', '-b:a', f"{br_value}k", '-movflags', '+faststart']
                opts['prefer_ffmpeg'] = True
                # Use %(ext)s with explicit ext forced via preferredcodec; yt-dlp will use .m4a
                opts['outtmpl'] = os.path.join(self.download_path, f'{safe_title}.%(ext)s')
            else:
                opts['postprocessor_args'] = ['-b:a', f"{br_value}k"]
                opts['outtmpl'] = os.path.join(self.download_path, f'{safe_title}.%(ext)s')
            # keep normalized fmt for later metadata step
            fmt = fmt_norm
            
            print(f"⬇️  Downloading: {video_title}")
            print(f"  -> outtmpl: {opts['outtmpl']}")
            print(f"  -> safe_title: {safe_title}")
            
            # Download the audio
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([video_url])
            
            # After download, find the actual output file produced by yt-dlp
            # Prefer the expected extension first to avoid picking wrong container
            expected_ext = 'm4a' if fmt == 'm4a' else 'mp3'
            ordered_exts = [expected_ext] + [e for e in ['mp3', 'm4a', 'm4b', 'aac', 'wav', 'ogg', 'opus'] if e != expected_ext]
            out_path = None
            for ext in ordered_exts:
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

            # Aggressive dedup: strip repeated extensions anywhere
            if out_path:
                # collapse ".m4a.m4a" or ".mp3.mp3" etc. anywhere in basename
                base, ext = os.path.splitext(out_path)
                # ext is last extension; check if base itself ends with same ext
                while base.lower().endswith(ext.lower()) and ext:
                    print(f"  -> dedup extension: {out_path} -> {base}")
                    prev = out_path
                    # remove duplicate suffix from base
                    base = base[: -len(ext)]
                    out_path = base + ext
                    # also rename file if it exists with double
                    if os.path.exists(prev) and not os.path.exists(out_path):
                        try:
                            os.rename(prev, out_path)
                            print(f"  -> renamed dedup: {prev} -> {out_path}")
                        except Exception as e:
                            print(f"  ⚠️  dedup rename failed: {e}")
                            out_path = prev
                            break
                    elif os.path.exists(prev) and os.path.exists(out_path):
                        try:
                            os.remove(prev)
                        except Exception:
                            pass
                        break
                    else:
                        # no file yet with double, but fix path for next steps
                        break
                    base, ext = os.path.splitext(out_path)
                # also sanitize any scan-found file with multiple extensions
                # e.g., "Song.m4a.m4a" found via scan
                if out_path.lower().endswith('.m4a.m4a'):
                    fixed = re.sub(r'(\.m4a)+$', '.m4a', out_path, flags=re.IGNORECASE)
                    if fixed != out_path and not os.path.exists(fixed):
                        try:
                            os.rename(out_path, fixed)
                            print(f"  -> fixed double extension: {out_path} -> {fixed}")
                            out_path = fixed
                        except Exception as e:
                            print(f"  ⚠️  Could not fix double extension: {e}")

            if out_path and os.path.exists(out_path):
                # Coerce mismatched extension if needed (e.g., yt-dlp produced opus but we wanted m4a)
                # If user requested m4a but we found mp3/opus, try to convert via ffmpeg to proper m4a
                actual_ext = os.path.splitext(out_path)[1].lower().lstrip('.')
                if fmt == 'm4a' and actual_ext != 'm4a':
                    # attempt ffmpeg transcode to AAC/m4a
                    try:
                        import subprocess
                        ffmpeg = shutil.which('ffmpeg') or os.path.join(_resolve_ffmpeg_location() or '', 'ffmpeg.exe')
                        if ffmpeg and os.path.exists(ffmpeg) if ffmpeg.endswith('.exe') else shutil.which(ffmpeg):
                            target = os.path.join(self.download_path, f"{safe_title}.m4a")
                            # avoid overwriting if target already exists
                            if out_path != target and not os.path.exists(target):
                                cmd = [ffmpeg, '-y', '-i', out_path, '-c:a', 'aac', '-b:a', f"{br_value}k", '-movflags', '+faststart', target]
                                print(f"  -> transcoding {out_path} -> {target} via ffmpeg")
                                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                if os.path.exists(target):
                                    try:
                                        os.remove(out_path)
                                    except Exception:
                                        pass
                                    out_path = target
                                    print(f"  -> transcoded to {out_path}")
                    except Exception as e:
                        print(f"  ⚠️  Transcode to m4a failed: {e}")

                # Verify actual file is AAC/MP4 when m4a requested (probe via ffprobe if available)
                if fmt == 'm4a':
                    try:
                        probe = shutil.which('ffprobe') or os.path.join(_resolve_ffmpeg_location() or '', 'ffprobe.exe')
                        if probe and (os.path.exists(probe) if probe.endswith('.exe') else shutil.which(probe)):
                            import subprocess, json as _json
                            cmd = [probe, '-v', 'quiet', '-print_format', 'json', '-show_streams', out_path]
                            res = subprocess.run(cmd, capture_output=True, text=True)
                            if res.returncode == 0:
                                info = _json.loads(res.stdout or '{}')
                                streams = info.get('streams', [])
                                # expect audio codec aac
                                codecs = [s.get('codec_name') for s in streams]
                                print(f"  -> probe codecs: {codecs}")
                    except Exception:
                        pass

                # Enrich metadata from iTunes before writing (always try to fill missing fields correctly)
                try:
                    # Clean search query - use artist + title, handling parenthetical
                    search_artist = track_info.get('artist', '')
                    search_title = track_info.get('title', '')
                    if '(' in search_title:
                        search_title = search_title.split('(')[0].strip()
                    if missing_keys or not track_info.get('release_date'):
                        try:
                            itc = iTunesClient()
                            q = f"{search_artist} {search_title}".strip()
                            if q:
                                results = itc.search_tracks(q, limit=3)
                                if results:
                                    meta = results[0]
                                    # Properly map all enrichment fields
                                    for key in ('album', 'cover_url', 'genre', 'release_date', 'release_year', 'duration'):
                                        if not track_info.get(key) and meta.get(key):
                                            track_info[key] = meta.get(key)
                                    # Also ensure title/artist are correct if enriched
                                    if meta.get('title') and meta.get('title').lower() in search_title.lower():
                                        pass  # keep original title
                                    print(f"  -> enriched metadata: album={meta.get('album')}, genre={meta.get('genre')}, release={meta.get('release_date')}")
                        except Exception as e:
                            print(f"  ⚠️  Enrichment search failed: {e}")
                    # fetch lyrics if missing - use clean title
                    try:
                        if not track_info.get('lyrics'):
                            lc = LyricsClient()
                            lyrics_title = search_title
                            lyrics_artist = search_artist or track_info.get('artist', '')
                            if lyrics_artist:
                                l = lc.fetch_lyrics(lyrics_artist, lyrics_title)
                                if l:
                                    track_info['lyrics'] = l
                                    print(f"  -> fetched lyrics: {len(l)} chars")
                    except Exception:
                        pass

                    # add metadata for supported container types (ensure correct ext handling)
                    _, ext_for_meta = os.path.splitext(out_path)
                    ext_for_meta = ext_for_meta.lower()
                    try:
                        ok = self._add_metadata(out_path, track_info)
                        # Verify m4a tags were actually written
                        if fmt == 'm4a' and ext_for_meta in ('.m4a', '.mp4'):
                            try:
                                mp4v = MP4(out_path)
                                keys = list((mp4v.tags or {}).keys())
                                needed = ['\xa9nam', '\xa9ART']
                                if not all(k in keys for k in needed):
                                    print(f"  ⚠️  MP4 tags missing after first write: {keys} — retrying with helper")
                                    self._add_metadata(out_path, track_info)
                                    mp4v2 = MP4(out_path)
                                    print(f"  -> retry tags: {list((mp4v2.tags or {}).keys())}")
                            except Exception as e:
                                print(f"  ⚠️  Verify MP4 tags failed: {e}")
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
    
    def _add_metadata(self, file_path: str, track_info: Dict) -> bool:
        """Add metadata to file. Returns True if tags were written, False otherwise.

        Handles mp3 (ID3) and m4a/mp4 (MP4 atoms) reliably. For m4a, ensures AAC
        container before attempting MP4 tags and verifies write succeeded.
        """
        # Determine file type by extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip('.')

        title = track_info.get('title', '') or track_info.get('name', '')
        artist = track_info.get('artist', '') or track_info.get('artistName', '')
        album = track_info.get('album', '') or track_info.get('collectionName', '')
        genre = track_info.get('genre', '') or track_info.get('primaryGenreName', '')
        release = track_info.get('release_date', '') or track_info.get('releaseDate', '') or ''
        cover_url = track_info.get('cover_url') or track_info.get('artworkUrl100')

        try:
            print(f"Adding metadata -> file: {file_path} ext: {ext}")
            if ext == 'mp3':
                try:
                    audio = ID3(file_path)
                except ID3NoHeaderError:
                    audio = ID3()

                # Only add non-empty frames to avoid blank tags
                if title:
                    audio.add(TIT2(encoding=3, text=title))
                if artist:
                    audio.add(TPE1(encoding=3, text=artist))
                if album:
                    audio.add(TALB(encoding=3, text=album))
                if genre:
                    audio.add(TCON(encoding=3, text=genre))
                if release:
                    try:
                        audio.add(TDRC(encoding=3, text=str(release)[:4]))
                    except Exception:
                        pass
                if cover_url:
                    try:
                        resp = requests.get(cover_url, timeout=10)
                        if resp.status_code == 200:
                            mime = resp.headers.get('Content-Type', 'image/jpeg')
                            if mime == 'image/png':
                                fmt = 'image/png'
                            else:
                                fmt = 'image/jpeg'
                            audio.add(APIC(encoding=3, mime=fmt, type=3, desc='Cover', data=resp.content))
                    except Exception:
                        pass
                lyrics = track_info.get('lyrics')
                if lyrics:
                    try:
                        audio.add(USLT(encoding=3, lang='eng', desc='', text=lyrics))
                    except Exception:
                        pass
                try:
                    audio.save(file_path, v2_version=3)
                except TypeError:
                    audio.save(file_path)
                print(f"  -> MP3 tags written: {list(audio.keys())}")
                return True

            elif ext in ('m4a', 'm4b', 'mp4'):
                # Ensure file is a valid MP4/M4A before tagging
                # If file is actually webm/opus but named .m4a, MP4() will fail — detect and skip
                try:
                    mp4 = MP4(file_path)
                except Exception as e:
                    print(f"  ⚠️  MP4 open failed ({e}) — file may not be valid M4A, skipping MP4 tags")
                    return False
                if mp4.tags is None:
                    mp4.add_tags()
                    mp4.tags = MP4Tags()
                elif not isinstance(mp4.tags, MP4Tags):
                    # coercion safety
                    mp4.tags = MP4Tags(mp4.tags)

                # Only set non-empty to avoid overwriting with blanks
                if title:
                    mp4.tags['\xa9nam'] = [str(title)]
                if artist:
                    mp4.tags['\xa9ART'] = [str(artist)]
                if album:
                    mp4.tags['\xa9alb'] = [str(album)]
                if genre:
                    mp4.tags['\xa9gen'] = [str(genre)]
                if release:
                    # year or full date
                    mp4.tags['\xa9day'] = [str(release)[:10]]
                # tool/encoder tag
                mp4.tags['\xa9too'] = ['MusicDownloader']

                if cover_url:
                    try:
                        resp = requests.get(cover_url, timeout=10)
                        if resp.status_code == 200:
                            ct = resp.headers.get('Content-Type', '')
                            if 'png' in ct.lower():
                                fmt = MP4Cover.FORMAT_PNG
                            else:
                                fmt = MP4Cover.FORMAT_JPEG
                            mp4.tags['covr'] = [MP4Cover(resp.content, imageformat=fmt)]
                    except Exception:
                        pass
                lyrics = track_info.get('lyrics')
                if lyrics:
                    # iTunes-style lyrics
                    try:
                        # try both keys for compatibility
                        mp4.tags['\xa9lyr'] = [str(lyrics)]
                    except Exception:
                        try:
                            mp4.tags['----:com.apple.iTunes:LYRICS'] = [str(lyrics).encode('utf-8')]
                        except Exception:
                            pass
                try:
                    mp4.save()
                    # verify
                    mp4_check = MP4(file_path)
                    keys = list((mp4_check.tags or {}).keys())
                    print(f"  -> MP4 tags written: {keys}")
                    # success if at least title/artist present when they were supplied
                    if title and '\xa9nam' not in keys:
                        print("  ⚠️  MP4 title not persisted")
                        return False
                    if artist and '\xa9ART' not in keys:
                        print("  ⚠️  MP4 artist not persisted")
                        return False
                    return True
                except Exception as e:
                    print(f"  ⚠️  Could not save MP4 tags: {e}")
                    return False

            else:
                print(f"  ⚠️  Unsupported extension for metadata: .{ext} — skip")
                return False

        except Exception as e:
            print(f"  ⚠️  Could not add metadata: {e}")
            return False
    
    def _safe_filename(self, filename: str) -> str:
        """Convert string to safe filename without duplicate extensions."""
        filename = filename.strip()
        filename = filename.rstrip('. ')
        # Strip ALL trailing audio extensions repeatedly: "a.m4a.m4a" -> "a"
        # Also handles mixed case and multiple dots/spaces.
        while True:
            lower = filename.lower()
            stripped = None
            for ext in ('.mp3', '.m4a', '.mp4', '.m4b', '.aac', '.wav', '.ogg', '.opus', '.flac', '.webm'):
                if lower.endswith(ext):
                    stripped = filename[: -len(ext)].rstrip('. ')
                    break
            if stripped is not None and stripped != filename:
                filename = stripped
            else:
                break
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        filename = filename.rstrip('. ')
        # Collapse multiple spaces
        filename = re.sub(r'\s+', ' ', filename)
        return filename

    def fix_all_metadata(self, force: bool = False) -> list:
        """Scan download folder and enrich files missing basic metadata.

        If `force` is True, attempt to write metadata for all files regardless
        of whether basic tags appear present.

        Returns a list of results with filename and status.
        Uses proper metadata mapping to ensure correct tags.
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
            # try iTunes search - handle title with parentheses for better matching
            # e.g., "Sial (Acoustic Version)" -> search for "Sial"
            search_title = title
            if '(' in title:
                search_title = title.split('(')[0].strip()
            try:
                results_it = itc.search_tracks(search_title, limit=8)
            except Exception:
                results_it = []
            match = None
            # First try exact match
            for r in results_it:
                if r.get('title','').lower() == title.lower():
                    match = r
                    break
            # Then try partial match (title contains search term)
            if not match:
                for r in results_it:
                    if search_title.lower() in r.get('title','').lower() or r.get('title','').lower() in search_title.lower():
                        match = r
                        break
            if not match and results_it:
                match = results_it[0]
            if match:
                # Properly map all available metadata fields
                track_info.update({
                    'title': match.get('title') or title,
                    'artist': match.get('artist'),
                    'album': match.get('album'),
                    'cover_url': match.get('cover_url'),
                    'genre': match.get('genre'),
                    'release_date': match.get('release_date'),
                    'release_year': match.get('release_year'),
                    'preview_url': match.get('preview_url'),
                    'duration': match.get('duration'),
                })

            # lyrics - fetch with clean artist/title
            artist_for_lyrics = track_info.get('artist') or ''
            title_for_lyrics = track_info.get('title') or title
            if artist_for_lyrics:
                try:
                    # Clean title for lyrics search (remove parenthetical)
                    lyrics_title = title_for_lyrics.split('(')[0].strip() if '(' in title_for_lyrics else title_for_lyrics
                    l = lc.fetch_lyrics(artist_for_lyrics, lyrics_title)
                    if l:
                        track_info['lyrics'] = l
                except Exception:
                    pass

            try:
                result = self._add_metadata(path, track_info)
                # _add_metadata returns bool, check if successful
                if result is True:
                    results.append({'file': fname, 'status': 'written'})
                else:
                    results.append({'file': fname, 'status': 'error', 'error': 'Failed to write metadata'})
            except Exception as e:
                results.append({'file': fname, 'status': 'error', 'error': str(e)})

        return results

    def fix_metadata_for_file(self, file_path: str) -> dict:
        """Enrich and write metadata for a single file. Returns result dict.
        
        Properly maps metadata to ensure correct tags are written.
        """
        itc = iTunesClient()
        lc = LyricsClient()
        fname = os.path.basename(file_path)
        title = os.path.splitext(fname)[0]
        track_info = {'title': title}

        # try iTunes search - handle title with parentheses
        search_title = title.split('(')[0].strip() if '(' in title else title
        try:
            results_it = itc.search_tracks(search_title, limit=6)
        except Exception:
            results_it = []
        match = None
        # Exact match first
        for r in results_it:
            if r.get('title','').lower() == title.lower():
                match = r
                break
        # Partial match fallback
        if not match:
            for r in results_it:
                if search_title.lower() in r.get('title','').lower() or r.get('title','').lower() in search_title.lower():
                    match = r
                    break
        if not match and results_it:
            match = results_it[0]
        if match:
            track_info.update({
                'title': match.get('title') or title,
                'artist': match.get('artist'),
                'album': match.get('album'),
                'cover_url': match.get('cover_url'),
                'genre': match.get('genre'),
                'release_date': match.get('release_date'),
                'release_year': match.get('release_year'),
                'preview_url': match.get('preview_url'),
                'duration': match.get('duration'),
            })

        # lyrics
        artist_for_lyrics = track_info.get('artist') or ''
        title_for_lyrics = track_info.get('title') or title
        if artist_for_lyrics:
            try:
                lyrics_title = title_for_lyrics.split('(')[0].strip() if '(' in title_for_lyrics else title_for_lyrics
                l = lc.fetch_lyrics(artist_for_lyrics, lyrics_title)
                if l:
                    track_info['lyrics'] = l
            except Exception:
                pass

        try:
            result = self._add_metadata(file_path, track_info)
            if result is True:
                return {'file': fname, 'status': 'written'}
            else:
                return {'file': fname, 'status': 'error', 'error': 'Failed to write metadata'}
        except Exception as e:
            return {'file': fname, 'status': 'error', 'error': str(e)}