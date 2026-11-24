"""E4: micro-benchmarks of the primitives used by the mitigations (this host only)."""
import hashlib, hmac, json, os, statistics, time, platform
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from model import _enc

def bench(fn, n=2000, reps=7):
    ts = []
    for _ in range(reps):
        t0 = time.perf_counter()
        for _ in range(n):
            fn()
        ts.append((time.perf_counter() - t0) / n * 1e6)
    return statistics.median(ts)

def run():
    msg, key, nonce = os.urandom(64), os.urandom(32), os.urandom(16)
    res = {"hmac_sha224_64B_us": bench(lambda: hmac.new(key, msg, hashlib.sha224).digest()),
           "aes256_ctr_64B_us": bench(lambda: _enc(key, nonce, msg))}
    for name, curve in (("secp192r1", ec.SECP192R1), ("secp256r1", ec.SECP256R1)):
        k = ec.generate_private_key(curve()); sig = k.sign(msg, ec.ECDSA(hashes.SHA256()))
        pk = k.public_key()
        res[f"ecdsa_{name}_sign_us"] = bench(lambda: k.sign(msg, ec.ECDSA(hashes.SHA256())), n=300)
        res[f"ecdsa_{name}_verify_us"] = bench(lambda: pk.verify(sig, msg, ec.ECDSA(hashes.SHA256())), n=300)
        res[f"ecdsa_{name}_sig_bytes"] = len(sig)
    res["alias_extra_bytes_per_association"] = 8  # 64-bit alias
    # amortised cost of M2 per data message: one verify per update event
    # (one update per 1000 s per topic in the article's setup, one data message per second assumed)
    res["m2_amortised_verify_us_per_msg_p256"] = res["ecdsa_secp256r1_verify_us"] / 1000.0
    res["host"] = platform.processor() or platform.machine()
    return res

if __name__ == "__main__":
    r = run(); json.dump(r, open("results/e4_overhead.json", "w"), indent=1)
    for k, v in r.items(): print(k, round(v, 2) if isinstance(v, float) else v)
