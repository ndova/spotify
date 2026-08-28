from mutagen.mp4 import MP4
import os
p = os.path.join('downloads','Shallow Water.m4a')
print('File ->', p)
if not os.path.exists(p):
    print('File not found')
    raise SystemExit(1)
mp4 = MP4(p)
print('tags ->')
for k,v in (mp4.tags or {}).items():
    if isinstance(v, bytes):
        print(k,'->', f'bytes len {len(v)}')
    else:
        print(k,'->', v)
print('raw keys ->', list((mp4.tags or {}).keys()))
