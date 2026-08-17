# Chapter 5 — Lattices

Companion code for Chapter 5 of *Maths for Post-Quantum Cryptography*
(Mathematics for Everything, Book 4).

| File | What it is |
|---|---|
| `lab05.ipynb` | **Lab 5** — Gram-Schmidt orthogonalisation, unimodular equivalence, Minkowski's bound vs. the Gaussian heuristic, and a $q$-ary lattice, all built from scratch |
| `build_lab05.py` | Generator for the notebook. The notebook is built from this, not hand-edited, so that it stays diffable in git |
| `requirements.txt` | Pinned dependencies |

## Running it

```bash
pip install -r requirements.txt
jupyter lab lab05.ipynb
```

Or headlessly, which is what CI does:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace lab05.ipynb
```

Same policy as Labs 1-4: no lattice-reduction library, no SageMath. Every
algorithm is implemented directly from the chapter's derivations in plain
Python, so the object the chapter defines is the object the code computes —
nothing is hidden inside a library call.

## What the lab covers

**Part A — a lattice from a basis.** `gram_schmidt` implements Section 5.3's
orthogonalisation directly; the determinant identity
$|\det B| = \prod_i \|b_i^*\|$ is checked against the direct determinant on
the book's running example and on 200 random integer bases in dimensions
2-6.

**Part B — unimodular equivalence.** Reproduces Figure 5.2 as numbers: the
book's good basis $\{(4,2),(1,3)\}$ and the bad basis reached by
Derivation 5.1's unimodular row operation generate the *identical* point
set within a bounded box, while the bad basis's Gram-Schmidt vectors are
wildly uneven (one over 13 long, one under 1). A general experiment at
dimension 10 measures how large that gap gets under 100 random unimodular
transforms — foreshadowing why Chapter 8's lattice reduction exists at all.

**Part C — successive minima vs. the two bounds.** Brute-force shortest-
vector search on random small lattices confirms Minkowski's bound
(Section 5.4) is never violated, and tracks the Gaussian heuristic's
(Section 5.5) accuracy against dimension 2 through 6 — a genuinely
asymptotic estimate, and the notebook shows it honestly under-performing at
the toy sizes brute force can still reach.

**Part D — a $q$-ary lattice.** Builds $\Lambda_q^\perp(A)$ for random $A$
by exhaustive counting, confirms $\det = q^m$ (Derivation 5.5) for several
$(q,m,n)$ triples, and reproduces Figure 5.5's toy example
($q=5$, $A=(2,1)$) exactly, including checking that the two vectors drawn
in the figure form an actual basis of the lattice.

## CI

`_selftest()` in the final cell asserts every numerical claim the lab makes.
Add to `.github/workflows/notebooks.yml`:

```yaml
  ch05:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r ch05/requirements.txt
      - run: python -m jupyter nbconvert --to notebook --execute --stdout ch05/lab05.ipynb > /dev/null
```

## Exercises

The notebook implements Exercises 5.10–5.12 (Lab 5 Parts A-D) in full.
Exercises 5.1–5.9 and 5.13 are pencil-and-paper or standards-reading
exercises; worked solutions are in Appendix C of the book.

- **5.10** Gram-Schmidt and unimodular equivalence (Lab 5 Parts A, B), including the worst/best GSO-vector ratio at dimension 10
- **5.11** Minkowski's bound vs. the Gaussian heuristic across dimension (Lab 5 Part C)
- **5.12** $q$-ary lattice determinant, for reader-chosen $(q,m,n)$ (Lab 5 Part D)

---

Errata: `ERRATA.md` at the repository root.
Standards status: <https://mathsforeverything.com/pqc/standards>
