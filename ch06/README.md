# Chapter 6 — Hard Problems

Companion code for Chapter 6 of *Maths for Post-Quantum Cryptography*
(Mathematics for Everything, Book 4).

| File | What it is |
|---|---|
| `lab06.ipynb` | **Lab 6** — brute-force SVP and CVP, the combinatorial cost of being exact, the BDD uniqueness radius, and toy GapSVP instances, all built from scratch |
| `build_lab06.py` | Generator for the notebook. The notebook is built from this, not hand-edited, so that it stays diffable in git |
| `requirements.txt` | Pinned dependencies |

## Running it

```bash
pip install -r requirements.txt
jupyter lab lab06.ipynb
```

Or headlessly, which is what CI does:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace lab06.ipynb
```

Same policy as Labs 1-5: no lattice-reduction library, no SageMath. Every
algorithm is implemented directly from the chapter's definitions in plain
Python, so the object the chapter defines is the object the code computes —
nothing is hidden inside a library call.

## What the lab covers

**Part A — SVP and CVP by brute force.** `svp_bruteforce` and
`cvp_bruteforce` implement Definitions 6.1 and 6.2 by exhaustive search over
small integer coefficient vectors, checked against the book's running
example ($\lambda_1=\sqrt{10}$; the closest lattice point to $t=(2,2)$ is
$(1,3)$ at distance $\sqrt2$, with the two Exercise 6.1 runner-up candidates
confirmed farther away).

**Part B — the cost of being exact.** Benchmarks `svp_bruteforce` across
dimension 2 through 8 with a fixed coefficient range, plotting search-space
size and wall-clock time on a semilog axis. The search space grows by a
factor of roughly 34,000 from $n=2$ to $n=8$ while the basis itself only
grew by a factor of 4 — a small, honest demonstration of why Section 6.2's
"exact is the wrong question" is not just a rhetorical point.

**Part C — the uniqueness radius.** Reproduces Figure 6.2 numerically: the
unique-decoding case (noise strictly under $\lambda_1/2$) and the exact tie
at $\lambda_1/2$ between $(0,0)$ and $(-3,1)$ from Derivation 6.1, plus a
300-trial randomized sweep confirming decoding is unique whenever noise
stays strictly inside the $\lambda_1/2$ ball.

**Part D — toy GapSVP instances.** `gap_svp_decide` implements
Definition 6.4 by brute force, correctly separates three $(\mathbb{Z}^n, 1)$
YES-instances from three $(q\mathbb{Z}^n, 1)$ NO-instances, then times how
far $n$ can go before even this promise-problem toy exceeds one second of
brute-force search — the same combinatorial wall Part B hits, from a
different angle.

## CI

`_selftest()` in the final cell asserts every numerical claim the lab makes.
Add to `.github/workflows/notebooks.yml`:

```yaml
  ch06:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r ch06/requirements.txt
      - run: python -m jupyter nbconvert --to notebook --execute --stdout ch06/lab06.ipynb > /dev/null
```

## Exercises

The notebook implements Exercises 6.8–6.10 (Lab 6 Parts A-D) in full.
Exercises 6.1–6.7 and 6.11 are pencil-and-paper or literature-reading
exercises; worked solutions are in Appendix C of the book.

- **6.8** Brute-force SVP/CVP on the running example, including the runner-up distance check (Lab 6 Part A)
- **6.9** The combinatorial cost of exact search, dimension 2 through 8 (Lab 6 Part B)
- **6.10** BDD uniqueness radius and toy GapSVP instances (Lab 6 Parts C, D)

---

Errata: `ERRATA.md` at the repository root.
Standards status: <https://mathsforeverything.com/pqc/standards>
