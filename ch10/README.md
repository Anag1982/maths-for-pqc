# Chapter 10 — FIPS 204: ML-DSA

Companion code for Chapter 10 of *Maths for Post-Quantum Cryptography*
(Mathematics for Everything, Book 4).

| File | What it is |
|---|---|
| `lab10.ipynb` | **Lab 10** — rejection-sampling secret-independence, exact Decompose/hint identities, and a full toy end-to-end ML-DSA-like sign/verify scheme |
| `build_lab10.py` | Generator for the notebook. The notebook is built from this, not hand-edited, so that it stays diffable in git |
| `requirements.txt` | Pinned dependencies |

## Running it

```bash
pip install -r requirements.txt
jupyter lab lab10.ipynb
```

Or headlessly, which is what CI does:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace lab10.ipynb
```

Same policy as every earlier lab: no external estimator, no borrowed
constant, no signature library. Everything — the rejection loop, the
hint mechanism, the ring arithmetic — is implemented directly from the
chapter's own formulas.

## What the lab covers

**Part A — rejection sampling is secret-independent.** `sample_y`/
`accepted_z` implement Derivation 10.2's uniform-box argument exactly:
two different secret shifts produce accepted-$z$ histograms that agree
to within sampling noise (max bin difference 0.0015 at $N=200{,}000$),
and the empirical acceptance probability matches the derivation's
closed-form prediction.

**Part B — Decompose and the hint, exactly.** `decompose`/`highbits`/
`lowbits`/`make_hint`/`use_hint` implement Definition 10.3 and
Derivation 10.3's hint mechanism directly, including the
$r\equiv-1\pmod q$ edge case. Both round-trip identities — Decompose's
own consistency and $\mathrm{UseHint}(\mathrm{MakeHint}(z,r),r)=
\mathrm{HighBits}(r+z)$ — hold exactly on 20,000 random trials each,
zero failures.

**Part C — a toy end-to-end scheme.** `negacyclic_mul`/`mat_vec`
implement toy ring and module arithmetic directly (ring dimension 8,
module rank 2, so the mechanism is visible without 256-dimensional
arithmetic obscuring it), and `keygen`/`sign`/`verify` assemble
Sections 10.1–10.4's pieces into a complete, working signature scheme
— every rejection check from Algorithm 7 (the $z$ bound, the $r_0$
bound, and the hint-weight cap), correct verification, correct
rejection of a signature checked against the wrong message, and
correct rejection of a signature with one corrupted $z$-coefficient.
200/200 sign/verify cycles succeed.

**Part D — how many restarts, really.** Measures the empirical mean
number of signing attempts per successful signature (3.8, at Part C's
toy parameters) against Part A's single-bound prediction (1.1) —
reproducing, quantitatively, Section 10.3's point that the real
rejection loop combines three checks, not one, so the true restart
count is higher than a naive single-bound estimate suggests.

## CI

`_selftest()` in the final cell asserts every numerical claim the lab
makes. Add to `.github/workflows/notebooks.yml`:

```yaml
  ch10:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r ch10/requirements.txt
      - run: python -m jupyter nbconvert --to notebook --execute --stdout ch10/lab10.ipynb > /dev/null
```

## Exercises

The notebook implements Exercises 10.12–10.14 (Lab 10 Parts A–D) in
full. The remaining exercises are pencil-and-paper or standards-reading
exercises; worked solutions are in Appendix C of the book.

- **10.12** Rejection sampling and the hint identities, including the
  acceptance probability rising toward Part A's prediction as $\gamma_1$
  grows (Lab 10 Parts A, B)
- **10.13** The toy end-to-end scheme, including rejecting a signature
  with one corrupted coefficient (Lab 10 Part C)
- **10.14** The empirical restart count versus the single-bound and
  combined predictions (Lab 10 Part D)

---

Errata: `ERRATA.md` at the repository root.
Standards status: <https://mathsforeverything.com/pqc/standards>
