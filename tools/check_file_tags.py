import sys
from mutagen.mp4 import MP4
import os

if len(sys.argv) < 2:
    print('Usage: check_file_tags.py <relative-path>')
    raise SystemExit(1)

p = sys.argv[1]
if not os.path.exists(p):
    print('File not found:', p)
    raise SystemExit(1)

print('File ->', p)
try:
    mp4 = MP4(p)
    tags = mp4.tags or {}
    if not tags:
        print('No tags present')
    else:
        print('Tags:')
        for k,v in tags.items():
            print(k, '->', v if isinstance(v, (str,list,tuple)) and len(str(v))<1000 else f'<{type(v)} len {len(v)}>')
except Exception as e:
    print('Error reading tags:', e)
