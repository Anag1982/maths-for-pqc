# Chapter 14 — Isogenies: A Cautionary Tale

Companion code for Chapter 14 of *Maths for Post-Quantum Cryptography*
(Mathematics for Everything, Book 4).

| File | What it is |
|---|---|
| `lab14.ipynb` | **Lab 14** — Vélu's isogeny formulas built and checked from scratch, a toy SIDH-style key exchange with a genuine four-way secret, and a toy demonstration of exactly what the auxiliary torsion-point data Castryck and Decru exploited actually leaks |
| `build_lab14.py` | Generator for the notebook. The notebook is built from this, not hand-edited, so that it stays diffable in git |
| `requirements.txt` | Pinned dependencies |

## Running it

```bash
pip install -r requirements.txt
jupyter lab lab14.ipynb
```

Or headlessly, which is what CI does:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace lab14.ipynb
```

No elliptic-curve or number-theory library anywhere in this notebook —
point addition, scalar multiplication, and Vélu's formulas are all
plain modular arithmetic over `int`.

## What the lab covers

**Part A — Vélu's formulas, implemented and checked.** `velu_isogeny`
implements Derivation 14.1's odd-prime-degree construction directly;
it is checked against a hand-worked numerical example ($p=101$,
degree-3 kernel) before being trusted further, then checked for the
one property that actually matters — $\varphi(P+Q)=\varphi(P)+\varphi(Q)$
— on a toy curve of order 90 over $\mathbb F_{73}$ chosen so its
3-torsion is fully rational ($(\mathbb Z/3)^2$, four subgroups of order
3) while its 5-torsion is only a single cyclic subgroup. Walking all
four degree-3 kernels already surfaces the fact Part C exploits: two
of the four land on curves with the *same* j-invariant.

**Part B — a toy SIDH-style key exchange.** Alice's secret is one of
the four degree-3 kernels; Bob's is the (non-secret, in this toy) degree-5
kernel. Each publishes an image curve plus the images of the *other*
party's public torsion points under their own secret isogeny — exactly
what real SIDH publishes. Both parties independently reach the same
shared curve, checked for all four of Alice's possible secrets.

**Part C — what the auxiliary point actually leaks.** With Alice's
secret fixed, an eavesdropper who sees only her published curve is left
with two tied candidates (same j-invariant, from Part A's own finding).
Given the published auxiliary point as well, exactly one candidate
survives. This is a simplified, honest illustration of *why* SIDH's
auxiliary torsion data is exploitable — not a reproduction of
Castryck-Decru's actual genus-2/Kani's-theorem construction, which is
described in §14.3 rather than implemented here.

## A note on scope

Real SIDH needs both parties' relevant torsion to be fully
two-dimensional, which forces much larger curves over $\mathbb
F_{p^2}$; this toy curve gives that property to only one party to stay
brute-force-checkable by eye. The degree-2 ("even") branch of Vélu's
formulas, needed for real SIDH's power-of-two side, is not implemented
here — both isogeny steps in this lab use only the odd-prime-degree
formula.

## CI

`_selftest()` in the final cell asserts every numerical claim the lab
makes. Add to `.github/workflows/notebooks.yml`:

```yaml
  ch14:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r ch14/requirements.txt
      - run: python -m jupyter nbconvert --to notebook --execute --stdout ch14/lab14.ipynb > /dev/null
```

## Exercises

The notebook implements Exercises 14.10–14.11 (Lab 14 Parts A–C) in
full. The remaining exercises are pencil-and-paper or standards-reading
exercises; worked solutions are in Appendix C of the book.

- **14.10** Vélu's formulas checked against a hand-worked example, the
  homomorphism property confirmed on a fresh curve, and the toy
  SIDH-style exchange matching on the shared curve for all four
  possible secrets (Lab 14 Parts A and B)
- **14.11** The auxiliary-torsion-point leak, isolated and measured
  (Lab 14 Part C)

---

Errata: `ERRATA.md` at the repository root.
Standards status: <https://mathsforeverything.com/pqc/standards>
