"""Fetch annual requests with monthly resolution, then split without losing provenance."""
import json,hashlib,datetime as dt,urllib.request,urllib.error,argparse
from download_context import ROOT,BASE,PRODUCTS,token,request_spec,flatten
from urllib.parse import urlencode

def fetch(product,year,credential):
 last='08' if year==2026 else '12'
 spec=request_spec(product,f'{year}-{last}')
 spec['params']['date-range']=f'{year}-01-01T00:00:00.000Z,'+spec['params']['date-range'].split(',')[1]
 spec['url']=BASE+'report?'+urlencode(spec['params'])
 folder=ROOT/'data/raw/context_annual'/product;folder.mkdir(parents=True,exist_ok=True)
 path=folder/f'{year}.json';manifest=folder/f'{year}.request.json'
 if path.exists() and manifest.exists():
  meta=json.loads(manifest.read_text());raw=path.read_bytes()
  if meta['request']!=spec or meta['sha256']!=hashlib.sha256(raw).hexdigest():raise ValueError('Cache mismatch')
 else:
  req=urllib.request.Request(spec['url'],data=json.dumps(spec['body']).encode(),headers={'Authorization':'Bearer '+credential,'User-Agent':'Mozilla/5.0','Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(req,timeout=95) as f:raw=f.read()
  except urllib.error.HTTPError as e:
   raise RuntimeError(f'{product} {year}: HTTP {e.code}: '+e.read().decode()[:500]) from None
  flatten(json.loads(raw));path.write_bytes(raw)
  meta={'request':spec,'retrieved_at':dt.datetime.now(dt.timezone.utc).isoformat(),'sha256':hashlib.sha256(raw).hexdigest()}
  manifest.write_text(json.dumps(meta,indent=2),encoding='utf-8')
 rows=flatten(json.loads(raw))
 if any(not str(r['date']).startswith(str(year)) for r in rows):raise ValueError('Unexpected year')
 dest=ROOT/'data/raw/context'/product;dest.mkdir(parents=True,exist_ok=True)
 for m in range(1,int(last)+1):
  month=f'{year}-{m:02d}';subset=[r for r in rows if str(r['date'])[:7]==month]
  # Keep original single-month reports for an independent cross-check.
  p=dest/f'{month}.json'
  if p.exists() and (dest/f'{month}.request.json').exists():
   original=flatten(json.loads(p.read_text()))
   field='hours' if product in ('presence','effort') else 'detections'
   before=sum(float(r[field]) for r in original);after=sum(float(r[field]) for r in subset)
   if abs(before-after)>max(0.01,before*1e-8):raise ValueError(f'Monthly/annual totals differ: {product} {month} {before} {after}')
  p.write_text(json.dumps({'entries':subset,'metadata':{'annual_source':str(path.relative_to(ROOT))}},separators=(',',':')),encoding='utf-8')
 print('Complete',product,year,len(rows),'monthly vessel/group rows',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--years',nargs='+',type=int,default=list(range(2017,2027)));p.add_argument('--products',nargs='+',default=list(PRODUCTS),choices=list(PRODUCTS));a=p.parse_args();t=token()
 for year in a.years:
  for product in a.products:fetch(product,year,t)
