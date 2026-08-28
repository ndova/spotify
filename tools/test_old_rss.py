import requests
for country in ['us','id','gb','jp','au']:
    url = f'https://itunes.apple.com/{country}/rss/topsongs/5/json'
    try:
        r = requests.get(url, timeout=10)
        print(country, r.status_code)
        if r.status_code==200:
            data=r.json()
            for item in data.get('feed',{}).get('entry',[]):
                print(' -', item.get('im:name',{}).get('label'), 'by', item.get('im:artist',{}).get('label'))
    except Exception as e:
        print('err', country, e)
