# Chapter 7 — SIS and LWE

Companion code for Chapter 7 of *Maths for Post-Quantum Cryptography*
(Mathematics for Everything, Book 4).

| File | What it is |
|---|---|
| `lab07.ipynb` | **Lab 7** — SIS by brute force, a real search-to-decision reduction, CBD_η vs. a discrete Gaussian, and a two-panel BDD-decoding reproduction |
| `build_lab07.py` | Generator for the notebook. The notebook is built from this, not hand-edited, so that it stays diffable in git |
| `requirements.txt` | Pinned dependencies |

## Running it

```bash
pip install -r requirements.txt
jupyter lab lab07.ipynb
```

Or headlessly, which is what CI does:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace lab07.ipynb
```

Same policy as Labs 1-6: no lattice-reduction library, no SageMath, and no
cryptographic sampling library standing in for the code the chapter
actually derives. Every algorithm here is implemented directly from the
chapter's definitions in plain Python.

## What the lab covers

**Part A — SIS by brute force.** `sis_bruteforce` reuses Chapter 6's
exhaustive-search idea on $\Lambda_q^\perp(A)$ and reproduces the running
example exactly: $q=5$, $A=(2,1)$, shortest nonzero solutions $(2,1)$,
$(-1,2)$ and their negatives at norm $\sqrt5$, consistent with
Derivation 7.1's pigeonhole guarantee.

**Part B — the search-to-decision reduction, for real.** A toy
decision-LWE oracle is built by brute force (small $q$, small $n$ —
feasible only because the parameters are toy). Derivation 7.2's
coordinate-by-coordinate algorithm is then run against that oracle as a
genuine black box and recovers the secret in 20/20 random instances,
without ever enumerating the secret directly.

**Part C — $\mathrm{CBD}_\eta$ against a discrete Gaussian.** Confirms
Derivation 7.3's $\mathrm{Var}(\mathrm{CBD}_\eta)=\eta/2$ empirically, then
counts a naive rejection-sampler's iterations per draw, showing honestly
that the iteration count depends on the value eventually sampled — the
control-flow property the chapter's constant-time note describes, not a
real timing side-channel measurement (Python gives no constant-time
guarantee to measure).

**Part D — Figure 7.1, both ways.** Reproduces both panels of the toy LWE
lattice numerically: one target decodes correctly (noise under
$\lambda_1/2$), the other decodes to the wrong secret (noise over
$\lambda_1/2$) — the exact mechanism behind a nonzero decryption-failure
probability.

## CI

`_selftest()` in the final cell asserts every numerical claim the lab
makes. Add to `.github/workflows/notebooks.yml`:

```yaml
  ch07:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r ch07/requirements.txt
      - run: python -m jupyter nbconvert --to notebook --execute --stdout ch07/lab07.ipynb > /dev/null
```

## Exercises

The notebook implements Exercises 7.9–7.11 (Lab 7 Parts A-D) in full.
Exercises 7.1–7.8 and 7.12 are pencil-and-paper or standards-reading
exercises; worked solutions are in Appendix C of the book.

- **7.9** SIS and the search-to-decision reduction, run for real against a toy oracle (Lab 7 Parts A, B)
- **7.10** $\mathrm{CBD}_\eta$ vs. a discrete Gaussian, including the rejection-sampler's iteration count (Lab 7 Part C)
- **7.11** Figure 7.1 reproduced numerically, including the boundary case (Lab 7 Part D)

---

Errata: `ERRATA.md` at the repository root.
Standards status: <https://mathsforeverything.com/pqc/standards>
