"""One cached monthly-resolution AIS presence report per year for EEZ 8466."""
import argparse, datetime as dt, hashlib, json, urllib.request, urllib.parse
from download_context import ROOT, BASE, token, request_spec, flatten

def boundary():
    folder=ROOT/'data/raw/fleet'; folder.mkdir(parents=True,exist_ok=True)
    for name,endpoint in [('eez_region','datasets/public-eez-areas/context-layers/8466'),('eez_metadata','datasets/public-eez-areas')]:
        path=folder/f'{name}.json'
        if path.exists(): continue
        url='https://gateway.api.globalfishingwatch.org/v3/'+endpoint
        request=urllib.request.Request(url,headers={'Authorization':'Bearer '+token(),'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(request,timeout=45) as response: raw=response.read()
        json.loads(raw);path.write_bytes(raw)
        path.with_suffix('.request.json').write_text(json.dumps({'url':url,'sha256':hashlib.sha256(raw).hexdigest(),
            'retrieved_at':dt.datetime.now(dt.timezone.utc).isoformat()},indent=2),encoding='utf-8')

def fetch(year):
    spec = request_spec('presence', f'{year}-08' if year == 2026 else f'{year}-12')
    spec['params']['date-range'] = f'{year}-01-01T00:00:00.000Z,' + spec['params']['date-range'].split(',')[1]
    spec['body'] = {'region': {'dataset': 'public-eez-areas', 'id': 8466}}
    spec['url'] = BASE + 'report?' + urllib.parse.urlencode(spec['params'])
    folder = ROOT / 'data/raw/fleet/eez_presence'; folder.mkdir(parents=True, exist_ok=True)
    path = folder / f'{year}.json'; manifest = folder / f'{year}.request.json'
    if path.exists() and manifest.exists():
        raw = path.read_bytes(); meta = json.loads(manifest.read_text())
        assert meta['request'] == spec and meta['sha256'] == hashlib.sha256(raw).hexdigest()
    else:
        req = urllib.request.Request(spec['url'], data=json.dumps(spec['body']).encode(), headers={
            'Authorization': 'Bearer ' + token(), 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=95) as response: raw = response.read()
        flatten(json.loads(raw))
        path.write_bytes(raw)
        manifest.write_text(json.dumps({'request': spec, 'sha256': hashlib.sha256(raw).hexdigest(),
            'retrieved_at': dt.datetime.now(dt.timezone.utc).isoformat()}, indent=2), encoding='utf-8')
    rows = flatten(json.loads(raw))
    assert all(str(r['date']).startswith(str(year)) for r in rows)
    print(year, len(rows), 'monthly presence rows', flush=True)

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--years', nargs='+', type=int, default=list(range(2017,2027)))
    boundary()
    for year in p.parse_args().years: fetch(year)
