import sys
import os
sys.path.insert(0, os.getcwd())
from downloader import AudioDownloader
from config import Config

d = AudioDownloader(Config.DOWNLOAD_PATH)
res = d.fix_all_metadata(force=True)
print(res)
