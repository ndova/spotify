from downloader import AudioDownloader
from itunes_client import iTunesClient
from lyrics_client import LyricsClient
from mutagen.mp4 import MP4
from mutagen.id3 import ID3
import os

DOWNLOADS = 'downloads'

itc = iTunesClient()
lc = LyricsClient()
ad = AudioDownloader(DOWNLOADS)

files = [f for f in os.listdir(DOWNLOADS) if os.path.isfile(os.path.join(DOWNLOADS,f))]
print('Found files:', len(files))

candidates = []
for f in files:
    path = os.path.join(DOWNLOADS, f)
    name, ext = os.path.splitext(f)
    ext = ext.lower()
    try:
        if ext == '.mp3':
            tags = ID3(path)
            has_title = 'TIT2' in tags
            has_artist = 'TPE1' in tags
            if not (has_title and has_artist):
                candidates.append((f, path, 'mp3'))
        elif ext in ('.m4a', '.mp4'):
            mp4 = MP4(path)
            tags = mp4.tags or {}
            has_title = '\u00a9nam' in tags
            has_artist = '\u00a9ART' in tags
            if not (has_title and has_artist):
                candidates.append((f, path, 'm4a'))
    except Exception as e:
        print('Error reading tags for', f, e)
        candidates.append((f, path, ext.lstrip('.')))

print('Candidates to fix:', len(candidates))
for fname, path, ftype in candidates:
    print('\nProcessing:', fname)
    title = os.path.splitext(fname)[0]
    # search iTunes
    try:
        results = itc.search_tracks(title, limit=10)
    except Exception as e:
        print('  iTunes search failed:', e)
        results = []
    match = None
    for r in results:
        if r.get('title','').lower() == title.lower():
            match = r
            break
    if not match and results:
        match = results[0]
    track_info = {'title': title}
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
        except Exception as e:
            print('  lyrics fetch failed:', e)
    print('  track_info ->', {k:v for k,v in track_info.items() if k in ('title','artist','album')})
    try:
        ad._add_metadata(path, track_info)
        print('  wrote metadata for', fname)
    except Exception as e:
        print('  failed to write metadata for', fname, e)

print('\nDone. Re-run tag checks to verify.')
