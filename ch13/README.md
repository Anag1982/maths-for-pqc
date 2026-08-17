# Chapter 13 — Codes: HQC and Classic McEliece

Companion code for Chapter 13 of *Maths for Post-Quantum Cryptography*
(Mathematics for Everything, Book 4).

| File | What it is |
|---|---|
| `lab13.ipynb` | **Lab 13** — a real toy binary Goppa code (Classic McEliece) with zero measured decoding failures, a toy quasi-cyclic code (HQC-style) with a measured, growing decoding failure rate, and a reaction attack that recovers a secret from decoding outcomes alone |
| `build_lab13.py` | Generator for the notebook. The notebook is built from this, not hand-edited, so that it stays diffable in git |
| `requirements.txt` | Pinned dependencies |

## Running it

```bash
pip install -r requirements.txt
jupyter lab lab13.ipynb
```

Or headlessly, which is what CI does:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace lab13.ipynb
```

`numpy` is used only for `GF(2)` linear algebra (RREF, nullspace,
matrix inverse). Every finite-field ($\mathbb F_{16}$), Goppa-code, and
quasi-cyclic-code construction is built from scratch — no coding-theory
library anywhere in this notebook.

## What the lab covers

**Part A — a toy binary Goppa code, keyed and decoded.** `GF2m`
implements $\mathbb F_{16}$ via log/antilog tables; a degree-2
irreducible Goppa polynomial and a 12-point support build a genuine
binary Goppa code's parity-check matrix via the *correct* relation
(coefficients of $(X-\alpha_j)^{-1}\bmod g(X)$ — not the naive
alternant-code formula, which only coincides with it for $g(X)=X^t$;
the notebook measures the code's actual minimum distance and confirms
it meets Goppa's $2t+1$ bound before trusting the construction further).
KeyGen masks the code exactly as §13.2 describes ($G=SG'P$); 500
random encrypt/decrypt trials, each with a genuine weight-$t$ error,
produce zero failures.

**Part B — a toy quasi-cyclic code and its decoding failure rate.** A
rate-$1/2$ quasi-cyclic code in $\mathbb F_2[X]/(X^{11}-1)$, decoded by
a bounded-distance search with a fixed correction radius. An
i.i.d.-per-coordinate noise model (the same simplifying assumption
HQC's own specification uses) is swept across increasing flip
probabilities, and the empirical decoding failure rate is measured
directly and checked against a hand-derived binomial-tail estimate —
both rise together, confirming decoding failure is a real, measurable
phenomenon rather than a footnote.

**Part C — the reaction attack, demonstrated.** A secret sparse vector
$y$ is hidden behind a 1-bit oracle that reports only whether a
crafted candidate lies within the decoder's correction radius of $y$
— exactly the "did decapsulation succeed" signal a real reaction
attack observes, nothing more. A purely statistical attack — comparing
the oracle's success rate when a given bit is guessed 1 against when
it is guessed 0, across 800 random queries — recovers the entire
secret, bit for bit, with no access to a plaintext or an error vector
at any point.

## CI

`_selftest()` in the final cell asserts every numerical claim the lab
makes. Add to `.github/workflows/notebooks.yml`:

```yaml
  ch13:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r ch13/requirements.txt
      - run: python -m jupyter nbconvert --to notebook --execute --stdout ch13/lab13.ipynb > /dev/null
```

## Exercises

The notebook implements Exercises 13.11–13.12 (Lab 13 Parts A–C) in
full. The remaining exercises are pencil-and-paper or standards-reading
exercises; worked solutions are in Appendix C of the book.

- **13.11** The Goppa-code McEliece instance with zero measured
  failures, and the quasi-cyclic instance with a measured, growing
  decoding failure rate (Lab 13 Parts A, B)
- **13.12** The reaction attack against Part B's undefended decoder
  (Lab 13 Part C)

---

Errata: `ERRATA.md` at the repository root.
Standards status: <https://mathsforeverything.com/pqc/standards>
