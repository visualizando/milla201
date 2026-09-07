"""Combine normalized exports from the same GFW dataset, retaining latest rows.

Example: python combine_downloads.py --inputs work/data_2017_2022 work/data_desde_2023
         --out outputs/datos_2017_2026 --start 2017-01-01 --end 2026-09-08
"""
import argparse
import csv
import json
from pathlib import Path
import gfw_disabling as g


def combine(inputs, out, start, end):
    records = {}
    configs = []
    for folder in map(Path, inputs):
        config = json.loads((folder / 'request.json').read_text())
        if config['probe']:
            raise ValueError('Cannot combine partial probes')
        configs.append(config)
        with (folder / 'events_normalized.csv').open(encoding='utf-8', newline='') as f:
            for row in csv.DictReader(f):
                key = row['gap_id']
                if key not in records or row['retrieved_at'] >= records[key]['retrieved_at']:
                    records[key] = row
    if len({(c['dataset'], c['vessel_type']) for c in configs}) != 1:
        raise ValueError('Inputs must share dataset version and vessel type')
    cursor = start
    for config in sorted(configs, key=lambda c: c['start']):
        if config['start'] > cursor:
            raise ValueError('Uncovered interval between downloads')
        cursor = max(cursor, config['end'])
    if cursor < end:
        raise ValueError('Inputs do not cover the requested end')
    rows = sorted(records.values(), key=lambda r: (r['gap_start_timestamp'], r['gap_id']))
    map_rows = [r for r in rows if start <= r['gap_start_timestamp'] < end
        and r['is_closed'].lower() == 'true' and r['intentional_disabling'].lower() != 'false'
        and r['gap_start_lat'] != '' and r['gap_start_lon'] != '']
    regional = [r for r in map_rows if -70 <= float(r['gap_start_lon']) <= -40
                and -60 <= float(r['gap_start_lat']) <= -30]
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    g.write_csv(out / 'ais_disabling_events.csv', map_rows, g.LEGACY)
    g.write_csv(out / 'events_normalized.csv', rows, g.LEGACY + g.EXTRA)
    g.write_csv(out / 'ais_disabling_events_atlantico.csv', regional, g.LEGACY)
    g.atomic_json(out / 'summary.json', {'inputs': configs, 'unique_normalized': len(rows),
        'map_rows': len(map_rows), 'regional_rows': len(regional),
        'start_inclusive': start, 'end_exclusive': end,
        'min_start': min((r['gap_start_timestamp'] for r in map_rows),default=None),
        'max_start': max((r['gap_start_timestamp'] for r in map_rows),default=None),
        'note': 'Same dataset version; latest retrieved representation per ID. Regional bounding box is not the EEZ.'})
    print(f'{len(map_rows)} global events; {len(regional)} regional events')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs', nargs='+', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--start', required=True)
    p.add_argument('--end', required=True)
    a = p.parse_args()
    combine(a.inputs,a.out,a.start,a.end)
