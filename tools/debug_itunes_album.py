from itunes_client import iTunesClient
import os

album_id = '1753916519'
cli = iTunesClient()
print('Lookup album id:', album_id)
res = cli.get_album_tracks(album_id)
print('Tracks count:', len(res))
for i, t in enumerate(res[:10]):
    print(i+1, t.get('title'), t.get('track_id'))

# Also show raw lookup data
import requests
params = {'id': album_id, 'entity': 'song', 'country': 'US'}
resp = requests.get('https://itunes.apple.com/lookup', params=params, timeout=10)
print('HTTP', resp.status_code)
try:
    data = resp.json()
    print('results len', len(data.get('results', [])))
    for i, item in enumerate(data.get('results', [])[:10]):
        print(i, item.get('wrapperType'), item.get('kind'), item.get('trackName'), item.get('collectionName'))
except Exception as e:
    print('Failed parsing json', e)
