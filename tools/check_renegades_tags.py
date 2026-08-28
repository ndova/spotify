from mutagen.mp4 import MP4
import os
p = os.path.join('downloads','Renegades of Funk.m4a')
print('file ->', p)
mp4 = MP4(p)
print('tags ->')
for k,v in (mp4.tags or {}).items():
    print(k, '->', v)
print('--- raw keys ---')
print(list((mp4.tags or {}).keys()))
