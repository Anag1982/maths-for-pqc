# Chapter 4 — The Number-Theoretic Transform

Companion code for Chapter 4 of *Maths for Post-Quantum Cryptography*
(Mathematics for Everything, Book 4).

| File | What it is |
|---|---|
| `lab04.ipynb` | **Lab 4** — ML-KEM's incomplete NTT built from scratch, benchmarked against Chapter 3's naive convolution, then Montgomery and Barrett reduction for both standards' moduli |
| `build_lab04.py` | Generator for the notebook. The notebook is built from this, not hand-edited, so that it stays diffable in git |
| `requirements.txt` | Pinned dependencies |

## Running it

```bash
pip install -r requirements.txt
jupyter lab lab04.ipynb
```

Or headlessly, which is what CI does:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace lab04.ipynb
```

Same policy as Labs 1-3: no cryptographic library. `NTT`, `NTT_inv`,
`MultiplyNTTs` and `BaseCaseMultiply` are transliterated directly from FIPS
203 Algorithms 9-12, and Montgomery/Barrett reduction are implemented from
the formulas in Derivations 4.4 and 4.5, so the exact arithmetic the chapter
derives is visible in the code rather than hidden inside a library call.

## What the lab covers

**Part A — build the incomplete transform.** `ntt` and `ntt_inv` are
line-for-line transliterations of Algorithms 9 and 10 for ML-KEM's
parameters ($n=256$, $q=3329$, $\zeta=17$); `base_case_multiply` implements
Derivation 4.3's formula and `multiply_ntts` implements Algorithm 11 on top
of it. Checked three ways: $\mathrm{NTT}^{-1}(\mathrm{NTT}(f)) = f$ on 200
random polynomials, NTT-based multiplication agrees with Chapter 3 Lab's
naive negacyclic convolution on 1,000 random pairs, and the $q=17$, $n=4$,
$\psi=9$ worked example from §4.2 is reproduced by direct evaluation and
recovered exactly by the inverse formula.

**Part B — benchmark the difference.** Times naive $\mathcal{O}(n^2)$
convolution against NTT-based multiplication at the real size ($n=256$,
300 trials), then generalises to a toy `ntt_generic`/`find_modulus_and_root`
pair that finds a working $(q,\zeta)$ for any power-of-two $n$ and times the
forward transform alone against naive evaluation at $n=8,16,\ldots,256$,
plotted on log-log axes to show the $\mathcal{O}(n^2)$-versus-$\mathcal{O}(n
\log n)$ gap widen with $n$.

**Part C — reduction without division.** `montgomery_reduce` and
`barrett_reduce` implement Derivations 4.4 and 4.5 exactly, including the
book's hand-checkable $q=17$, $R=32$, $T=100$ worked example
($\to 1$), then are checked against plain `% q` on thousands of random
values for both ML-KEM's modulus (3329) and ML-DSA's (8380417).

## CI

`_selftest()` in the final cell asserts every numerical claim the lab makes.
Add to `.github/workflows/notebooks.yml`:

```yaml
  ch04:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r ch04/requirements.txt
      - run: python -m jupyter nbconvert --to notebook --execute --stdout ch04/lab04.ipynb > /dev/null
```

## Exercises

The notebook implements Exercises 4.7–4.9 (Lab 4 Parts A, B and C) in full,
and extends to Exercise 4.10 (ML-DSA's complete transform). Exercises
4.1–4.6, 4.11–4.12 and 4.13 are pencil-and-paper, standards-reading, or
hand-count exercises; worked solutions are in Appendix C of the book.

- **4.7** build ML-KEM's incomplete NTT from scratch; roundtrip and multiplication-agreement checked at $n=256$
- **4.8** benchmark naive vs. NTT-based multiplication, at $n=256$ and across smaller toy sizes
- **4.9** Montgomery and Barrett reduction for both standards' moduli, checked against `% q`
- **4.10** extend Part A to ML-DSA's complete transform; confirm no `BaseCaseMultiply` is needed
- **4.13** count scalar multiplications exactly for ML-KEM-768's $As$, naive vs. transform-based

---

Errata: `ERRATA.md` at the repository root.
Standards status: <https://mathsforeverything.com/pqc/standards>
