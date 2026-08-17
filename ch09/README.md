# Chapter 9 — FIPS 203: ML-KEM

Companion code for Chapter 9 of *Maths for Post-Quantum Cryptography*
(Mathematics for Everything, Book 4).

| File | What it is |
|---|---|
| `lab09.ipynb` | **Lab 9** — textbook Regev encryption, the K-PKE noise-cancellation identity, and an independent reproduction of FIPS 203's decapsulation failure rates |
| `build_lab09.py` | Generator for the notebook. The notebook is built from this, not hand-edited, so that it stays diffable in git |
| `requirements.txt` | Pinned dependencies |

## Running it

```bash
pip install -r requirements.txt
jupyter lab lab09.ipynb
```

Or headlessly, which is what CI does:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace lab09.ipynb
```

Same policy as every earlier lab: no external estimator, no borrowed
constant. The one new dependency is `mpmath`, needed only in Part D —
the tail probabilities involved (down to roughly $2^{-177}$) are far
beyond what double-precision floating point can resolve without
catastrophic cancellation.

## What the lab covers

**Part A — textbook Regev.** `regev_keygen`/`regev_encrypt`/`regev_decrypt`
implement Derivation 9.1 exactly: one secret, $m$ LWE samples, one bit
per ciphertext. Zero failures at a conservative noise level.

**Part B — turn up the noise, watch it break.** Sweeps the noise
standard deviation and plots the empirical decryption-failure rate
against a prediction computed directly from the $q/4$ boundary —
Chapter 7 Figure 7.1's mechanism, made continuous instead of a single
two-panel snapshot.

**Part C — K-PKE's noise term, exactly.** `negacyclic_mul`/`module_mul`
implement ring and module multiplication mod $q$ directly, and confirm
Derivation 9.2's central claim — the $s^{\top}A^{\top}r$ cancellation —
holds exactly (integer arithmetic mod $q$, not approximately) at real
Module-LWE dimensions ($n=256$).

**Part D — Table 9.2, reproduced.** `decap_failure_probability` builds
the exact CBD and compression-error distributions for all three ML-KEM
parameter sets, computes the noise term's cumulant generating function,
solves for the saddle point, and evaluates the tail via the
Bahadur–Rao large-deviation approximation — reproducing FIPS 203's
published decapsulation failure rates to within three or four bits,
independently, from nothing but $(n,k,q,\eta_1,\eta_2,d_u,d_v)$.

## CI

`_selftest()` in the final cell asserts every numerical claim the lab
makes. Add to `.github/workflows/notebooks.yml`:

```yaml
  ch09:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r ch09/requirements.txt
      - run: python -m jupyter nbconvert --to notebook --execute --stdout ch09/lab09.ipynb > /dev/null
```

## Exercises

The notebook implements Exercises 9.12–9.13 (Lab 9 Parts A–D) in full.
The remaining exercises are pencil-and-paper or standards-reading
exercises; worked solutions are in Appendix C of the book.

- **9.12** Textbook Regev and the noise sweep, including the noise
  level at which the empirical failure rate first exceeds $2^{-10}$
  (Lab 9 Parts A, B)
- **9.13** Table 9.2 reproduced for ML-KEM-768, including a
  hypothetical $d_v=6$ (Lab 9 Part D)

---

Errata: `ERRATA.md` at the repository root.
Standards status: <https://mathsforeverything.com/pqc/standards>
