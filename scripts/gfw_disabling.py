"""Download GFW AIS-off events and export the exact Welch/Observable CSV schema.

Python 3.10+, standard library only. Token: GFW_API_TOKEN environment variable
or a hidden prompt. Never put the token in Observable. See README.md.
"""
import argparse
import csv
import datetime as dt
import getpass
import hashlib
import json
import math
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://gateway.api.globalfishingwatch.org/v3/events'
DATASET = 'public-global-gaps-events:v4.0'
LEGACY = ['gap_id', 'mmsi', 'vessel_class', 'flag', 'vessel_length_m',
          'vessel_tonnage_gt', 'gap_start_timestamp', 'gap_start_lat',
          'gap_start_lon', 'gap_start_distance_from_shore_m',
          'gap_end_timestamp', 'gap_end_lat', 'gap_end_lon',
          'gap_end_distance_from_shore_m', 'gap_hours']
EXTRA = ['vessel_id', 'vessel_name', 'vessel_type', 'event_type', 'is_closed',
         'intentional_disabling', 'source_dataset', 'retrieved_at',
         'duration_from_timestamps_hours', 'duration_difference_hours',
         'event_lat', 'event_lon', 'eez_ids', 'regions_json', 'gap_json',
         'quality_notes']


def number(x):
    if x is None or x == '':
        return None
    n = float(x)
    if not math.isfinite(n):
        raise ValueError('Nonfinite number')
    return n


def timestamp(value):
    if not value:
        return None
    t = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if t.tzinfo is None:
        raise ValueError('Timestamp without timezone: ' + value)
    return t.astimezone(dt.timezone.utc)


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def normalize(event, dataset=DATASET, retrieved_at=None):
    if str(event.get('type', '')).upper() not in ('GAP', 'GAP_START'):
        raise ValueError('Unexpected event type; refusing to normalize as GAP')
    if not event.get('id'):
        raise ValueError('Missing event ID')
    row = dict.fromkeys(LEGACY + EXTRA)
    gap, vessel = event.get('gap') or {}, event.get('vessel') or {}
    distances = event.get('distances') or {}
    start, end = timestamp(event.get('start')), timestamp(event.get('end'))
    if start and end and end < start:
        raise ValueError('Event end precedes start')
    closed = gap.get('isClosed', event.get('isClosed'))
    if closed is None:
        closed = bool(end) and str(event.get('type')).upper() != 'GAP_START'
    notes = []
    row.update(gap_id=str(event['id']), mmsi=str(vessel['ssvid']) if vessel.get('ssvid') is not None else None,
               flag=vessel.get('flag'), vessel_id=vessel.get('id'),
               vessel_name=vessel.get('name'), vessel_type=vessel.get('type'),
               event_type=event.get('type'), is_closed=closed,
               intentional_disabling=gap.get('intentionalDisabling'),
               source_dataset=dataset, retrieved_at=retrieved_at,
               gap_start_timestamp=start.isoformat(sep=' ') if start else None,
               gap_end_timestamp=end.isoformat(sep=' ') if end else None)
    # The Events API's broad 'fishing' type is NOT Welch's fishing gear class.
    notes.append('legacy_class_length_tonnage_unavailable_in_events_schema')
    for side, position in [('start', gap.get('offPosition')), ('end', gap.get('onPosition'))]:
        p = position or {}
        lat, lon = number(p.get('lat')), number(p.get('lon'))
        if lat is not None and not -90 <= lat <= 90 or lon is not None and not -180 <= lon <= 180:
            raise ValueError('Invalid geographic coordinates')
        row[f'gap_{side}_lat'], row[f'gap_{side}_lon'] = lat, lon
        d = number(distances.get(side + 'DistanceFromShoreKm'))
        row[f'gap_{side}_distance_from_shore_m'] = d * 1000 if d is not None else None
        if lat is None or lon is None:
            notes.append('missing_' + side + '_position')
    hours = number(gap.get('durationHours'))
    computed = (end - start).total_seconds() / 3600 if start and end and closed else None
    if hours is not None and hours < 0:
        raise ValueError('Negative duration')
    row['gap_hours'] = hours if hours is not None else computed
    row['duration_from_timestamps_hours'] = computed
    row['duration_difference_hours'] = hours - computed if hours is not None and computed is not None else None
    if not closed:
        notes.append('open_gap_duration_not_final')
    if gap.get('intentionalDisabling') is False:
        notes.append('source_explicitly_marks_nonintentional')
    regions = event.get('regions') or {}
    row.update(event_lat=(event.get('position') or {}).get('lat'),
               event_lon=(event.get('position') or {}).get('lon'),
               eez_ids=';'.join(map(str, regions.get('eez') or [])),
               regions_json=json.dumps(regions, ensure_ascii=False),
               gap_json=json.dumps(gap, ensure_ascii=False), quality_notes=';'.join(notes))
    return row


