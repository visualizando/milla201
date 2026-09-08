"""Resumable monthly 4Wings reports for the site's exact regional box.
Raw responses and request provenance stay outside the public build.
One report at a time, as required by GFW. No token is logged or persisted here.
"""
import argparse, calendar, datetime as dt, hashlib, json, os, time
import urllib.request, urllib.parse, urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='https://gateway.api.globalfishingwatch.org/v3/4wings/'
POLYGON={'type':'Polygon','coordinates':[[[-70,-60],[-40,-60],[-40,-30],[-70,-30],[-70,-60]]]}
PRODUCTS={
 'effort':('public-global-fishing-effort:v4.0',None,'MMSI'),
 'presence':('public-global-presence:v4.0',"vessel_type = 'fishing'",'MMSI'),
 'sar_all':('public-global-sar-presence:v4.0',None,None),
 'sar_unmatched':('public-global-sar-presence:v4.0',"matched = 'false'",None),
}
def token():
 value=os.environ.get('GFW_API_TOKEN','').strip()
 if not value:
  p=ROOT/'.secrets/gfw.env'
  if p.exists():
   for line in p.read_text(encoding='utf-8-sig').splitlines():
    if line.startswith('GFW_API_TOKEN='):value=line.split('=',1)[1].strip().strip('\"').strip("'")
 if not value:raise RuntimeError('Set GFW_API_TOKEN in .secrets/gfw.env')
 return value

def flatten(data):
 if not isinstance(data,dict) or not isinstance(data.get('entries'),list):
  raise ValueError('Unexpected report response: entries list required')
 if data.get('nextOffset') not in (None,0):raise ValueError('Paginated report: do not use an incomplete result')
 rows=[]
 for entry in data['entries']:
  if isinstance(entry,dict) and 'date' in entry:rows.append(entry)
  elif isinstance(entry,dict):
   for dataset,items in entry.items():
    if not isinstance(items,list):raise ValueError('Unknown report wrapper')
    rows.extend(dict(row,source_dataset=dataset) for row in items)
  else:raise ValueError('Unknown report entry')
 return rows

def request_spec(product,month):
 year,m=map(int,month.split('-'))
 end=f'{year:04d}-{m:02d}-{calendar.monthrange(year,m)[1]:02d}T23:59:59.999Z'
 dataset,filter_,group=PRODUCTS[product]
 params={'datasets[0]':dataset,'date-range':f'{month}-01T00:00:00.000Z,{end}',
  'format':'JSON','temporal-resolution':'MONTHLY','spatial-aggregation':'true','spatial-resolution':'HIGH'}
 if group:params['group-by']=group
 if filter_:params['filters[0]']=filter_
 return {'url':BASE+'report?'+urllib.parse.urlencode(params),'body':{'geojson':POLYGON},'params':params}

def download(product,month,credential):
 spec=request_spec(product,month)
 folder=ROOT/'data/raw/context'/product;folder.mkdir(parents=True,exist_ok=True)
 dest=folder/(month+'.json');manifest=folder/(month+'.request.json')
 if dest.exists() and manifest.exists():
  old=json.loads(manifest.read_text());raw=dest.read_bytes()
  if old['request']==spec and old['sha256']==hashlib.sha256(raw).hexdigest():
   flatten(json.loads(raw));print('Cached',product,month,flush=True);return
  raise ValueError('Cached request/hash mismatch; preserve and inspect before replacing')
 headers={'Authorization':'Bearer '+credential,'User-Agent':'Mozilla/5.0','Content-Type':'application/json'}
 req=urllib.request.Request(spec['url'],data=json.dumps(spec['body']).encode(),headers=headers)
 try:
  with urllib.request.urlopen(req,timeout=95) as response:raw=response.read()
 except urllib.error.HTTPError as error:
  # Stop rather than accidentally attributing another application's last report.
  raise RuntimeError(f'GFW HTTP {error.code} for {product} {month}. If timed out, inspect /4wings/last-report before resuming.') from None
 data=json.loads(raw);rows=flatten(data)
 for row in rows:
  if not str(row['date']).startswith(month):raise ValueError('Report returned a date outside the requested month')
 temp=dest.with_suffix('.part');temp.write_bytes(raw);temp.replace(dest)
 manifest.write_text(json.dumps({'request':spec,'retrieved_at':dt.datetime.now(dt.timezone.utc).isoformat(),
  'sha256':hashlib.sha256(raw).hexdigest(),'rows':len(rows)},indent=2),encoding='utf-8')
 print('Downloaded',product,month,len(rows),'rows',flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--start',default='2017-01');p.add_argument('--end',default='2026-08');p.add_argument('--products',nargs='+',choices=list(PRODUCTS),default=list(PRODUCTS));p.add_argument('--plan',action='store_true');a=p.parse_args()
 months=[f'{y}-{m:02d}' for y in range(2017,2027) for m in range(1,13) if a.start<=f'{y}-{m:02d}'<=a.end]
 if a.plan:
  print(json.dumps([{'product':prod,'month':month,**request_spec(prod,month)} for month in months for prod in a.products],indent=2));return
 credential=token()
 for month in months:
  for product in a.products:download(product,month,credential)
if __name__=='__main__':main()
