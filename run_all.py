"""Runs E1-E4, writes results/*.json and the two figures. Usage: python3 run_all.py"""
import json, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import exp_downgrade, exp_metadata, exp_forgery, exp_overhead

os.makedirs("results", exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
                     "font.size": 8, "axes.linewidth": 0.6})
e2 = exp_downgrade.run(); json.dump(e2, open("results/e2_downgrade.json", "w"), indent=1)
json.dump(exp_downgrade.threshold_check(), open("results/e2b_threshold.json", "w"), indent=1)
json.dump(exp_metadata.run(), open("results/e1_metadata.json", "w"), indent=1)
json.dump(exp_forgery.run(), open("results/e3_forgery.json", "w"), indent=1)
json.dump(exp_overhead.run(), open("results/e4_overhead.json", "w"), indent=1)

# Fig. 2: effect of attacker-induced load
sty = {("HPD-HPU", False): ("HPD-HPU", "k", "o", "-"), ("LPD-LPU", False): ("LPD-LPU", "0.35", "s", "--"),
       ("LPD-LPU", True): ("LPD-LPU with floor", "0.0", "^", ":")}
fig, ax = plt.subplots(2, 1, figsize=(3.4, 3.9), sharex=True)
for (pol, fl), (lab, col, mk, ls) in sty.items():
    rs = [r for r in e2 if r["kappa"] == 0.25 and r["policy"] == pol and r["conf_floor"] == fl]
    x = [100 * r["rho"] for r in rs]
    ax[0].plot(x, [100 * r["conf_off_low_fraction"] for r in rs], color=col, marker=mk, ls=ls, ms=3.5, lw=1, label=lab)
    ax[1].plot(x, [100 * r["mission_completion"] for r in rs], color=col, marker=mk, ls=ls, ms=3.5, lw=1, label=lab)
ax[0].set_ylabel("Low-priority time without\nconfidentiality (percent)"); ax[1].set_ylabel("Mission completed (percent)")
ax[1].set_xlabel("Attacker-induced extra load (percent of reference consumption)")
ax[0].legend(frameon=False, fontsize=7); ax[0].text(0.95, 0.88, "(a)", transform=ax[0].transAxes); ax[1].text(0.01, 0.1, "(b)", transform=ax[1].transAxes)
for a in ax: a.grid(alpha=.3, lw=.4)
fig.tight_layout(); fig.savefig("results/fig_load.png", dpi=300); plt.close(fig)

# Fig. 1: attack surface
fig, a = plt.subplots(figsize=(3.4, 2.3)); a.axis("off"); a.set_xlim(0, 10); a.set_ylim(0, 7)
def box(x, y, w, h, t):
    a.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", fc="white", ec="k", lw=.8)); a.text(x + w/2, y + h/2, t, ha="center", va="center")
box(0.1, 4.6, 2.4, 1.4, "Publisher"); box(3.8, 4.6, 2.4, 1.4, "Broker"); box(7.5, 4.6, 2.4, 1.4, "Subscriber"); box(3.8, 0.6, 2.4, 1.4, "TTA")
def arr(p, q, ls="-"): a.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="->", lw=.8, ls=ls))
arr((2.6, 5.3), (3.7, 5.3)); arr((6.3, 5.3), (7.4, 5.3)); arr((1.3, 4.5), (3.9, 2.0), "--"); arr((8.7, 4.5), (6.2, 1.8), "--")
a.text(3.1, 5.75, "data", ha="center"); a.text(6.9, 5.75, "data", ha="center")
a.text(1.0, 3.0, "keys, update", ha="center"); a.text(8.6, 3.0, "keys", ha="center")
a.text(5.0, 6.7, "A1: observe topic names", ha="center", style="italic"); a.text(0.1, 6.7, "A2: load", ha="left", style="italic"); a.text(9.9, 6.7, "A3: forge", ha="right", style="italic")
a.annotate("", xy=(4.4, 6.55), xytext=(4.4, 6.1), arrowprops=dict(arrowstyle="->", lw=.8))
a.annotate("", xy=(1.0, 6.55), xytext=(1.0, 6.1), arrowprops=dict(arrowstyle="->", lw=.8))
a.annotate("", xy=(8.9, 6.55), xytext=(8.9, 6.1), arrowprops=dict(arrowstyle="->", lw=.8))
fig.tight_layout(); fig.savefig("results/fig_surface.png", dpi=300); plt.close(fig)
print("done")
