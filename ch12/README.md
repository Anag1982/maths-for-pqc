# Chapter 12 — FN-DSA / FALCON

Companion code for Chapter 12 of *Maths for Post-Quantum Cryptography*
(Mathematics for Everything, Book 4).

| File | What it is |
|---|---|
| `lab12.ipynb` | **Lab 12** — a real toy NTRU key pair (the NTRU equation actually solved), $B_{\rm pub}$/$B_{\rm sec}$ proven to generate one lattice, the parallelepiped leak measured and fixed, and a precision-degradation experiment |
| `build_lab12.py` | Generator for the notebook. The notebook is built from this, not hand-edited, so that it stays diffable in git |
| `requirements.txt` | Pinned dependencies |

## Running it

```bash
pip install -r requirements.txt
jupyter lab lab12.ipynb
```

Or headlessly, which is what CI does:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace lab12.ipynb
```

`numpy` does the floating-point work (deliberately — floating point is
this chapter's subject); `sympy` is used once, for an exact-arithmetic
check that two integer bases generate the same lattice.

## What the lab covers

**Part A — a toy NTRU lattice.** A compact version of FALCON's own
key-generation algorithm (Pornin & Prest 2019): short ternary $f,g$
sampled at $n=8$, the NTRU equation $fG-gF=q$ solved exactly via a
recursive field-norm reduction down to a base-case extended Euclidean
step, then Babai-reduced back down to short $F,G$. $B_{\rm pub}$ and
$B_{\rm sec}$ are built explicitly as $16\times16$ integer matrices,
and `sympy` confirms $B_{\rm sec}\cdot B_{\rm pub}^{-1}$ is an exact
integer, unimodular matrix — proof, not assertion, that both bases
generate the identical lattice.

**Part B — the leak, and Klein's fix, measured.** Naive Babai
nearest-plane rounding is run against $B_{\rm sec}$ on 3,000 random
targets; the empirical covariance of the rounding error matches a
theoretical prediction shaped by $B_{\rm sec}$'s own Gram–Schmidt
directions (cosine similarity above 0.99) far better than an isotropic
prediction — Derivation 12.1's leak, reproduced by measurement, not
argued. Klein's randomised-rounding fix is then run through the same
experiment and the result reverses: it matches the isotropic
prediction, not the basis-shaped one. Both results are then repeated
against a second, genuinely different secret basis of the *same*
lattice (built via a small unimodular row transform of $B_{\rm sec}$,
confirmed by the same exact-arithmetic check as Part A) — Klein's fix
lands close to isotropic for both bases, exactly as the "independent
of which particular short basis produced it" claim requires.

**Part C — why 53 bits.** Part B's randomised sampler is rerun with
every intermediate real value snapped to a coarse step size, standing
in for a low-precision numeric format. Isotropy survives essentially
unchanged from a step of $10^{-4}$ down through a step of $2$, then
collapses sharply by a step of $4$–$8$ — a measured threshold behind
§12.5's insistence on 53-bit (binary64) precision, not an assumed one.

## CI

`_selftest()` in the final cell asserts every numerical claim the lab
makes. Add to `.github/workflows/notebooks.yml`:

```yaml
  ch12:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r ch12/requirements.txt
      - run: python -m jupyter nbconvert --to notebook --execute --stdout ch12/lab12.ipynb > /dev/null
```

## Exercises

The notebook implements Exercises 12.11–12.12 (Lab 12 Parts A–C) in
full. The remaining exercises are pencil-and-paper or standards-reading
exercises; worked solutions are in Appendix C of the book.

- **12.11** The parallelepiped leak and Klein's fix, at increasing toy
  dimension (Lab 12 Parts A, B)
- **12.12** The precision threshold at which Klein's fix stops working
  (Lab 12 Part C)

---

Errata: `ERRATA.md` at the repository root.
Standards status: <https://mathsforeverything.com/pqc/standards>
