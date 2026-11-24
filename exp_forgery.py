"""E3: can a holder of the sub-topic key forge a level-change update?"""
import json, os
from cryptography.hazmat.primitives.asymmetric import ec
from model import build_update, verify_update, sign_update, verify_update_signed

def run(trials=1000):
    key = os.urandom(32)                 # K_stl, held by publisher and every authorised subscriber
    wrong = os.urandom(32)               # key of an outsider
    priv = ec.generate_private_key(ec.SECP256R1())
    pub = priv.public_key()
    alias = "t4/st_3"
    acc = {"insider_original": 0, "insider_with_signature_check": 0,
           "outsider_original": 0, "replay_original": 0, "genuine_with_signature_check": 0}
    for i in range(1, trials + 1):
        c, tag = build_update(key, 1, i)                     # insider forges "move to level 1"
        acc["insider_original"] += verify_update(key, c, tag, i - 1) is not None
        # insider has no publisher private key: its best attempt is a signature of its own key
        bad = ec.generate_private_key(ec.SECP256R1())
        s = sign_update(bad, alias, c, tag)
        acc["insider_with_signature_check"] += verify_update_signed(key, pub, alias, c, tag, s, i - 1) is not None
        c2, t2 = build_update(wrong, 1, i)
        acc["outsider_original"] += verify_update(key, c2, t2, i - 1) is not None
        acc["replay_original"] += verify_update(key, c, tag, i) is not None
        g = sign_update(priv, alias, c, tag)                 # genuine publisher
        acc["genuine_with_signature_check"] += verify_update_signed(key, pub, alias, c, tag, g, i - 1) is not None
    return {k: v / trials for k, v in acc.items()} | {"trials": trials}

if __name__ == "__main__":
    r = run(); json.dump(r, open("results/e3_forgery.json", "w"), indent=1); print(r)
