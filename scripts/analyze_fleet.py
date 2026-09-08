"""Repeat MMSI and observed gap endpoints. Requires shapely>=2; no inferred tracks."""
import argparse, collections, csv, hashlib, json
from pathlib import Path
from shapely.geometry import shape, Point
from shapely.prepared import prep
from download_context import ROOT, flatten

def write_csv(path, rows):
    if not rows: return
    with path.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--events', nargs='+', required=True); a=p.parse_args()
    boundary=ROOT/'data/raw/fleet/eez_region.json'
    feature=json.loads(boundary.read_text()); geom=shape(feature['geometry'])
    assert geom.is_valid, 'Invalid EEZ geometry: inspect before analysis'
    zone=prep(geom)
    regional_ids={r['gap_id'] for r in csv.DictReader((ROOT/'data/processed/ais_disabling_events_atlantico.csv').open(encoding='utf-8'))}
    events={}
    for filename in a.events:
        with open(filename, encoding='utf-8-sig', newline='') as f:
            for r in csv.DictReader(f):
                if r['gap_id'] in regional_ids:
                    if r['gap_id'] in events:
                        assert all(events[r['gap_id']][k]==r[k] for k in ('mmsi','gap_start_timestamp','gap_end_timestamp','gap_start_lat','gap_start_lon','gap_end_lat','gap_end_lon')), 'Conflicting duplicate event'
                        continue
                    for side in ('start','end'):
                        lon,lat=r[f'gap_{side}_lon'],r[f'gap_{side}_lat']
                        r[f'{side}_inside_eez']=zone.covers(Point(float(lon),float(lat))) if lon and lat else None
                    events[r['gap_id']]=r
    assert set(events)==regional_ids, 'Missing normalized event records'
    groups=collections.defaultdict(list)
    for r in events.values(): groups[r['mmsi']].append(r)
    vessels=[]; annual=[]
    for mmsi, rows in groups.items():
        years=collections.Counter(r['gap_start_timestamp'][:4] for r in rows)
        names=collections.Counter(r['vessel_name'] for r in rows if r['vessel_name'])
        flags=sorted({r['flag'] or 'UNKNOWN' for r in rows})
        v={'mmsi':mmsi, 'name':names.most_common(1)[0][0] if names else '',
           'names':' | '.join(sorted(names)), 'flags':' | '.join(flags),
           'vessel_ids':' | '.join(sorted({r['vessel_id'] for r in rows if r['vessel_id']})),
           'gaps':len(rows), 'years_with_gaps':len(years),
           'first_gap':min(r['gap_start_timestamp'] for r in rows), 'last_gap':max(r['gap_start_timestamp'] for r in rows),
           'start_inside_eez':sum(r['start_inside_eez'] is True for r in rows),
           'end_inside_eez':sum(r['end_inside_eez'] is True for r in rows),
           'either_endpoint_inside_eez':sum(r['start_inside_eez'] is True or r['end_inside_eez'] is True for r in rows)}
        vessels.append(v)
        for year,count in sorted(years.items()):
            yr=[r for r in rows if r['gap_start_timestamp'].startswith(year)]
            annual.append({'mmsi':mmsi,'name':v['name'],'year':int(year),'gaps':count,
                'flags':' | '.join(sorted({r['flag'] or 'UNKNOWN' for r in yr})),
                'either_endpoint_inside_eez':sum(r['start_inside_eez'] is True or r['end_inside_eez'] is True for r in yr)})
    vessels.sort(key=lambda r:(-r['gaps'],r['mmsi']))
    seen=set(); previous=set(); transitions=[]
    for year in range(2017,2027):
        ys=[r for r in annual if r['year']==year]; current={r['mmsi'] for r in ys}
        transitions.append({'year':year,'mmsi':len(current),'gaps':sum(r['gaps'] for r in ys),
            'seen_in_earlier_year':len(current & seen),'seen_in_previous_year':len(current & previous),
            'first_seen_with_gap':len(current-seen), 'returning_pct':100*len(current&seen)/len(current) if current else None,
            'partial_year':year==2026})
        seen |= current; previous=current
    flags=[]
    for flag in sorted({r['flag'] or 'UNKNOWN' for r in events.values()}):
        rows=[r for r in events.values() if (r['flag'] or 'UNKNOWN')==flag]
        flags.append({'flag':flag,'gaps':len(rows),'mmsi':len({r['mmsi'] for r in rows}),
            'either_endpoint_inside_eez':sum(r['start_inside_eez'] is True or r['end_inside_eez'] is True for r in rows)})
    flags.sort(key=lambda r:-r['gaps'])
    endpoints=[{k:r[k] for k in ('gap_id','mmsi','vessel_id','vessel_name','flag','gap_start_timestamp','gap_end_timestamp',
        'gap_start_lat','gap_start_lon','gap_end_lat','gap_end_lon','start_inside_eez','end_inside_eez')} for r in events.values()]
    out=ROOT/'data/processed'; out.mkdir(exist_ok=True)
    write_csv(out/'fleet-vessels.csv',vessels); write_csv(out/'fleet-annual.csv',annual)
    write_csv(out/'fleet-gap-endpoints.csv',endpoints); write_csv(out/'fleet-flags.csv',flags)
    result={'scope':'Regional gaps whose start is within 70–40 W, 60–30 S; 2017–2026-09-03',
        'identity_unit':'MMSI; not necessarily a unique physical vessel. Names and flags from event records.',
        'eez':{'dataset':'public-eez-areas','id':8466,'properties':feature['properties'],
            'sha256':hashlib.sha256(boundary.read_bytes()).hexdigest(),'bounds':geom.bounds,
            'method':'Full unsimplified polygon, covers(start/end point); no route interpolation. Boundary points included.'},
        'summary':{'gaps':len(events),'mmsi':len(vessels),'mmsi_multiple_years':sum(v['years_with_gaps']>1 for v in vessels),
            'gaps_repeat_mmsi':sum(v['gaps'] for v in vessels if v['years_with_gaps']>1),
            'top20_gaps':sum(v['gaps'] for v in vessels[:20]),
            'gaps_either_endpoint_inside_eez':sum(v['either_endpoint_inside_eez'] for v in vessels)},
        'transitions':transitions,'flags':flags,'vessels':vessels,'annual':annual}
    (out/'fleet-analysis.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(json.dumps({'summary':result['summary'],'transitions':transitions,'top12':vessels[:12],'flags':flags[:10]},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
