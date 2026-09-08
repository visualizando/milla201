"""Join completed 4Wings reports to gaps. Missing reports remain null, never zero.
Presence hours / 24 are equivalent observed vessel-days, not calendar days.
SAR unmatched share is descriptive; no coverage-adjusted claim without footprints.
"""
import csv,json,math
from collections import defaultdict
from pathlib import Path
from download_context import flatten,PRODUCTS
ROOT=Path(__file__).resolve().parents[1]

def divide(a,b,multiplier=1):return a/b*multiplier if a is not None and b is not None and b>0 else None

def load(product,month):
 p=ROOT/'data/raw/context'/product/(month+'.json')
 if not p.exists():return None
 rows=flatten(json.loads(p.read_text(encoding='utf-8')))
 if any(not str(r['date']).startswith(month) for r in rows):raise ValueError('Unexpected date')
 return rows

def hours_by_mmsi(rows):
 if rows is None:return None
 totals=defaultdict(float)
 for row in rows:
  hours=float(row['hours'])
  if not math.isfinite(hours) or hours<0:raise ValueError('Invalid hours')
  mmsi=str(row.get('mmsi') or '').strip()
  if not mmsi:raise ValueError('MMSI missing: cannot compute distinct fleet or overlap')
  totals[mmsi]+=hours
 return dict(totals)

def summarize(month,gaps,presence,effort,sar_all,sar_unmatched):
 seen=set(presence or {});gap_vessels={r['mmsi'] for r in gaps if r['mmsi']}
 ph=sum(presence.values()) if presence is not None else None
 fh=sum(effort.values()) if effort is not None else None
 matched_gaps=sum(r['mmsi'] in seen for r in gaps) if presence is not None else None
 overlap=len(gap_vessels & seen) if presence is not None else None
 if sar_all is not None and sar_unmatched is not None and sar_unmatched>sar_all:raise ValueError('Unmatched detections exceed all detections')
 return {'month':month,'gaps':len(gaps),'gap_mmsi':len(gap_vessels),
  'presence_hours':ph,'observed_equivalent_vessel_days':ph/24 if ph is not None else None,
  'apparent_fishing_hours':fh,'presence_mmsi':len(seen) if presence is not None else None,
  'fishing_mmsi':len(effort) if effort is not None else None,
  'gap_mmsi_in_observed_fleet':overlap,'gaps_in_observed_fleet':matched_gaps,
  'gap_mmsi_missing_from_presence':len(gap_vessels-seen) if presence is not None else None,
  'gaps_per_1000_observed_vessel_days':divide(matched_gaps,ph,24000),
  'observed_fleet_with_gaps_pct':divide(overlap,len(seen) if presence is not None else None,100),
  'sar_detections':sar_all,'sar_unmatched':sar_unmatched,
  'sar_unmatched_pct':divide(sar_unmatched,sar_all,100),
  'sar_coverage_adjusted_density':None}

def main():
 with (ROOT/'data/interim/ais_disabling_events.csv').open(encoding='utf-8') as f:
  gaps=[r for r in csv.DictReader(f) if -70<=float(r['gap_start_lon'])<=-40 and -60<=float(r['gap_start_lat'])<=-30]
 grouped=defaultdict(list)
 for r in gaps:grouped[r['gap_start_timestamp'][:7]].append(r)
 months=[f'{y}-{m:02d}' for y in range(2017,2027) for m in range(1,13) if f'{y}-{m:02d}'<='2026-08']
 output=[];missing=[]
 for month in months:
  reports={prod:load(prod,month) for prod in PRODUCTS}
  missing.extend(f'{prod}/{month}' for prod,rows in reports.items() if rows is None)
  def detections(prod):
   if reports[prod] is None:return None
   values=[float(r['detections']) for r in reports[prod]]
   if any(not math.isfinite(v) or v<0 for v in values):raise ValueError('Invalid detections')
   return sum(values)
  output.append(summarize(month,grouped[month],hours_by_mmsi(reports['presence']),hours_by_mmsi(reports['effort']),detections('sar_all'),detections('sar_unmatched')))
 dest=ROOT/'data/processed';dest.mkdir(exist_ok=True)
 with (dest/'context-monthly.csv').open('w',encoding='utf-8',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(output[0]));writer.writeheader();writer.writerows(output)
 (dest/'context-analysis.json').write_text(json.dumps({'status':'missing_reports' if missing else 'descriptive_reports_complete',
  'missing_reports':missing,'monthly':output,'sar_coverage_status':'requires_processed_scene_footprints'},ensure_ascii=False,indent=2),encoding='utf-8')
 print(f'Calculated {len(output)} monthly rows; {len(missing)} reports missing. No missing value replaced with zero.')
if __name__=='__main__':main()
