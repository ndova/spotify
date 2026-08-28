from downloader import AudioDownloader

ad = AudioDownloader('./downloads')
res = ad.fix_all_metadata()
for r in res:
    if r.get('file','').lower().startswith('shallow water'):
        print('Result ->', r)

if not any(r.get('file','').lower().startswith('shallow water') for r in res):
    print('No result for Shallow Water in fix_all_metadata run')
