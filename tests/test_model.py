import os, random, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from model import *
import exp_downgrade, exp_forgery, exp_metadata

class T(unittest.TestCase):
    def test_update_roundtrip_and_replay(self):
        k = os.urandom(32); c, t = build_update(k, 3, 7)
        self.assertEqual(verify_update(k, c, t, 6), (3, 7))
        self.assertIsNone(verify_update(k, c, t, 7))
        self.assertIsNone(verify_update(os.urandom(32), c, t, 6))
        self.assertIsNone(verify_update(k, c, bytes(28), 6))
    def test_no_attack_no_downgrade(self):
        r = exp_downgrade.simulate("HPD-HPU", 0.0)
        self.assertIsNone(r["first_downgrade_delay_s"]); self.assertEqual(r["mission_completion"], 1.0)
    def test_levels_stay_in_range(self):
        for pol in ("HPD-HPU", "LPD-LPU"):
            r = exp_downgrade.simulate(pol, 0.6)
            for name, _, (lo, hi) in TOPICS:
                self.assertTrue(lo <= r["final_levels"][name] <= hi)
    def test_floor_blocks_plaintext(self):
        r = exp_downgrade.simulate("LPD-LPU", 0.6, PublisherConfig(conf_floor=True))
        self.assertEqual(r["conf_off_low_fraction"], 0.0)
    def test_policy_order(self):
        self.assertEqual(order_for("HPD-HPU", make_topics())[0].prio, "H")
        self.assertEqual(order_for("LPD-LPU", make_topics())[0].prio, "L")
    def test_forgery(self):
        r = exp_forgery.run(50)
        self.assertEqual(r["insider_original"], 1.0); self.assertEqual(r["insider_with_signature_check"], 0.0)
    def test_alias_hides_level(self):
        r = exp_metadata.simulate("alias", 1, T=20000, churn=0.0)
        self.assertLess(r["level_inference_accuracy"], 0.7)
if __name__ == "__main__": unittest.main()
