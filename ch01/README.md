# Chapter 1 — What Quantum Computing Actually Breaks

Companion code for Chapter 1 of *Maths for Post-Quantum Cryptography*
(Mathematics for Everything, Book 4).

| File | What it is |
|---|---|
| `lab01.ipynb` | **Lab 1** — Mosca exposure arithmetic, and period-finding by classical DFT |
| `build_lab01.py` | Generator for the notebook. The notebook is built from this, not hand-edited, so that it stays diffable in git |
| `requirements.txt` | Pinned dependencies |

## Running it

```bash
pip install -r requirements.txt
jupyter lab lab01.ipynb
```

Or headlessly, which is what CI does:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace lab01.ipynb
```

Chapter 1 needs **no cryptographic library and no quantum hardware** — only
`numpy` and `matplotlib`. That is deliberate: the point of Part B is that the
mathematics of Shor's algorithm runs on a laptop, and what a quantum computer
contributes is scale, not novelty. The heavier environment (SageMath,
`liboqs-python`, PQClean, the lattice-estimator) is set up in Appendix B and
first needed in Chapter 4.

## What the lab covers

**Part A — Mosca arithmetic.** `exposure(x, y, z)` returns the years of data
already lost under $x + y > z$, and `plot_exposure_bars` draws the chart. The
useful output is not the number but the picture: the exposed interval does not
disappear when you push the arrival year out by five years, which is the
argument for acting on a compliance calendar rather than a forecast.

**Part B — See the period.** Brute-force `order(a, N)`; the periodicity picture
from Figure 1.1; the DFT of $a^x \bmod N$ showing peaks at multiples of $M/r$;
then the case where $r \nmid M$, where the peaks smear and you need continued
fractions to recover $r$ — which is the step most popular accounts of Shor's
algorithm skip. Finally `factor_from_period`, and an exhaustive check of how
often a random $a$ actually works.

## A correction the lab produced

Writing this lab found an error in an early draft of the chapter. The success
probability of the factoring step for random $a$ is at least
$1 - 2^{-(m-1)}$, where $m$ is the number of distinct odd prime factors of $N$
(Nielsen & Chuang, Thm A4.13) — **not** $1 - 2^{-m}$. The difference matters
for exactly the case that matters: for a semiprime, $m = 2$ gives a guarantee
of $1/2$, not $3/4$.

The bound is tight. The `success_rate` cell verifies exhaustively that
$N = 21$ and $N = 33$ both attain exactly $1/2$, which rules out the stronger
claim. `_selftest()` asserts this, so the notebook will fail CI if anyone
"corrects" the chapter back.

## CI

`_selftest()` in the final cell asserts every numerical claim the lab makes.
Add to `.github/workflows/notebooks.yml`:

```yaml
name: notebooks
on: [push, pull_request]
jobs:
  ch01:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r ch01/requirements.txt
      - run: python -m jupyter nbconvert --to notebook --execute --stdout ch01/lab01.ipynb > /dev/null
```

## Exercises

The notebook has scaffolds, not solutions, for Exercises 1.6–1.9. Worked
solutions are in Appendix C of the book.

- **1.6** exposure over $z \in [2030, 2045]$; largest tolerable $y$ at $z = 2035$
- **1.7** orders mod 91, and which values of $r$ account for the failures
- **1.8** per-iteration Grover depth $d_1$ for AES-128, and $\log_2 m$ against $\log_2$ `MAXDEPTH` — the slope is the whole of §1.4 in one number
- **1.9** the Gidney–Ekerå 2019 and Gidney 2025 qubit and runtime ratios

---

Errata: `ERRATA.md` at the repository root.
Standards status: <https://mathsforeverything.com/pqc/standards>
