# Chapter 2 — Modular Arithmetic and Finite Fields

Companion code for Chapter 2 of *Maths for Post-Quantum Cryptography*
(Mathematics for Everything, Book 4).

| File | What it is |
|---|---|
| `lab02.ipynb` | **Lab 2** — two modular-inversion algorithms compared, primitive roots and roots of unity for the standards' moduli, and $\mathbb{F}_{2^8}$ built from scratch |
| `build_lab02.py` | Generator for the notebook. The notebook is built from this, not hand-edited, so that it stays diffable in git |
| `requirements.txt` | Pinned dependencies |

## Running it

```bash
pip install -r requirements.txt
jupyter lab lab02.ipynb
```

Or headlessly, which is what CI does:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace lab02.ipynb
```

Chapter 2 needs **no cryptographic library** — only `numpy` and `matplotlib`,
and only for arrays and plotting. Extended Euclid, order-by-factor-and-divide,
primitive-root search, and $\mathbb{F}_{2^8}$ arithmetic are all written from
scratch in plain Python, deliberately: the point of this chapter is to see
exactly what each of those computes and how, not to call a library that hides
it. The heavier environment (SageMath, `liboqs-python`, PQClean, the
lattice-estimator) is set up in Appendix B and first needed in Chapter 4.

## What the lab covers

**Part A — two inverses, one comparison.** `xgcd_inverse` (extended Euclid)
and `fermat_inverse` (exponentiation by $q-2$) are checked to agree on every
unit modulo a handful of primes, then compared at scale: for $q = 3329$
(ML-KEM), the extended-Euclid step count is plotted against $a$ for all 3328
units. The count ranges from 1 to 13 steps with a mean around 7 — visible,
data-dependent variation that a timing side-channel could exploit, which is
exactly why §2.3 introduces the constant-time principle using this pair of
algorithms as the motivating example.

**Part B — orders, primitive roots, and the standards' moduli.** `order(a, q)`
uses Lagrange's theorem (order divides $q-1$) plus a one-time factorisation of
$q - 1$, rather than a brute-force scan — necessary at $q = 8380417$, where a
scan could take up to 8.3 million steps per call. Primitive roots are found
for $q = 11, 3329, 8380417$, and `has_nth_root_of_unity` checks the exact
divisibility claim from §2.5: ML-KEM's modulus has primitive 256th roots of
unity but no 512th roots; ML-DSA's has both. This single fact is why
Chapter 4's number-theoretic transform is incomplete for one standard and
complete for the other.

**Part C — $\mathbb{F}_{2^8}$ from scratch.** Byte addition (XOR) and
multiplication (carry-less polynomial multiply, reduced modulo
$x^8+x^4+x^3+x+1$ — the same polynomial AES's S-box uses) are built with no
library. Every one of the 255 non-zero bytes is confirmed to have a
multiplicative inverse by brute force, the full $256\times256$ multiplication
table is checked for the Latin-square property, and associativity and
distributivity are spot-checked on 200 random triples.

**Your turn — Exercise 2.10.** A scaffold for repeating Part C with a
different irreducible degree-8 polynomial over $\mathbb{F}_2$ (an
irreducibility test by trial division is provided) and checking that the
resulting field is isomorphic to the first.

## CI

`_selftest()` in the final cell asserts every numerical claim the lab makes,
including the exact 256th/512th-root-of-unity table for all three moduli, the
range of the extended-Euclid step count, and every field axiom checked in
Part C. Add to `.github/workflows/notebooks.yml`:

```yaml
  ch02:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r ch02/requirements.txt
      - run: python -m jupyter nbconvert --to notebook --execute --stdout ch02/lab02.ipynb > /dev/null
```

(This job is already in the repository's `notebooks.yml` — see the root
README.)

## Exercises

The notebook implements Exercises 2.7–2.9 (Lab 2 Parts A, B and C) in full,
and scaffolds Exercise 2.10. Exercises 2.1–2.6 and 2.11–2.12 are
pencil-and-paper or standards-reading exercises; worked solutions are in
Appendix C of the book.

- **2.7** extended-Euclid iteration count vs. $a$ for $q = 3329$; min, max, mean
- **2.8** smallest primitive root and an element of order 512 mod 8380417
- **2.9** the full $\mathbb{F}_{2^8}$ multiplication table and its Latin-square check
- **2.10** a second irreducible degree-8 polynomial, and the isomorphism between the two fields it builds

---

Errata: `ERRATA.md` at the repository root.
Standards status: <https://mathsforeverything.com/pqc/standards>
