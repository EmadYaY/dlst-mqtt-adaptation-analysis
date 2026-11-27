"""Runs E1-E4, writes results/*.json and the two figures. Usage: python3 run_all.py"""
import json, os
import exp_downgrade, exp_metadata, exp_forgery, exp_overhead

os.makedirs("results", exist_ok=True)
e2 = exp_downgrade.run(); json.dump(e2, open("results/e2_downgrade.json", "w"), indent=1)
e2b = exp_downgrade.threshold_check()
for mu_, idle_, kap_ in ((0.10, 0.2, 0.25), (0.25, 0.2, 0.25), (0.15, 0.4, 0.25), (0.15, 0.2, 0.1), (0.15, 0.2, 0.5)):
    e2b += exp_downgrade.threshold_check(onsets=(0.0, 2500.0), mu=mu_, idle_share=idle_, kappa=kap_)
json.dump(e2b, open("results/e2b_threshold.json", "w"), indent=1)
json.dump(exp_metadata.run(), open("results/e1_metadata.json", "w"), indent=1)
json.dump(exp_forgery.run(), open("results/e3_forgery.json", "w"), indent=1)
json.dump(exp_overhead.run(), open("results/e4_overhead.json", "w"), indent=1)

import figures
figures.make(e2)
print("done")
