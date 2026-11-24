"""Reference model of the topic-level security adaptation described for DLST-MQTT.

Scope (see README): this is NOT the authors' implementation. It encodes only the
elements of the scheme that are stated in the DLST-MQTT article and that the
analysis needs: topic priorities and level ranges, the update message of the
update procedure, and the HPD-HPU / LPD-LPU downgrade heuristics.
"""
import hashlib
import hmac
import os
from dataclasses import dataclass, field

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.exceptions import InvalidSignature

# Total security score of each level (Table 5 of the DLST-MQTT article).
LEVEL_SCORE = {0: 0.0, 1: 1.7, 2: 2.3, 3: 2.5, 4: 2.94, 5: 3.2}
CONF_MIN_LEVEL = 2          # level 2 is the first level that adds confidentiality
TLS_ECC_SCORE = 3.4         # reference score of TLS with ECC (Table 5)

# Topics of the experimental setup (Table 6 of the article): name, priority, level range.
TOPICS = [
    ("t1", "H", (4, 5)),
    ("t2", "H", (4, 5)),
    ("t3", "M", (2, 4)),
    ("t4", "L", (1, 3)),
    ("t5", "L", (1, 3)),
]
PRIORITY_ORDER = {"H": 0, "M": 1, "L": 2}


def subtopic_name(topic, level):
    """Sub-topic naming as notated in the article: t/st_l (level visible in the name)."""
    return f"{topic}/st_{level}"


class AliasRegistry:
    """Mitigation M1: the TTA binds every registered security association to a random alias.

    The alias is returned to authorised clients together with the association
    (Phase V of the protocol); the broker routes on the alias only.
    """

    def __init__(self, rng):
        self._rng = rng
        self._table = {}

    def register(self, topic, level):
        alias = f"{topic}/{self._rng.getrandbits(64):016x}"
        self._table[alias] = (topic, level)
        return alias

    def resolve(self, alias):
        return self._table[alias]


# ---------------------------------------------------------------------------
# Update message (Phase VI of the article): m = update || l_new || sn,
# C = Encrypt(m, K), tag = H(C, K), packet = C || tag.
# ---------------------------------------------------------------------------
TAG_LEN = 28  # HMAC-SHA224


def _enc(key, nonce, data):
    c = Cipher(algorithms.AES(key), modes.CTR(nonce)).encryptor()
    return c.update(data) + c.finalize()


def build_update(key, l_new, sn):
    nonce = os.urandom(16)
    m = b"update" + bytes([l_new]) + sn.to_bytes(4, "big")
    c = nonce + _enc(key, nonce, m)
    tag = hmac.new(key, c, hashlib.sha224).digest()
    return c, tag


def verify_update(key, c, tag, last_sn):
    """Subscriber side of the original scheme. Returns (l_new, sn) or None."""
    if not hmac.compare_digest(hmac.new(key, c, hashlib.sha224).digest(), tag):
        return None
    nonce, body = c[:16], c[16:]
    m = _enc(key, nonce, body)
    if not m.startswith(b"update") or len(m) != 11:
        return None
    l_new = m[6]
    sn = int.from_bytes(m[7:11], "big")
    if sn <= last_sn:
        return None  # replayed or stale
    return l_new, sn


# Mitigation M2: the publisher additionally signs the update message.
def sign_update(priv, alias, c, tag):
    return priv.sign(alias.encode() + c + tag, ec.ECDSA(hashes.SHA256()))


def verify_update_signed(key, pub, alias, c, tag, sig, last_sn):
    try:
        pub.verify(sig, alias.encode() + c + tag, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        return None
    return verify_update(key, c, tag, last_sn)


# ---------------------------------------------------------------------------
# Publisher resource model used by the trigger-manipulation experiment.
# ---------------------------------------------------------------------------
@dataclass
class PublisherConfig:
    T: float = 5000.0        # mission duration (s); equals the 5000 s run of the article
    onset: float = 1000.0    # time at which the attacker starts to add load (s)
    mu: float = 0.15         # energy margin of the battery over the mission
    kappa: float = 0.25      # relative energy increase per additional level
    idle_share: float = 0.2  # share of the reference consumption that is level-independent
    conf_floor: bool = False # mitigation M3: never go below the first confidential level


@dataclass
class Topic:
    name: str
    prio: str
    lo: int
    hi: int
    level: int = field(default=0)


def make_topics(floor_conf=False):
    ts = []
    for name, prio, (lo, hi) in TOPICS:
        if floor_conf:
            lo = max(lo, CONF_MIN_LEVEL)
        ts.append(Topic(name, prio, lo, hi, level=hi))
    return ts


def order_for(policy, topics):
    """Downgrade order of the two heuristics (activation order breaks ties)."""
    idx = {t.name: i for i, t in enumerate(topics)}
    if policy == "HPD-HPU":
        key = lambda t: (PRIORITY_ORDER[t.prio], idx[t.name])
    elif policy == "LPD-LPU":
        key = lambda t: (-PRIORITY_ORDER[t.prio], idx[t.name])
    else:
        raise ValueError(policy)
    return sorted(topics, key=key)
