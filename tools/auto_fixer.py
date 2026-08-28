import time
import os
import json
import argparse
from downloader import AudioDownloader


def load_state(state_path):
    if os.path.exists(state_path):
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_state(state_path, processed):
    try:
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(list(processed), f)
    except Exception:
        pass


def main(download_path, interval=5, once=False):
    state_file = os.path.join(download_path, '.auto_fixer_state.json')
    processed = load_state(state_file)
    ad = AudioDownloader(download_path)
    try:
        if once:
            files = [f for f in os.listdir(download_path) if os.path.isfile(os.path.join(download_path, f))]
            for fname in files:
                if fname in processed:
                    continue
                path = os.path.join(download_path, fname)
                print(f"[auto-fixer] Processing: {fname}")
                res = ad.fix_metadata_for_file(path)
                print(f"[auto-fixer] -> {res}")
                processed.add(fname)
            save_state(state_file, processed)
            return

        print(f"Starting auto-fixer: watching {download_path}")
        while True:
            files = [f for f in os.listdir(download_path) if os.path.isfile(os.path.join(download_path, f))]
            for fname in files:
                if fname in processed:
                    continue
                path = os.path.join(download_path, fname)
                print(f"[auto-fixer] New file: {fname}")
                res = ad.fix_metadata_for_file(path)
                print(f"[auto-fixer] -> {res}")
                processed.add(fname)
                save_state(state_file, processed)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("[auto-fixer] Stopped by user")
    except Exception as e:
        print(f"[auto-fixer] Error: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--downloads', default='./downloads')
    parser.add_argument('--interval', type=int, default=5)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    main(args.downloads, interval=args.interval, once=args.once)
