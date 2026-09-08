"""Derive all public statistics from event-level CSV; stdlib only."""
import csv, gzip, json, math, statistics, argparse
from pathlib import Path
from collections import Counter, defaultdict

ROOT=Path(__file__).resolve().parents[1]
def prepare(source):
    target=ROOT/'data/processed'
    target.mkdir(parents=True,exist_ok=True)
    with Path(source).open(encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==len({r['gap_id'] for r in rows}), 'Duplicate IDs'
    cells=Counter()
    groups=defaultdict(list)
    region=[]
    for r in rows:
        year=int(r['gap_start_timestamp'][:4]); month=r['gap_start_timestamp'][:7]
        lon=float(r['gap_start_lon']); lat=float(r['gap_start_lat'])
        cells[(year,math.floor(lon*2)/2+.25,math.floor(lat*2)/2+.25)]+=1
        groups[('global',month)].append(r)
        if -70<=lon<=-40 and -60<=lat<=-30:
            groups[('region',month)].append(r)
            region.append(r)
    monthly=[]
    for area in ['global','region']:
        for year in range(2017,2027):
            for m in range(1,13):
                month=f'{year}-{m:02d}'
                if month>'2026-09':continue
                rs=groups[(area,month)]
                durations=[float(r['gap_hours']) for r in rs]
                monthly.append({'area':area,'month':month,'events':len(rs),
                    'vessels':len({r['mmsi'] for r in rs}),
                    'medianHours':round(statistics.median(durations),1) if durations else None,
                    'over30days':sum(h>720 for h in durations),'partial':month=='2026-09'})
    flags=Counter(r['flag'] or 'Sin dato' for r in region)
    result={'snapshot':'2026-09-07','latestStart':max(r['gap_start_timestamp'] for r in rows),
        'dataset':'public-global-gaps-events:v4.0','total':len(rows),'regionalTotal':len(region),
        'bbox':[-70,-60,-40,-30], 'monthly':monthly,
        'flags':[{'flag':k,'events':v} for k,v in flags.most_common()],
        'positions':[[int(r['gap_start_timestamp'][:4]),float(r['gap_start_lon']),float(r['gap_start_lat'])] for r in rows],
        'regional':[[int(r['gap_start_timestamp'][:4]),round(float(r['gap_start_lon']),4),round(float(r['gap_start_lat']),4)] for r in region]}
    (target/'site-data.json').write_text(json.dumps(result,separators=(',',':'),ensure_ascii=False),encoding='utf-8')
    with gzip.open(target/'ais_disabling_events_2017_2026.csv.gz','wb') as f:
        f.write(Path(source).read_bytes())
    with (target/'ais_disabling_events_atlantico.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(region)
    with (target/'monthly.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(monthly[0]));w.writeheader();w.writerows(monthly)
    assert sum(r['events'] for r in monthly if r['area']=='global')==len(rows)
    print(f'Prepared {len(rows):,} global and {len(region):,} regional events')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);prepare(p.parse_args().source)
