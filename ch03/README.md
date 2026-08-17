# Chapter 3 — Polynomial Rings

Companion code for Chapter 3 of *Maths for Post-Quantum Cryptography*
(Mathematics for Everything, Book 4).

| File | What it is |
|---|---|
| `lab03.ipynb` | **Lab 3** — negacyclic multiplication two ways, primitive $2n$-th roots of unity, and module matrix-vector products for ML-KEM's ranks |
| `build_lab03.py` | Generator for the notebook. The notebook is built from this, not hand-edited, so that it stays diffable in git |
| `requirements.txt` | Pinned dependencies |

## Running it

```bash
pip install -r requirements.txt
jupyter lab lab03.ipynb
```

Or headlessly, which is what CI does:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace lab03.ipynb
```

Same policy as Labs 1 and 2: no cryptographic library, no polynomial-algebra
package, no NTT. Negacyclic convolution and module arithmetic are both
implemented directly from the formulas in the chapter, in plain Python, so
the cost and structure the chapter derives are visible in the code rather
than hidden inside a library call.

## What the lab covers

**Part A — negacyclic multiplication, two ways.** `negacyclic_mul_formula`
implements Derivation 3.1's closed form, $h_k = c_k - c_{k+n}$, directly.
`negacyclic_mul_reduce` implements the same product the "obvious" way — full
polynomial multiply, then term-by-term reduction using $x^{n+r} \equiv -x^r$.
The two agree on 200 random polynomial pairs at $n=256$ for both standards'
moduli, and the "multiply by $x^k$" special case is checked against a direct
rotate-and-negate of the coefficient array for every shift.

**Part B — does a primitive $2n$-th root exist?** Reuses Lab 2's `order`,
`factorize` and `smallest_primitive_root`, and adds `element_of_order_2n`,
which either returns an element of order exactly $2n$ or raises — mirroring
Derivation 3.3 exactly: it works for ML-DSA's modulus ($2n=512 \mid
8380416$) and correctly refuses for ML-KEM's ($512 \nmid 3328$). The
$q=17,\ n=4$ worked example from §3.4 is reproduced as a sanity check before
moving to $n=256$.

**Part C — a module, by hand.** Builds a $k\times k$ matrix and length-$k$
vector of random $R_q$ elements for each of ML-KEM's three ranks
($k=2,3,4$), computes $As$ using Part A's multiplication, and times the
result: going from $k=2$ to $k=4$ measured a $4.04\times$ slowdown, matching
the $\bigO(k^2n^2)$ prediction from §3.5 almost exactly.

**Your turn — Exercise 3.10.** A scaffold for extending Part C to ML-DSA's
three rectangular $(k,l)$ pairs and checking the $\bigO(kl\,n^2)$ prediction.

## CI

`_selftest()` in the final cell asserts every numerical claim the lab makes.
Add to `.github/workflows/notebooks.yml`:

```yaml
  ch03:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r ch03/requirements.txt
      - run: python -m jupyter nbconvert --to notebook --execute --stdout ch03/lab03.ipynb > /dev/null
```

## Exercises

The notebook implements Exercises 3.7–3.9 (Lab 3 Parts A, B and C) in full,
and scaffolds Exercise 3.10. Exercises 3.1–3.6 and 3.11–3.12 are
pencil-and-paper or standards-reading exercises; worked solutions are in
Appendix C of the book.

- **3.7** negacyclic multiplication, two independent implementations, agreement checked at $n=256$
- **3.8** primitive $2n$-th root search for both standards' moduli, reproducing the $q=17$ worked example first
- **3.9** module matrix-vector cost vs. $k$ for ML-KEM's three ranks
- **3.10** the same, extended to ML-DSA's rectangular $(k,l)$ pairs

---

Errata: `ERRATA.md` at the repository root.
Standards status: <https://mathsforeverything.com/pqc/standards>
