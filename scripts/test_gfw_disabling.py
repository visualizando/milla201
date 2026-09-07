"""Offline tests with synthetic events, not a downloaded GFW dataset."""
import copy
import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import gfw_disabling as g


def event():
    return {'id': 'test-gap', 'type': 'gap', 'start': '2025-12-31T20:00:00Z',
            'end': '2026-01-01T10:00:00Z',
            'position': {'lat': 0, 'lon': 0},
            'vessel': {'id': 'test-vessel', 'ssvid': '001234567', 'flag': 'ARG', 'type': 'fishing'},
            'gap': {'durationHours': 14, 'intentionalDisabling': True,
                    'offPosition': {'lat': '-45', 'lon': '-60'},
                    'onPosition': {'lat': -44, 'lon': -59}},
            'distances': {'startDistanceFromShoreKm': 100, 'endDistanceFromShoreKm': 0}}


class Tests(unittest.TestCase):
    def test_fields_units_identity(self):
        r = g.normalize(event())
        self.assertEqual(r['mmsi'], '001234567')
        self.assertEqual(r['gap_start_distance_from_shore_m'], 100000)
        self.assertEqual(r['gap_end_distance_from_shore_m'], 0)
        self.assertEqual(r['gap_hours'], 14)
        self.assertEqual(r['duration_difference_hours'], 0)
        self.assertIsNone(r['vessel_class'])
        self.assertEqual(r['vessel_type'], 'fishing')

    def test_no_fabricated_off_location(self):
        e = event()
        del e['gap']['offPosition']
        self.assertIsNone(g.normalize(e)['gap_start_lat'])

    def test_open_gap(self):
        e = event()
        e['end'] = ''
        del e['gap']['onPosition']
        r = g.normalize(e)
        self.assertFalse(r['is_closed'])
        self.assertIsNone(r['gap_end_lat'])
        self.assertIsNone(r['duration_from_timestamps_hours'])

    def test_invalid(self):
        e = event()
        e['gap']['offPosition']['lat'] = 100
        with self.assertRaises(ValueError):
            g.normalize(e)
        e = event()
        e['end'] = '2020-01-01T00:00:00Z'
        with self.assertRaises(ValueError):
            g.normalize(e)

    def test_months(self):
        self.assertEqual(list(g.months('2024-02-28', '2024-03-02')),
                         [('2024-02-28', '2024-03-01'), ('2024-03-01', '2024-03-02')])

    def test_pagination(self):
        self.assertEqual(g.next_offset({'entries': [1], 'total': 3, 'nextOffset': 1}, 0), 1)
        self.assertIsNone(g.next_offset({'entries': [1], 'total': 3}, 2))
        with self.assertRaises(ValueError):
            g.next_offset({'entries': [], 'total': 3}, 0)
        with self.assertRaises(ValueError):
            g.next_offset({'entries': [1], 'total': 3, 'nextOffset': 0}, 0)

    def test_bbox_modes(self):
        r = g.normalize(event())
        self.assertTrue(g.in_bbox(r, [-61, -46, -59.5, -44.5], 'start'))
        self.assertFalse(g.in_bbox(r, [-61, -46, -59.5, -44.5], 'end'))
        self.assertTrue(g.in_bbox(r, [-61, -46, -59.5, -44.5], 'either'))
        r['gap_start_lon'] = 179
        self.assertTrue(g.in_bbox(r, [170, -46, -170, -44], 'start'))

    def test_end_to_end_cache_dedup_resume_and_headers(self):
        import argparse
        with tempfile.TemporaryDirectory() as temp:
            args = argparse.Namespace(start='2025-12-01', end='2026-02-01', out=temp,
                dataset=g.DATASET, vessel_type='FISHING', limit=1, probe=False)
            e2 = copy.deepcopy(event())
            e2['id'] = 'test-2'
            responses = [
                {'entries': [event()], 'total': 2, 'nextOffset': 1},
                {'entries': [e2], 'total': 2},
                {'entries': [event()], 'total': 1}]
            with patch.object(g, 'request_page', side_effect=responses) as mock, \
                 patch.dict(g.os.environ, {'GFW_API_TOKEN': 'synthetic-test-token'}), \
                 patch.object(g.time, 'sleep'):
                g.download(args)
                self.assertEqual(mock.call_count, 3)
                g.download(args)
                self.assertEqual(mock.call_count, 3)
            with (Path(temp) / 'ais_disabling_events.csv').open() as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, g.LEGACY)
                self.assertEqual(len(list(reader)), 2)
            (Path(temp) / 'raw' / '2025-12-01_2026-01-01_000000001.json').unlink()
            with self.assertRaises(FileNotFoundError):
                g.export(Path(temp), Path(temp) / 'incomplete', None, 'start')


if __name__ == '__main__':
    unittest.main()
