# Chapter 11 — FIPS 205: SLH-DSA

Companion code for Chapter 11 of *Maths for Post-Quantum Cryptography*
(Mathematics for Everything, Book 4).

| File | What it is |
|---|---|
| `lab11.ipynb` | **Lab 11** — Lamport signatures broken on purpose, a WOTS+ chain and its checksum, a Merkle tree and authentication path, and a full toy SLH-DSA built end to end |
| `build_lab11.py` | Generator for the notebook. The notebook is built from this, not hand-edited, so that it stays diffable in git |
| `requirements.txt` | Pinned dependencies |

## Running it

```bash
pip install -r requirements.txt
jupyter lab lab11.ipynb
```

Or headlessly, which is what CI does:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace lab11.ipynb
```

Same policy as every earlier lab, taken further here than anywhere
else in the book: no cryptographic library at all, not even for the
hash function beyond Python's built-in `hashlib`. Every construction
in this notebook — Lamport, WOTS+, Merkle trees, FORS, the SLH-DSA
hypertree — is a hash function called directly, because that is the
entire point of the chapter.

## What the lab covers

**Part A — Lamport, and breaking it on purpose.** `lamport_keygen`/
`lamport_sign`/`lamport_verify` implement Definition 11.1 exactly at a
toy 64-bit digest length. One legitimate signature, then a second on
the bitwise complement of the first message, then full secret-key
extraction from the two signatures and a forged signature on a third,
never-signed message — Derivation 11.1's worst case, executed rather
than just argued.

**Part B — WOTS+ and the checksum's job.** `chain`/`wots_sign`/
`wots_pk_from_sig` implement Definition 11.2's hash chain, digit
encoding and checksum exactly, at $w=16$ (FIPS 205's real value).
`len2` is computed from the general formula rather than hard-coded,
so the toy's smaller $n$ correctly yields `len2=2` instead of FIPS
205's `len2=3`. The checksum-free forgery from Derivation 11.2 is
implemented directly: it fools a verifier that checks only the
message-digit chains, on every one of 50 trials, and is rejected by
the real verifier (which also checks the checksum chains) on all 50.

**Part C — a Merkle tree and its authentication path.** An 8-leaf
tree reproducing Figure 11.3 exactly: the authentication path for a
chosen leaf recomputes the true root, corrupting that leaf breaks
verification, and corrupting an unrelated leaf's storage has no
effect on the proof at all — the proof is a pure function of the leaf
being proven, its path, and the root, nothing else.

**Part D — a toy SLH-DSA end to end.** `slh_keygen`/`slh_sign`/
`slh_verify` assemble Parts A–C plus a small FORS instance
($k=4$, $a=3$) into a working, single-layer ($d=1$) toy signature
scheme. 48 signatures all verify; a signature checked against a
different message, or with one corrupted byte, is correctly rejected.
Because 48 messages exceed the toy's 16 hypertree leaves, a
leaf-index collision is pigeonhole-guaranteed among them: the lab
finds that colliding pair and confirms the WOTS+ portions of their
two signatures are byte-for-byte identical while their FORS portions
differ — direct, measured evidence for §11.5's claim that a reused
leaf's WOTS+ key signs one *fixed* value both times, never the
message itself. A final check confirms the measured signature size
matches Table 11.2's byte-size formula exactly (120 bytes, with the
formula's randomness prefix omitted to match the toy's deterministic
signing mode).

## CI

`_selftest()` in the final cell asserts every numerical claim the lab
makes. Add to `.github/workflows/notebooks.yml`:

```yaml
  ch11:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r ch11/requirements.txt
      - run: python -m jupyter nbconvert --to notebook --execute --stdout ch11/lab11.ipynb > /dev/null
```

## Exercises

The notebook implements Exercises 11.12–11.14 (Lab 11 Parts A–D) in
full. The remaining exercises are pencil-and-paper or standards-reading
exercises; worked solutions are in Appendix C of the book.

- **11.12** Lamport reuse and the WOTS+ checksum forgery, including the
  average number of disagreeing bit positions between two random
  messages (Lab 11 Parts A, B)
- **11.13** The Merkle tree and authentication path at a larger tree
  height (Lab 11 Part C)
- **11.14** The toy SLH-DSA's leaf-collision check at a smaller,
  faster-colliding hypertree height (Lab 11 Part D)

---

Errata: `ERRATA.md` at the repository root.
Standards status: <https://mathsforeverything.com/pqc/standards>
