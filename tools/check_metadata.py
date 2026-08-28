import sys
import os
from mutagen.mp4 import MP4
from mutagen.id3 import ID3, USLT

DEFAULT = os.path.join('downloads', "If You're Not the One.m4a")
fn = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
fn = os.path.abspath(fn)
print('Checking file:', fn)
if not os.path.exists(fn):
    print('File not found')
    sys.exit(1)

ext = os.path.splitext(fn)[1].lower()
if ext in ('.m4a', '.mp4', '.m4b'):
    mp4 = MP4(fn)
    tags = mp4.tags or {}
    print('MP4 tags keys:', list(tags.keys()))
    # common lyrics keys
    for k in ['\xa9lyr', '©lyr', '----:com.apple.iTunes:LYRICS']:
        if k in tags:
            print(f'Found lyrics key {k}:')
            print(tags[k])
    # fallback: print covr presence
    if '\xa9lyr' not in tags and '©lyr' not in tags:
        print('No lyrics found in MP4 tags')
elif ext == '.mp3':
    try:
        id3 = ID3(fn)
        print('ID3 tags present')
        uslt = [frame for frame in id3.getall('USLT')]
        if uslt:
            for u in uslt:
                print('USLT:', u.text[:400])
        else:
            print('No USLT frames')
    except Exception as e:
        print('Error reading ID3:', e)
else:
    print('Unsupported file type')
