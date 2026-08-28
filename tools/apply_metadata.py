from itunes_client import iTunesClient
from downloader import AudioDownloader
import os

TITLE = "If You're Not the One"
DOWNLOADS = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'downloads')
TARGET = os.path.join(DOWNLOADS, "If You're Not the One.m4a")
print('Target file:', TARGET)

cli = iTunesClient()
results = cli.search_tracks(TITLE, limit=5)
print('Found', len(results), 'results')
if results:
    first = results[0]
    print('Using:', first.get('artist'), '-', first.get('title'), '| album:', first.get('album'))
    ad = AudioDownloader(DOWNLOADS)
    ad._add_metadata(TARGET, first)
    print('Metadata write attempted')
else:
    print('No results found for query')
