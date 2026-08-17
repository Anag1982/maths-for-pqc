# Chapter 8 — How Hard Is It Really?

Companion code for Chapter 8 of *Maths for Post-Quantum Cryptography*
(Mathematics for Everything, Book 4).

| File | What it is |
|---|---|
| `lab08.ipynb` | **Lab 8** — the Geometric Series Assumption, the primal attack's success condition, and the core-SVP cost model, reproducing NIST's Category claims from scratch |
| `build_lab08.py` | Generator for the notebook. The notebook is built from this, not hand-edited, so that it stays diffable in git |
| `requirements.txt` | Pinned dependencies |

## Running it

```bash
pip install -r requirements.txt
jupyter lab lab08.ipynb
```

Or headlessly, which is what CI does:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace lab08.ipynb
```

Same policy as Labs 1-7, taken furthest here: no SageMath, no
lattice-estimator package, no external tool of any kind. Chapter 8's
entire argument is that the core-SVP methodology is simple enough to
implement directly from its own formulas — this lab is that
implementation.

## What the lab covers

**Part A — the GSA curve.** `delta_gsa` implements Definition 8.3's
Geometric Series Assumption and confirms it decreases monotonically
toward 1 as the BKZ block size $\beta$ grows.

**Part B — solving for $\beta$.** `best_primal_attack` implements
Derivation 8.2's success condition and searches over both the sample
count $m$ and the block size $\beta$, for ML-KEM-512/768/1024's actual
$(n{=}256, k, q{=}3329, \eta_1)$. The result — $\beta=406/624/874$ —
matches the CRYSTALS-Kyber specification's own published Table 4
($\beta=406/626/878$) to within a handful of units, a residual gap of
under 1% attributable to search-grid and rounding choices in the
reference implementation, not a different model.

**Part C — Table 8.1, reproduced.** Converts each recovered $\beta$ to
classical ($2^{0.292\beta}$) and quantum ($2^{0.265\beta}$) bit costs,
reproducing all four numeric columns of the chapter's Table 8.1 from
nothing but the parameter set's $(n,k,q,\eta_1)$.

**Part D — how much margin, really.** Compares each parameter set's raw
core-SVP classical cost against NIST's actual category threshold
(Chapter 1's Table 1.2: 143/207/272 bits for Categories 1/3/5),
confirming all three parameter sets fall short in the raw model — exactly
Section 8.5's honest point — and computes exactly how much larger $\beta$
would need to be to close that gap on the raw number alone.

## CI

`_selftest()` in the final cell asserts every numerical claim the lab
makes. Add to `.github/workflows/notebooks.yml`:

```yaml
  ch08:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r ch08/requirements.txt
      - run: python -m jupyter nbconvert --to notebook --execute --stdout ch08/lab08.ipynb > /dev/null
```

## Exercises

The notebook implements Exercises 8.9–8.11 (Lab 8 Parts A-D) in full.
Exercises 8.1–8.8 and 8.12 are pencil-and-paper or standards-reading
exercises; worked solutions are in Appendix C of the book.

- **8.9** The GSA curve and the beta-search, including sensitivity to search resolution (Lab 8 Parts A, B)
- **8.10** Table 8.1 reproduced, including a hypothetical smaller $\eta_1$ (Lab 8 Part C)
- **8.11** The raw-to-threshold margin for all three parameter sets (Lab 8 Part D)

---

Errata: `ERRATA.md` at the repository root.
Standards status: <https://mathsforeverything.com/pqc/standards>