def months(start, end):
    a, stop = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    if a >= stop:
        raise ValueError('start must precede end (exclusive)')
    while a < stop:
        b = min((a.replace(day=28) + dt.timedelta(days=4)).replace(day=1), stop)
        yield a.isoformat(), b.isoformat()
        a = b


def next_offset(page, offset):
    entries = page.get('entries')
    if not isinstance(entries, list) or 'total' not in page:
        raise ValueError('Unexpected API pagination schema')
    total = int(page['total'])
    if offset + len(entries) >= total:
        return None
    if not entries:
        raise ValueError('Empty page before total reached; incomplete response')
    nxt = page.get('nextOffset')
    if nxt is None or int(nxt) <= offset:
        raise ValueError('Missing or nonadvancing nextOffset')
    return int(nxt)


def request_page(params, token):
    url = BASE + '?' + urllib.parse.urlencode(params)
    for attempt in range(5):
        req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token,
                                                   'Accept': 'application/json',
                                                   'User-Agent': 'gfw-disabling-research/1.0'})
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise RuntimeError(f'GFW HTTP {exc.code}: verify token / dataset access.') from None
            if exc.code == 429:
                raise RuntimeError('GFW quota reached (429). Resume later using the same output folder.') from None
            if exc.code not in (500, 502, 503, 504, 524) or attempt == 4:
                raise RuntimeError(f'GFW HTTP {exc.code}; cached pages retained.') from None
        except (urllib.error.URLError, TimeoutError):
            if attempt == 4:
                raise RuntimeError('GFW connection failed; cached pages retained.') from None
        time.sleep(2 ** attempt)


