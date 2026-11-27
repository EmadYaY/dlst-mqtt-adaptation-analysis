"""Figures of the paper, drawn only from results/e2_downgrade.json (nothing is typed in by hand)."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


def make(e2):
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
                         "font.size": 8, "axes.linewidth": 0.6})
    # Fig. 2: effect of attacker-induced load
    sty = {("HPD-HPU", False): ("HPD-HPU", "k", "o", "-"), ("LPD-LPU", False): ("LPD-LPU", "0.35", "s", "--"),
           ("LPD-LPU", True): ("LPD-LPU with floor", "0.0", "^", ":")}
    fig, ax = plt.subplots(2, 1, figsize=(3.4, 3.9), sharex=True)
    for (pol, fl), (lab, col, mk, ls) in sty.items():
        rs = [r for r in e2 if r["kappa"] == 0.25 and r["policy"] == pol and r["conf_floor"] == fl]
        x = [100 * r["rho"] for r in rs]
        ax[0].plot(x, [100 * r["conf_off_low_fraction"] for r in rs], color=col, marker=mk, ls=ls, ms=(6 if pol == "HPD-HPU" else 3.5), mfc=("none" if pol == "HPD-HPU" else col), lw=1, label=lab)
        ax[1].plot(x, [100 * r["mission_completion"] for r in rs], color=col, marker=mk, ls=ls, ms=(6 if pol == "HPD-HPU" else 3.5), mfc=("none" if pol == "HPD-HPU" else col), lw=1, label=lab)
    ax[0].set_ylabel("Low-priority time without\nconfidentiality (percent)"); ax[1].set_ylabel("Mission completed (percent)")
    ax[1].set_xlabel("Attacker-induced extra load (percent of reference consumption)")
    ax[0].legend(frameon=False, fontsize=7); ax[0].text(0.95, 0.88, "(a)", transform=ax[0].transAxes); ax[1].text(0.01, 0.1, "(b)", transform=ax[1].transAxes)
    for a in ax: a.grid(alpha=.3, lw=.4)
    fig.tight_layout(); fig.savefig("results/fig_load.png", dpi=300); plt.close(fig)

    # Fig. 1: attack surface
    fig, a = plt.subplots(figsize=(3.4, 2.3)); a.axis("off"); a.set_xlim(0, 10); a.set_ylim(0, 7)
    def box(x, y, w, h, t):
        a.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", fc="white", ec="k", lw=.8)); a.text(x + w/2, y + h/2, t, ha="center", va="center")
    def arr(p, q, ls="-", style="->"): a.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle=style, lw=.8, ls=ls))
    box(0.1, 4.2, 2.4, 1.4, "Publisher"); box(3.8, 4.2, 2.4, 1.4, "Broker"); box(7.5, 4.2, 2.4, 1.4, "Subscriber"); box(3.8, 0.4, 2.4, 1.4, "TTA")
    arr((2.6, 4.9), (3.7, 4.9)); arr((6.3, 4.9), (7.4, 4.9))
    a.text(3.15, 5.3, "data,\nupdate", ha="center", va="bottom", fontsize=6.5); a.text(6.85, 5.3, "data,\nupdate", ha="center", va="bottom", fontsize=6.5)
    arr((1.3, 4.1), (3.8, 1.5), "--", "<->"); arr((8.7, 4.1), (6.2, 1.5), "--", "<->")
    a.text(0.9, 2.5, "SA, $K_{stl}$", ha="center"); a.text(9.1, 2.5, "SA, $K_{stl}$", ha="center")
    for x, t in ((1.3, "A2: adds load"), (5.0, "A1: reads topic names"), (8.7, "A3: forges update")):
        a.annotate(t, xy=(x, 5.7), xytext=(x, 6.5), ha="center", style="italic", arrowprops=dict(arrowstyle="->", lw=.8))
    fig.tight_layout(); fig.savefig("results/fig_surface.png", dpi=300); plt.close(fig)
