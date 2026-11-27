"""E2: manipulation of the resource trigger that drives level downgrades.

Resource trigger (Eq. 1 of the paper):  tau(t) = B(t)/P(t) - (T - t) <= 0
triggers one downgrade step. All powers are normalised to the reference consumption
P_ref (all topics at the top of their range, no attack).
"""
import json
from model import (LEVEL_SCORE, CONF_MIN_LEVEL, PublisherConfig, make_topics, order_for)


def topic_power(level, w, kappa, lmax=5):
    return w * (1 + kappa * (level - 1)) / (1 + kappa * (lmax - 1))


def simulate(policy, rho, cfg=PublisherConfig(), dt=1.0):
    topics = make_topics(cfg.conf_floor)
    n_steps = int(cfg.T / dt)
    # per-topic weight so that the reference consumption equals 1.0
    top_sum = sum(topic_power(t.hi, 1.0, cfg.kappa) for t in topics)
    w = (1 - cfg.idle_share) / top_sum
    p_idle = cfg.idle_share
    p_ref = p_idle + sum(topic_power(t.hi, w, cfg.kappa) for t in topics)
    assert abs(p_ref - 1.0) < 1e-9
    battery = (1 + cfg.mu) * p_ref * cfg.T
    order = order_for(policy, topics)

    first_dg = None
    depleted_at = None
    conf_off = {t.name: 0.0 for t in topics}
    score_h = 0.0
    steps_alive = 0
    for k in range(n_steps):
        t = k * dt
        p_atk = rho * p_ref if t >= cfg.onset else 0.0
        p = p_idle + sum(topic_power(x.level, w, cfg.kappa) for x in topics) + p_atk
        battery -= p * dt
        if battery <= 0:
            depleted_at = t
            break
        steps_alive += 1
        for x in topics:
            if x.level < CONF_MIN_LEVEL:
                conf_off[x.name] += dt
        hs = [LEVEL_SCORE[x.level] for x in topics if x.prio == "H"]
        score_h += sum(hs) / len(hs) * dt
        tau = battery / p - (cfg.T - t)
        if tau <= 0:
            for x in order:
                if x.level > x.lo:
                    x.level -= 1
                    if first_dg is None:
                        first_dg = t
                    break
    alive = steps_alive * dt
    low = [x.name for x in topics if x.prio == "L"]
    return {
        "policy": policy, "rho": rho, "kappa": cfg.kappa, "conf_floor": cfg.conf_floor,
        "first_downgrade_delay_s": None if first_dg is None else max(0.0, first_dg - cfg.onset),
        "conf_off_low_fraction": sum(conf_off[n] for n in low) / len(low) / cfg.T,
        "mean_score_high": score_h / alive if alive else 0.0,
        "conf_off_low_alive_fraction": (sum(conf_off[n] for n in low) / len(low) / alive) if alive else 0.0,
        "mission_completion": min(1.0, alive / cfg.T),
        "final_levels": {x.name: x.level for x in topics},
    }


def run():
    rhos = [round(0.05 * i, 2) for i in range(0, 13)]
    configs = [
        ("HPD-HPU", False),
        ("LPD-LPU", False),
        ("LPD-LPU", True),   # M3: confidentiality floor
    ]
    out = []
    for kappa in (0.1, 0.25, 0.5):
        for pol, floor in configs:
            for rho in rhos:
                cfg = PublisherConfig(kappa=kappa, conf_floor=floor)
                out.append(simulate(pol, rho, cfg))
    return out


if __name__ == "__main__":
    res = run()
    json.dump(res, open("results/e2_downgrade.json", "w"), indent=1)
    for r in res:
        if r["kappa"] == 0.25 and r["rho"] in (0.0, 0.15, 0.3, 0.45, 0.6):
            print(r["policy"], r["conf_floor"], r["rho"], r["first_downgrade_delay_s"],
                  round(r["conf_off_low_fraction"], 3), round(r["mean_score_high"], 3),
                  round(r["mission_completion"], 3), r["final_levels"])


def threshold_check(onsets=(0.0, 1000.0, 2500.0, 4000.0), mu=0.15, T=5000.0,
                    idle_share=0.2, kappa=0.25):
    """E2b: compare the closed-form trigger threshold rho* = mu*T/(T - t_a) with the simulator."""
    rows = []
    for ta in onsets:
        cfg = PublisherConfig(T=T, onset=ta, mu=mu, idle_share=idle_share, kappa=kappa)
        lo, hi = 0.0, 3.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if simulate("LPD-LPU", mid, cfg)["first_downgrade_delay_s"] is None:
                lo = mid
            else:
                hi = mid
        rows.append({"mu": mu, "idle_share": idle_share, "kappa": kappa, "onset_s": ta, "analytic": mu * T / (T - ta), "simulated": hi})
    return rows
