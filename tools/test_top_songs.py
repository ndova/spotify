from itunes_client import iTunesClient
itc = iTunesClient()
for country in ['US','ID','GB','JP','AU']:
    try:
        print('==', country)
        top = itc.get_top_songs(limit=5, country=country)
        print('len ->', len(top))
        for t in top:
            print(' -', t.get('title'), 'by', t.get('artist'), 'id', t.get('track_id'))
    except Exception as e:
        print('err', e)
