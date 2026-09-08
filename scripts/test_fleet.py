"""Checks identity joins, event counts, geography and partial-year handling."""
import collections,csv,json,unittest
from shapely.geometry import shape,Point,Polygon
from download_context import ROOT,flatten

class FleetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads((ROOT/'data/processed/fleet-analysis.json').read_text(encoding='utf-8'))
        with (ROOT/'data/processed/fleet-gap-endpoints.csv').open(encoding='utf-8') as f:
            cls.events=list(csv.DictReader(f))
    def test_totals(self):
        self.assertEqual(len({r['gap_id'] for r in self.events}),18897)
        self.assertEqual(sum(v['gaps'] for v in self.d['vessels']),18897)
        self.assertEqual(sum(r['gaps'] for r in self.d['annual']),18897)
        self.assertEqual(sum(r['gaps'] for r in self.d['flags']),18897)
    def test_cohorts(self):
        seen=set()
        for t in self.d['transitions']:
            current={r['mmsi'] for r in self.d['annual'] if r['year']==t['year']}
            self.assertEqual(t['seen_in_earlier_year'],len(seen & current))
            self.assertEqual(t['first_seen_with_gap'],len(current-seen));seen |= current
    def test_nonempty_presence_join(self):
        self.assertEqual(self.d['eez_presence']['with_regional_gaps'],sum(v['eez_presence_months']>0 for v in self.d['vessels']))
        self.assertEqual(self.d['eez_presence']['with_regional_gaps'],921)
        for v in self.d['vessels']:
            self.assertLessEqual(v['eez_presence_years'],v['eez_presence_months'])
            self.assertLessEqual(v['eez_presence_months'],116)
    def test_partial_year(self):
        self.assertTrue(self.d['transitions'][-1]['partial_year'])
        rows=flatten(json.loads((ROOT/'data/raw/fleet/eez_presence/2026.json').read_text()))
        self.assertTrue(all(r['date']<='2026-08' for r in rows))
    def test_geometry_and_endpoint_union(self):
        geom=shape(json.loads((ROOT/'data/raw/fleet/eez_region.json').read_text())['geometry'])
        self.assertTrue(geom.is_valid)
        self.assertTrue(geom.covers(Point(-60,-40)))
        self.assertFalse(geom.covers(Point(-40,-40)))
        union=sum(r['start_inside_eez']=='True' or r['end_inside_eez']=='True' for r in self.events)
        self.assertEqual(union,self.d['summary']['gaps_either_endpoint_inside_eez'])
        p=Polygon([(0,0),(4,0),(4,4),(0,4)],holes=[[(1,1),(3,1),(3,3),(1,3)]])
        self.assertFalse(p.covers(Point(2,2)));self.assertTrue(p.covers(Point(0,2)))

if __name__=='__main__':unittest.main()
