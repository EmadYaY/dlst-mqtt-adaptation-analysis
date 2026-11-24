# Reference model and experiments: security analysis of dynamic topic-based security levels in MQTT

Code and data for the paper "Security Analysis of Dynamic Topic-Based Security Levels in MQTT: A Case Study on DLST-MQTT".

The code is a reference model of the scheme DLST-MQTT (De Rango, Spina, Iera, Future Generation Computer Systems 166, 107625, 2025, doi:10.1016/j.future.2024.107625). It is **not** the original authors' implementation. It encodes only what the article describes (see `model.py`).

## Contents

| File | Purpose |
|---|---|
| `model.py` | Reference model: topics, security levels, update message (AES-256-CTR + HMAC-SHA224), aliases (M1), signed updates (M2, ECDSA P-256), publisher resource model |
| `exp_metadata.py` | E1: observer that infers levels and level changes from topic names, with and without aliases |
| `exp_downgrade.py` | E2: load-driven downgrade simulation, and E2b: threshold check against the closed form |
| `exp_forgery.py` | E3: forged level-change messages, with and without the publisher signature |
| `exp_overhead.py` | E4: micro-benchmarks of the primitives |
| `run_all.py` | Runs E1 to E4 and writes `results/` and the two figures |
| `tests/test_model.py` | Seven sanity tests |
| `results/` | Output of the runs used in the paper. `results/e4_runs/` holds three timing runs on the test host |

## Run

Python 3.10 or newer.

    pip install -r requirements.txt
    python -m unittest tests.test_model -v     # all 7 tests must pass
    python run_all.py                          # writes results/ (about 10 s)

Each experiment can also be run alone, for example `python exp_overhead.py`.

E1 to E3 are seeded and reproduce the numbers in the paper exactly. E4 reports timings of the machine it runs on, so absolute values differ per machine.

## Test host of the reported timings

Intel Core i7-8750H (2.2 GHz, 6 cores), Windows 10 (build 22631), Python 3.15, cryptography 50.0.2. Three runs, in `results/e4_runs/`.

## License

MIT, see `LICENSE`.
