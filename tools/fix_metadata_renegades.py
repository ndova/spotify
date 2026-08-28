from itunes_client import iTunesClient
from lyrics_client import LyricsClient
from downloader import AudioDownloader
import os

fn = os.path.join('downloads','Renegades of Funk.m4a')
if not os.path.exists(fn):
    print('file not found:', fn)
    raise SystemExit(1)

title = os.path.splitext(os.path.basename(fn))[0]
print('Inferred title:', title)

itc = iTunesClient()
results = itc.search_tracks(title, limit=10)
print('iTunes results:', len(results))
match = None
for r in results:
    print('  candidate:', r.get('title'), '-', r.get('artist'))
    if r.get('title','').lower() == title.lower():
        match = r
        break
if not match and results:
    match = results[0]

track_info = {
    'title': title,
}
if match:
    track_info.update({
        'artist': match.get('artist'),
        'album': match.get('album'),
        'cover_url': match.get('cover_url'),
        'genre': match.get('genre'),
        'release_date': match.get('release_date'),
        'preview_url': match.get('preview_url')
    })

# fetch lyrics
lc = LyricsClient()
if track_info.get('artist'):
    l = lc.fetch_lyrics(track_info.get('artist'), track_info.get('title'))
    if l:
        track_info['lyrics'] = l

print('Final track_info:', track_info)

ad = AudioDownloader('./downloads')
ad._add_metadata(fn, track_info)
print('Done writing metadata')
