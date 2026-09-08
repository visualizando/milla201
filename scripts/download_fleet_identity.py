"""Registry enrichment for the 20 MMSI with most regional gaps; explicit sample."""
import datetime as dt, hashlib, json, urllib.request, urllib.parse
from download_context import ROOT, token

def main():
    fleet=json.loads((ROOT/'data/processed/fleet-analysis.json').read_text(encoding='utf-8'))
    folder=ROOT/'data/raw/fleet/identity'; folder.mkdir(parents=True,exist_ok=True)
    for v in fleet['vessels'][:20]:
        mmsi=v['mmsi']; path=folder/f'{mmsi}.json'
        if path.exists(): continue
        params={'datasets[0]':'public-global-vessel-identity:v4.0','where':f"ssvid='{mmsi}'",'limit':50}
        url='https://gateway.api.globalfishingwatch.org/v3/vessels/search?'+urllib.parse.urlencode(params)
        req=urllib.request.Request(url,headers={'Authorization':'Bearer '+token(),'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=45) as f: raw=f.read()
        data=json.loads(raw)
        assert not data.get('since'), 'Identity results paginated; inspect before using'
        assert len(data['entries'])==data['total'], 'Incomplete identity search'
        path.write_bytes(raw)
        path.with_suffix('.request.json').write_text(json.dumps({'url':url,'sha256':hashlib.sha256(raw).hexdigest(),
            'retrieved_at':dt.datetime.now(dt.timezone.utc).isoformat()},indent=2),encoding='utf-8')
        print(mmsi,len(data['entries']),'identity entries',flush=True)

if __name__=='__main__':main()
