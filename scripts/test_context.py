import unittest
from analyze_context import summarize,hours_by_mmsi
from download_context import flatten,request_spec
class ContextTests(unittest.TestCase):
 def test_missing_is_not_zero(self):
  r=summarize('2025-01',[],None,None,None,None)
  self.assertIsNone(r['presence_mmsi']);self.assertIsNone(r['sar_unmatched_pct'])
 def test_population_intersection(self):
  r=summarize('2025-01',[{'mmsi':'1'},{'mmsi':'1'},{'mmsi':'3'}],{'1':24,'2':24},{'1':12},10,4)
  self.assertEqual(r['gaps_per_1000_observed_vessel_days'],1000)
  self.assertEqual(r['observed_fleet_with_gaps_pct'],50)
  self.assertEqual(r['gap_mmsi_missing_from_presence'],1)
  self.assertEqual(r['sar_unmatched_pct'],40)
 def test_zero_denominator(self):
  r=summarize('2025-01',[],{}, {},0,0);self.assertIsNone(r['sar_unmatched_pct'])
 def test_deduplicate_mmsi_sum_hours(self):
  self.assertEqual(hours_by_mmsi([{'mmsi':'1','hours':2},{'mmsi':'1','hours':3}]),{'1':5})
 def test_missing_identity_fails(self):
  self.assertEqual(hours_by_mmsi([{'hours':1}]),{})
 def test_pagination_fails(self):
  with self.assertRaises(ValueError):flatten({'entries':[],'nextOffset':100})
 def test_invalid_sar_fails(self):
  with self.assertRaises(ValueError):summarize('2025-01',[],{}, {},2,3)
 def test_region_and_leap_month(self):
  spec=request_spec('presence','2024-02');self.assertIn('2024-02-29',spec['params']['date-range']);self.assertEqual(spec['body']['geojson']['coordinates'][0][0],[-70,-60])
if __name__=='__main__':unittest.main()
