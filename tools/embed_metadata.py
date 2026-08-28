import sys
import os
from itunes_client import iTunesClient
from downloader import AudioDownloader

if len(sys.argv) < 2:
    print('Usage: embed_metadata.py <path-to-file> [search-title]')
    sys.exit(1)

file_path = sys.argv[1]
search_title = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(os.path.basename(file_path))[0]

file_path = os.path.abspath(file_path)
print('Target file:', file_path)
if not os.path.exists(file_path):
    print('File not found')
    sys.exit(1)

cli = iTunesClient()
results = cli.search_tracks(search_title, limit=5)
print('Found', len(results), 'results for query:', search_title)
if results:
    first = results[0]
    print('Using:', first.get('artist'), '-', first.get('title'), '| album:', first.get('album'))
    ad = AudioDownloader(os.path.dirname(file_path))
    # pass track_info; ensure title matches search result
    info = dict(first)
    # keep title from result
    info['title'] = first.get('title')
    info['artist'] = first.get('artist')
    ad._add_metadata(file_path, info)
    print('Metadata write attempted')
else:
    print('No metadata found for query')
