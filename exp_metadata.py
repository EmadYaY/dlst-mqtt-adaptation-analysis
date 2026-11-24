"""E1: what a passive observer of topic strings learns about the security level.

The observer sits at the broker or on the link and sees PUBLISH/SUBSCRIBE topic
strings (MQTT carries them in clear). Level changes follow the update procedure:
every subscriber of the topic unsubscribes from the old sub-topic and subscribes
to the new one shortly after the update message.
"""
import bisect
import json
import random
from collections import Counter, defaultdict, deque
from model import TOPICS, AliasRegistry, subtopic_name


def simulate(mode, seed, T=100000.0, change_mean=1000.0, subs=15, churn=0.2,
             window=10.0, k=3, migrate_delay_mean=2.0, match_tol=15.0):
    rng = random.Random(seed)
    reg = AliasRegistry(rng)
    events = []                      # (time, kind, client, name)
    truth = []                       # (time, topic, old_level, new_level)
    history = {}                     # topic -> ([start times], [names])
    lvl_time = defaultdict(Counter)  # time spent per level, per topic (observer's prior)

    def name_of(topic, level):
        return subtopic_name(topic, level) if mode == "baseline" else reg.register(topic, level)

    for topic, _, (lo, hi) in TOPICS:
        lvl, cur, t = hi, None, 0.0
        cur = name_of(topic, lvl)
        starts, names = [0.0], [cur]
        clients = [f"{topic}-s{i}" for i in range(subs)]
        events += [(0.0, "SUB", c, cur) for c in clients]
        while True:
            dt = rng.expovariate(1.0 / change_mean)
            lvl_time[topic][lvl] += min(dt, T - t)
            t += dt
            if t >= T:
                break
            new = min(max(lvl + rng.choice([-1, 1]), lo), hi)
            if new == lvl:                     # at a bound: move the only possible way
                new = lvl - 1 if lvl > lo else lvl + 1
            truth.append((t, topic, lvl, new))
            nxt = name_of(topic, new)
            for c in clients:
                d = rng.expovariate(1.0 / migrate_delay_mean)
                events.append((t + d, "UNSUB", c, cur))
                events.append((t + d, "SUB", c, nxt))
            starts.append(t)
            names.append(nxt)
            lvl, cur = new, nxt
        history[topic] = (starts, names)

    # Background churn: new subscribers join whatever sub-topic is current for a random topic.
    for i in range(int(churn * T)):
        tm = rng.uniform(0, T)
        topic = rng.choice(TOPICS)[0]
        starts, names = history[topic]
        events.append((tm, "SUB", f"x{i}", names[bisect.bisect_right(starts, tm) - 1]))
    events.sort()

    # Detector (identical for both naming schemes): a burst of >= k SUBSCRIBEs to one
    # sub-topic name within `window` seconds is reported as a level change of that topic.
    recent, last_flag, first_seen, detected = defaultdict(deque), {}, {}, []
    for tm, kind, _, nm in events:
        if kind != "SUB" or tm == 0.0:
            continue
        first_seen.setdefault(nm, tm)
        q = recent[nm]
        q.append(tm)
        while q and tm - q[0] > window:
            q.popleft()
        if len(q) >= k and tm - last_flag.get(nm, -1e9) > 6 * window:
            last_flag[nm] = tm
            detected.append((q[0], nm.split("/")[0]))

    matched = set()
    for tm, topic, _, _ in truth:
        for i, (dtm, dtop) in enumerate(detected):
            if i not in matched and dtop == topic and -1.0 <= dtm - tm <= match_tol:
                matched.add(i)
                break
    tp = len(matched)
    fp, fn = len(detected) - tp, len(truth) - tp
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0

    if mode == "baseline":
        # The level is the numeric suffix of the sub-topic string; check it is recoverable.
        names = {nm for _, _, _, nm in events}
        acc = sum(int(nm.split("/st_")[1]) == int(nm[-1]) for nm in names) / len(names)
    else:
        # Without the name an observer can only play the prior: most frequent level of the topic.
        acc = (sum(max(c.values()) for c in lvl_time.values()) /
               sum(sum(c.values()) for c in lvl_time.values()))
    return {"events": len(truth), "precision": prec, "recall": rec, "f1": f1,
            "level_inference_accuracy": acc}


def run(seeds=5):
    out = []
    for mode in ("baseline", "alias"):
        for churn in (0.0, 0.1, 0.5, 1.0):
            rs = [simulate(mode, s, churn=churn) for s in range(seeds)]
            row = {k: sum(r[k] for r in rs) / seeds for k in rs[0]}
            row.update({"mode": mode, "churn": churn})
            out.append(row)
    return out


if __name__ == "__main__":
    res = run()
    json.dump(res, open("results/e1_metadata.json", "w"), indent=1)
    for r in res:
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
