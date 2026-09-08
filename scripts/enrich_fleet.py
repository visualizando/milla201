"""Join recurring-gap MMSI to monthly EEZ presence and a documented registry sample."""
import collections, json
from download_context import ROOT, flatten
from analyze_fleet import write_csv

def main():
    out=ROOT/'data/processed'; data=json.loads((out/'fleet-analysis.json').read_text(encoding='utf-8'))
    by_mmsi={v['mmsi']:v for v in data['vessels']}; monthly=[]; unknown_hours=0
    for year in range(2017,2027):
        path=ROOT/f'data/raw/fleet/eez_presence/{year}.json'
        assert path.exists(), f'Missing EEZ report {year}'
        grouped=collections.Counter()
        for r in flatten(json.loads(path.read_text())):
            mmsi=str(r.get('mmsi') or '')
            if not mmsi or mmsi=='0': unknown_hours+=float(r['hours']); continue
            assert r['date'][:4]==str(year)
            grouped[(mmsi,r['date'])]+=float(r['hours'])
        for (mmsi,month),hours in grouped.items():
            if hours>0:
                monthly.append({'mmsi':mmsi,'month':month,'hours':hours,'has_regional_gap_in_dataset':mmsi in by_mmsi})
    selected=collections.defaultdict(list)
    for r in monthly:
        if r['mmsi'] in by_mmsi: selected[r['mmsi']].append(r)
    for mmsi,v in by_mmsi.items():
        rows=selected.get(mmsi,[])
        v['eez_presence_months']=len(rows)
        v['eez_presence_years']=len({r['month'][:4] for r in rows})
        v['eez_presence_year_list']=' | '.join(sorted({r['month'][:4] for r in rows}))
        v['eez_presence_first_month']=min((r['month'] for r in rows),default='')
        v['eez_presence_last_month']=max((r['month'] for r in rows),default='')
        v['registry_geartypes']=''; v['registry_lengths_m']=''; v['registry_imos']=''
        v['identity_search_entries']=''; v['registry_status']='Not queried; sample limited to top 20 MMSI by gaps'
        identity=ROOT/f'data/raw/fleet/identity/{mmsi}.json'
        if identity.exists():
            entries=json.loads(identity.read_text())['entries']; registry=[]
            for e in entries:
                registry.extend(r for r in e.get('registryInfo',[]) if str(r.get('ssvid'))==mmsi)
            v['identity_search_entries']=len(entries)
            v['registry_status']='Registry candidates for this MMSI; not a historical identity resolution' if registry else 'No registry record with exact MMSI'
            v['registry_geartypes']=' | '.join(sorted({g for r in registry for g in r.get('geartypes',[])}))
            v['registry_lengths_m']=' | '.join(sorted({str(r['lengthM']) for r in registry if r.get('lengthM')}))
            v['registry_imos']=' | '.join(sorted({str(r['imo']) for r in registry if r.get('imo')}))
    data['eez_presence']={'scope':'All fishing-vessel MMSI in monthly EEZ presence, January 2017–August 2026',
        'all_mmsi':len({r['mmsi'] for r in monthly}),'with_regional_gaps':len(selected),
        'hours_without_mmsi':unknown_hours,'method':'Positive presence in spatially aggregated HIGH-resolution cells. Months are not visits or border crossings. Gap flags may differ from presence-time flags.',
        'annual':[{'year':year,'all_mmsi':len({r['mmsi'] for r in monthly if r['month'].startswith(str(year))})} for year in range(2017,2027)]}
    data['presence_by_vessel_year']=[{'mmsi':mmsi,'year':int(year),'months':sum(r['month'].startswith(year) for r in rows)}
        for mmsi,rows in selected.items() for year in sorted({r['month'][:4] for r in rows})]
    write_csv(out/'fleet-vessels.csv',data['vessels']); write_csv(out/'eez-presence-monthly.csv',monthly)
    (out/'fleet-analysis.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    candidates=sorted([v for v in data['vessels'] if v['flags'] not in ('ARG','UNKNOWN') and 'ARG' not in v['flags'] and v['eez_presence_years']>1],key=lambda v:(-v['eez_presence_years'],-v['eez_presence_months']))
    print(json.dumps({'presence':data['eez_presence'],'candidates':[{k:v[k] for k in ('mmsi','name','flags','gaps','eez_presence_years','eez_presence_months','either_endpoint_inside_eez')} for v in candidates[:15]]},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
