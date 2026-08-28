from downloader import AudioDownloader
import os

ad = AudioDownloader('./downloads')
track = {'artist':'Ed Sheeran','title':'Shape of You'}
print('Starting download test for:', track)
ok = ad.download_from_youtube(track, fmt='mp3', bitrate='128')
print('download_ok ->', ok)

safe = ad._safe_filename(track['title'])
files = [f for f in os.listdir('./downloads') if f.startswith(safe)]
print('found files ->', files)
for f in files:
    path = os.path.join('./downloads', f)
    print('file ->', path)
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == '.mp3':
            from mutagen.id3 import ID3
            tags = ID3(path)
            print('ID3 keys ->', list(tags.keys()))
        elif ext in ('.m4a', '.mp4'):
            from mutagen.mp4 import MP4
            mp4 = MP4(path)
            print('MP4 tags ->', list(mp4.tags.keys()) if mp4.tags else None)
        else:
            print('Unsupported ext for metadata check:', ext)
    except Exception as e:
        print('Error reading tags:', e)
