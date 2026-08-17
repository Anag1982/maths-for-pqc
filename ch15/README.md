# Chapter 15 — Migration Mathematics

Companion code for Chapter 15 of *Maths for Post-Quantum Cryptography*
(Mathematics for Everything, Book 4).

| File | What it is |
|---|---|
| `lab15.ipynb` | **Lab 15** — TLS handshake and certificate-chain byte arithmetic with a TCP slow-start round-trip simulation, and a probabilistic extension of Chapter 1's Mosca-inequality exposure calculator |
| `build_lab15.py` | Generator for the notebook. The notebook is built from this, not hand-edited, so that it stays diffable in git |
| `requirements.txt` | Pinned dependencies |

## Running it

```bash
pip install -r requirements.txt
jupyter lab lab15.ipynb
```

Or headlessly, which is what CI does:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace lab15.ipynb
```

No third-party library anywhere in this notebook — everything is the
Python standard library (`math`, `random`).

## What the lab covers

**Part A — why the KEM half of migration is easy and the certificate
half is not.** Reconstructs, from previously verified component sizes
alone (X25519 and ML-KEM-768 from Table 9.1/RFC 10024, ML-DSA from
Table 10.1/FIPS 204, certificate-chain figures from a real AWS/NIST
measurement study), the ClientHello/ServerHello byte increase from a
hybrid key exchange (a little over a kilobyte each way) against the
byte increase from a post-quantum certificate chain (up to 16KB). A
TCP slow-start simulation using RFC 6928's initial congestion window
then shows computationally that the hybrid keyshare never threatens a
handshake's first round trip, while an ML-DSA-65 certificate chain
does — landing on the same qualitative finding a real measurement
study (Kampanakis and Childs-Klein, AWS) reported from live
connections, reconstructed here from published sizes alone.

**Part B — Mosca's inequality without pretending to know z.** Chapter
1's Lab 1 computed exposure for a single guessed arrival year for a
cryptographically relevant quantum computer. This lab replaces that
guess with an explicitly illustrative probability distribution (chosen
for the right qualitative shape — wide, genuine expert disagreement —
not fitted to any specific survey's published numbers) and computes
the *expected* number of already-exposed years in closed form, cross-
checked against an independent Monte Carlo estimate. A sweep over
migration time `y` shows the return on shrinking migration time is
convex, not linear, in the region most real organisations' numbers
fall into — verified computationally, not asserted.

## A note on scope

Part A's TCP model is the textbook slow-start mechanism, not a network
simulator; real deployments see packet loss, path MTU discovery, and
other effects this lab does not model. Part B's distribution over the
CRQC arrival year is explicitly illustrative, chosen only to have the
right qualitative shape; it does not claim to reproduce any specific
survey's own published figures, and the chapter text is careful to say
so.

## CI

`_selftest()` in the final cell asserts every numerical claim the lab
makes. Add to `.github/workflows/notebooks.yml`:

```yaml
  ch15:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r ch15/requirements.txt
      - run: python -m jupyter nbconvert --to notebook --execute --stdout ch15/lab15.ipynb > /dev/null
```

## Exercises

The notebook implements Exercises 15.10–15.11 (Lab 15 Parts A–B) in
full. The remaining exercises are pencil-and-paper or standards-reading
exercises; worked solutions are in Appendix C of the book.

- **15.10** The TLS handshake and certificate-chain byte arithmetic, and
  the TCP slow-start round-trip simulation (Lab 15 Part A)
- **15.11** The probabilistic Mosca-inequality calculator, verified by
  an independent Monte Carlo check (Lab 15 Part B)

---

Errata: `ERRATA.md` at the repository root.
Standards status: <https://mathsforeverything.com/pqc/standards>
