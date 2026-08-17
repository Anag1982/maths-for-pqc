# Chapter 16 — The On-Ramp

Companion code for Chapter 16 of *Maths for Post-Quantum Cryptography*
(Mathematics for Everything, Book 4).

| File | What it is |
|---|---|
| `lab16.ipynb` | **Lab 16** — a toy MPC-in-the-head signature built from scratch (Part A), and a toy Unbalanced Oil and Vinegar trapdoor built from scratch (Part B) |
| `build_lab16.py` | Generator for the notebook. The notebook is built from this, not hand-edited, so that it stays diffable in git |
| `requirements.txt` | Pinned dependencies |

## Running it

```bash
pip install -r requirements.txt
jupyter lab lab16.ipynb
```

Or headlessly, which is what CI does:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace lab16.ipynb
```

No third-party library anywhere in this notebook — everything is the
Python standard library (`hashlib`, `random`, `time`). All finite-field
linear algebra (matrix inversion, Gaussian elimination) needed for Part B
is implemented directly rather than imported.

## What the lab covers

**Part A — MPC-in-the-head, for real.** Implements Derivation 16.2's
$N=3$-party, Fiat–Shamir-driven zero-knowledge proof of knowledge from
scratch for a toy quadratic relation $f(x) = ax^2+bx=y \pmod q$: additive
secret sharing, a Beaver-triple-style multiplication protocol for the one
nonlinear step, commitments, a Fiat–Shamir challenge selecting which
single party of three stays hidden, and verification of the opened
parties' views. It empirically confirms completeness (an honest prover
with a genuine witness always passes) and soundness (a prover without a
valid witness is caught with probability $(N-1)/N$ per round, so evades
detection across $\tau$ independent rounds with probability $(1/N)^\tau$
— verified for $\tau \in \{1,2,4\}$ against the closed-form prediction at
a four-sigma statistical tolerance, then verified again at $N=5$ to
confirm the bound's dependence on $N$).

One subtlety the lab documents rather than papering over: since
$f(x)=ax^2+bx$ is quadratic, a randomly drawn "wrong" witness is actually
a *second valid root* with probability about $1/q$. Over the toy field
$q=101$ that is roughly 1%, which is larger than the true $\tau=4$
prediction $(1/3)^4 \approx 1.2\%$ and would make a perfectly sound
construction look broken. The measurement therefore draws genuine
non-witnesses explicitly (`draw_non_witness`). This is an artifact of the
field being small enough to inspect by hand, not of the construction.

**Part B — a working oil-and-vinegar trapdoor.** Implements Section 16.4's
Unbalanced Oil and Vinegar construction end to end: a central quadratic
map with no oil-oil cross terms, a random invertible change of basis
hiding it as a public key, signing by fixing vinegar values and solving
the resulting linear system in the oil variables, and verification
against the public key alone. A small sweep (`v,o` from `(6,3)` up to
`(10,5)`, over a smaller field to keep runtimes short) times a legitimate
signer against a forger who does not know the oil/vinegar split and must
fall back to uniform random search over the full variable space —
Definition 16.1's worst-case-NP-hard, average-case-conjectured MQ problem,
with no shortcut available. The forger/signer time ratio grows by more
than two orders of magnitude across the sweep (roughly 22× to 7,800× in
the run committed here), confirming the gap widens rather than narrows as
the parameters grow — at toy scale, not at Table 16.3's real security
levels.

## A note on scope

Part A's $N=3$ construction is chosen to match Derivation 16.2's
exposition exactly, not to reproduce FAEST/MQOM/SDitH's actual
VOLE-in-the-head or TCitH machinery, which use much larger $N$
(Table 16.2) and different (though related) masking techniques. Part B's
field and parameter sizes are chosen so that both the trapdoor-based
signer and the brute-force forger finish in well under a second in this
notebook; they are not UOV's real Table 16.3 parameters and should not be
read as any kind of security estimate. Both parts exist to verify the
*shape* of an argument the chapter makes, not to benchmark a live scheme.

## CI

`_selftest()` in the final cell asserts every numerical claim the lab
makes. Add to `.github/workflows/notebooks.yml`:

```yaml
  ch16:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r ch16/requirements.txt
      - run: python -m jupyter nbconvert --to notebook --execute --stdout ch16/lab16.ipynb > /dev/null
```

## Exercises

The notebook implements Exercises 16.9–16.11 (Lab 16 Parts A–B, plus the
$N=5$ extension) in full. The remaining exercises are pencil-and-paper or
standards-reading exercises; worked solutions are in Appendix C of the
book.

- **16.9** The $N=3$-party MPC-in-the-head protocol, completeness and
  soundness verified empirically against the closed-form bounds (Lab 16
  Part A)
- **16.10** The oil-and-vinegar trapdoor, signer-versus-forger timing
  sweep (Lab 16 Part B)
- **16.11** The $N=5$ extension of Part A's soundness experiment, run and
  checked in full — every helper takes `n` as a parameter, so the $N=5$
  case is the same code with one argument changed

---

Errata: `ERRATA.md` at the repository root.
Standards status: <https://mathsforeverything.com/pqc/standards>