def atomic_json(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


def download(args):
    windows = list(months(args.start, args.end))
    folder = Path(args.out)
    raw = folder / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    config = dict(start=args.start, end=args.end, dataset=args.dataset,
                  vessel_type=args.vessel_type, limit=args.limit, probe=args.probe)
    manifest_path = folder / 'request.json'
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != config:
        raise ValueError('Output folder has different request settings; choose a new folder.')
    atomic_json(manifest_path, config)
    token = None
    counts = []
    for start, end in windows:
        offset = 0
        seen_pages = set()
        while True:
            params = {'datasets[0]': args.dataset, 'start-date': start,
                      'end-date': end, 'offset': offset, 'limit': args.limit,
                      'include-regions': 'true'}
            if args.vessel_type != 'ALL':
                params['vessel-types[0]'] = args.vessel_type
            path = raw / f'{start}_{end}_{offset:09d}.json'
            if path.exists():
                envelope = json.loads(path.read_text(encoding='utf-8'))
                if envelope['request'] != params:
                    raise ValueError('Cache request mismatch')
            else:
                if token is None:
                    token = os.environ.get('GFW_API_TOKEN') or getpass.getpass('GFW API token (hidden): ')
                    if not token.strip():
                        raise ValueError('GFW API token required')
                page = request_page(params, token.strip())
                next_offset(page, offset)  # Validate before caching.
                envelope = {'request': params, 'retrieved_at': now(), 'response': page}
                atomic_json(path, envelope)
                time.sleep(0.25)
            page = envelope['response']
            signature = hashlib.sha256(json.dumps(page['entries'], sort_keys=True).encode()).hexdigest()
            if signature in seen_pages and page['entries']:
                raise ValueError('Server repeated a page; refusing incomplete download')
            seen_pages.add(signature)
            if offset == 0:
                counts.append({'start': start, 'end_exclusive': end, 'overlapping_events': page['total'],
                               'metadata': page.get('metadata'), 'retrieved_at': envelope['retrieved_at']})
                print(start, 'matching events:', page['total'])
            nxt = next_offset(page, offset)
            if args.probe or nxt is None:
                break
            offset = nxt
    atomic_json(folder / 'coverage.json', {'probe_only': args.probe, 'windows': counts,
                'note': 'Counts may overlap between months. Zero does not prove absence of activity or complete coverage.'})
    if args.probe:
        print('Probe complete. No replacement CSV produced; these are partial pages.')
    else:
        export(folder, folder, None, 'start')


def in_bbox(row, bbox, mode):
    if bbox is None:
        return True
    west, south, east, north = bbox
    sides = ['start', 'end'] if mode == 'either' else [mode]
    for side in sides:
        lon, lat = row[f'gap_{side}_lon'], row[f'gap_{side}_lat']
        if lon is None or lat is None:
            continue
        longitude_ok = west <= lon <= east if west <= east else lon >= west or lon <= east
        if longitude_ok and south <= lat <= north:
            return True
    return False


def write_csv(path, rows, fields):
    temp = path.with_suffix('.tmp')
    with temp.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    temp.replace(path)


def export(source, out, bbox, mode):
    config = json.loads((source / 'request.json').read_text())
    if config['probe']:
        raise ValueError('Cannot export an incomplete coverage probe')
    records = {}
    # Confirm that every requested window has its complete pagination chain.
    for start, end in months(config['start'], config['end']):
        offset = 0
        while True:
            path = source / 'raw' / f'{start}_{end}_{offset:09d}.json'
            envelope = json.loads(path.read_text(encoding='utf-8'))
            page = envelope['response']
            for event in page['entries']:
                row = normalize(event, config['dataset'], envelope['retrieved_at'])
                key = row['gap_id']
                # Monthly overlap can repeat events; retain newest retrieved representation.
                if key not in records or row['retrieved_at'] >= records[key]['retrieved_at']:
                    records[key] = row
            offset = next_offset(page, offset)
            if offset is None:
                break
    rows = sorted((r for r in records.values() if in_bbox(r, bbox, mode)),
                  key=lambda r: (r['gap_start_timestamp'] or '', r['gap_id']))
    # Open gaps and missing OFF positions stay in the full export, not the map CSV.
    start_bound = timestamp(config['start'] + 'T00:00:00Z')
    end_bound = timestamp(config['end'] + 'T00:00:00Z')
    map_rows = [r for r in rows if r['is_closed'] and r['gap_start_timestamp']
                and start_bound <= timestamp(r['gap_start_timestamp']) < end_bound
                and r['gap_start_lat'] is not None
                and r['gap_start_lon'] is not None and r['intentional_disabling'] is not False]
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / 'ais_disabling_events.csv', map_rows, LEGACY)
    write_csv(out / 'events_normalized.csv', rows, LEGACY + EXTRA)
    starts = [r['gap_start_timestamp'] for r in rows if r['gap_start_timestamp']]
    ends = [r['gap_end_timestamp'] for r in rows if r['gap_end_timestamp']]
    atomic_json(out / 'summary.json', {'request': config, 'bbox': bbox, 'bbox_mode': mode,
        'unique_events': len(rows), 'map_events': len(map_rows),
        'min_observed_start': min(starts, default=None), 'max_observed_start': max(starts, default=None),
        'max_observed_end': max(ends, default=None),
        'missing_by_field': {k: sum(r[k] is None for r in rows) for k in LEGACY},
        'note': 'Observed dates do not certify full source coverage. Bounding box is not an EEZ polygon.'})
    print(f'Exported {len(map_rows)} map events; {len(rows)} normalized events to {out}')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest='command', required=True)
    d = commands.add_parser('download')
    d.add_argument('--start', required=True)
    d.add_argument('--end', required=True, help='Exclusive YYYY-MM-DD')
    d.add_argument('--dataset', default=DATASET)
    d.add_argument('--vessel-type', default='FISHING', choices=['FISHING', 'ALL', 'CARRIER', 'SUPPORT'])
    d.add_argument('--limit', type=int, default=1000)
    d.add_argument('--probe', action='store_true', help='First page per month only; counts, no CSV')
    d.add_argument('--out', required=True)
    n = commands.add_parser('export')
    n.add_argument('--source', required=True)
    n.add_argument('--out', required=True)
    n.add_argument('--bbox', type=float, nargs=4, metavar=('WEST', 'SOUTH', 'EAST', 'NORTH'))
    n.add_argument('--bbox-mode', choices=['start', 'end', 'either'], default='start')
    args = p.parse_args()
    if args.command == 'download':
        if args.limit < 1:
            p.error('--limit must be positive')
        download(args)
    else:
        if args.bbox:
            w, s, e, n = args.bbox
            if not (-180 <= w <= 180 and -180 <= e <= 180 and -90 <= s < n <= 90):
                p.error('Invalid bounding box')
        export(Path(args.source), Path(args.out), args.bbox, args.bbox_mode)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError) as exc:
        raise SystemExit(str(exc))
