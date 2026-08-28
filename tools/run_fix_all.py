from downloader import AudioDownloader
from config import Config

if __name__ == '__main__':
    d = AudioDownloader(Config.DOWNLOAD_PATH)
    res = d.fix_all_metadata(force=True)
    print(res)
