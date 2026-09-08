"""Explicit allowlist: only site assets and derived public data reach Pages."""
from pathlib import Path
import shutil, json
ROOT=Path(__file__).resolve().parents[1]
context=json.loads((ROOT/'data/processed/context-analysis.json').read_text(encoding='utf-8'))
assert not context['missing_reports'], 'Context downloads incomplete; do not publish partial charts'
dest=ROOT/'docs'
dest.mkdir(exist_ok=True)
for p in (ROOT/'site').rglob('*'):
    if p.is_file():
        q=dest/p.relative_to(ROOT/'site');q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
for name in ['site-data.json','ais_disabling_events_2017_2026.csv.gz','ais_disabling_events_atlantico.csv','monthly.csv','context-analysis.json','context-monthly.csv','context-periods.csv','fleet-analysis.json','fleet-vessels.csv','fleet-annual.csv','fleet-flags.csv','fleet-gap-endpoints.csv','eez-presence-monthly.csv']:
    p=ROOT/'data/processed'/name
    if not p.exists():raise SystemExit(f'Missing {p}; run prepare_data.py first')
    q=dest/'data'/name;q.parent.mkdir(exist_ok=True);shutil.copyfile(p,q)
(dest/'.nojekyll').write_text('')
for p in dest.rglob('*'):
    if p.is_file() and p.suffix in ['.html','.js','.json','.css']:
        assert 'eyJhbGciOi' not in p.read_text(encoding='utf-8'), 'Potential credential in public files'
print('Built docs/ for GitHub Pages; raw data and credentials excluded')
