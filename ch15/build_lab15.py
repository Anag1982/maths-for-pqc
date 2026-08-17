"""Build ch15/lab15.ipynb for 'Maths for Post-Quantum Cryptography'.

The notebook is generated from source rather than hand-edited so that it stays
diffable in git and reproducible in CI. Run:  python3 build_lab15.py
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
C = []
def _clean(t): return t.strip("\n").replace('\\"', '"')
def md(t): C.append(nbf.v4.new_markdown_cell(_clean(t)))
def code(t): C.append(nbf.v4.new_code_cell(_clean(t)))

# ---------------------------------------------------------------- front matter
md(r"""
# Lab 15 — Migration arithmetic, made concrete

**Maths for Post-Quantum Cryptography**, Chapter 15: *Migration Mathematics*

---

Two parts. Part A takes §15.3-§15.4's byte-counting seriously enough to
simulate it: it reconstructs, from published component sizes alone, why
a hybrid key exchange barely moves a TLS handshake while a post-quantum
certificate chain can push a connection into a second network round
trip — reproducing the qualitative finding of a real published
measurement study from first principles, not by looking up its
conclusion. Part B takes Chapter 1's Mosca-inequality exposure
calculator and removes its least honest assumption: that you know $z$,
the year a cryptographically relevant quantum computer arrives, at
all. It replaces a single guessed number with a probability
distribution and asks the only question that assumption ever let you
ask honestly: not "will I be exposed," but "how exposed, in
expectation, am I already."

### Requirements

```
python >= 3.9
```

No third-party numerical libraries are required — Part A is integer
arithmetic; Part B's Monte Carlo cross-check uses only the standard
library's `random` and `math` modules, and its closed-form check
implements the standard normal CDF via `math.erf` directly rather than
importing `scipy`.

**A note on scope.** Part A's TCP slow-start model is the textbook
mechanism (RFC 6928's 10-MSS initial window, doubling every round
trip) applied to realistic flight sizes; it is not a network
simulator, and real deployments see additional effects (packet loss,
path MTU discovery, TCP Fast Open) this lab does not model. Part B's
probability distribution over $z$ is explicitly illustrative — chosen
to have the right *qualitative* shape (a wide spread, reflecting
genuine expert disagreement) documented in surveys like the Global
Risk Institute's annual Quantum Threat Timeline Report (§15.1), not
fitted to that report's own published figures. Nothing in either part
should be read as a prediction; both are tools for turning an
uncertain belief into an honest number.
""")

# ============================================================ PART A
md(r"""
## Part A — why the KEM half is easy and the certificate half is not

Every size below is a previously verified figure from this book or a
cited primary source, not a fresh estimate: X25519 and ML-KEM-768
sizes from Table~9.1 and RFC~10024; ML-DSA-44/-65 sizes from
Table~10.1 (FIPS~204 Table~2); the certificate-chain figures from
Kampanakis and Childs-Klein's AWS/NIST measurement study
(§15.4); the TCP initial congestion window from RFC~6928.
""")

code(r"""
# --- hybrid key exchange: the ClientHello/ServerHello keyshare increase ---
X25519_PK = 32
MLKEM768_PK = 1184
MLKEM768_CT = 1088

hybrid_clienthello_increase = X25519_PK + MLKEM768_PK
hybrid_serverhello_increase = MLKEM768_CT + X25519_PK
print("ClientHello keyshare increase:", hybrid_clienthello_increase, "bytes")
print("ServerHello keyshare increase:", hybrid_serverhello_increase, "bytes")
assert hybrid_clienthello_increase == 1216   # RFC 10024 X25519MLKEM768, matches published measurements
assert hybrid_serverhello_increase == 1120
print("Part A.1: a hybrid key exchange adds a little over a kilobyte each way -- one extra Ethernet frame, not a fragmentation event")
""")

code(r"""
# --- certificate chains: leaf + one intermediate, "on the wire" sizes ---
# Kampanakis & Childs-Klein (AWS), NIST 5th PQC Standardization Conference 2024:
#   classical (ECDSA P-256) chain ~= 2.5 KB; ML-DSA-44 chain ~= 8 KB; ML-DSA-65 chain ~= 16 KB
CHAIN_BYTES = {
    "classical (ECDSA P-256)": 2_500,
    "ML-DSA-44":  8_000,
    "ML-DSA-65": 16_000,
}
# CertificateVerify signature sizes: classical ECDSA P-256 DER signature ~= 70 B;
# ML-DSA sizes from Table 10.1 (FIPS 204 Table 2).
CERTVERIFY_BYTES = {
    "classical (ECDSA P-256)": 70,
    "ML-DSA-44": 2_420,
    "ML-DSA-65": 3_309,
}
FIXED_OVERHEAD = 300  # ServerHello + EncryptedExtensions + Finished + record headers, approx.

server_flight = {
    label: CHAIN_BYTES[label] + CERTVERIFY_BYTES[label] + FIXED_OVERHEAD
    for label in CHAIN_BYTES
}
for label, total in server_flight.items():
    print(f"{label}: chain {CHAIN_BYTES[label]:>6} B + CertificateVerify {CERTVERIFY_BYTES[label]:>5} B "
          f"+ overhead {FIXED_OVERHEAD} B = {total:>6} B total server flight")
""")

md(r"""
### Derivation 15.2's threshold, simulated

RFC~6928 sets the initial TCP congestion window (`initcwnd`) to 10
maximum-segment-size packets. A server flight larger than `initcwnd`
cannot be sent in the first burst: TCP slow start requires waiting for
an acknowledgment before the window doubles and the next burst can go
out, costing one full network round trip per doubling needed.
""")

code(r"""
MSS = 1460                    # typical Ethernet/IPv4 maximum segment size, bytes
INITCWND = 10 * MSS           # RFC 6928
print(f"initcwnd = {INITCWND} bytes ({10} MSS at {MSS} B)")

def rtts_to_deliver(total_bytes, initcwnd=INITCWND):
    "Classic TCP slow start: cwnd doubles each RTT, starting at initcwnd."
    delivered, cwnd, rtts = 0, initcwnd, 0
    while delivered < total_bytes:
        delivered += cwnd
        rtts += 1
        cwnd *= 2
    return rtts

rtt_counts = {}
for label, total in server_flight.items():
    r = rtts_to_deliver(total)
    rtt_counts[label] = r
    print(f"{label}: {total} B -> {r} RTT(s) under slow start "
          f"({'fits in the first burst' if r == 1 else 'needs an extra round trip'})")

assert rtt_counts["classical (ECDSA P-256)"] == 1
assert rtt_counts["ML-DSA-44"] == 1
assert rtt_counts["ML-DSA-65"] == 2
print()
print("Part A.2: the hybrid KEM's +1.2KB never threatens initcwnd on its own; ML-DSA-65's")
print("certificate chain, reconstructed here from published component sizes alone, does --")
print("matching Kampanakis and Childs-Klein's measured finding without looking it up first.")
""")

# ============================================================ PART B
md(r"""
## Part B — Mosca's inequality without pretending to know $z$

Chapter~1's Lab~1 Part~A computed `exposure(x, y, z)` for a single
guessed value of $z$, the number of years until a cryptographically
relevant quantum computer exists. §15.1 spent several pages
establishing that no such single number is defensible: published
resource estimates for breaking RSA-2048 have themselves moved by a
factor of twenty in four years (Gidney and Ekerå's 2021 estimate of 20
million physical qubits, versus Gidney's 2025 revision to under one
million), and expert surveys report genuine, wide disagreement about
$z$ itself.

The fix is not to guess harder. It is to replace the single number $z$
with a probability distribution over $z$, and ask a better question:
not "am I exposed," but "what is my *expected* exposure."
""")

code(r"""
import math, random

# An explicitly ILLUSTRATIVE model for z = years-from-now until a CRQC exists.
# Chosen for the right QUALITATIVE shape -- a wide spread, reflecting genuine
# expert disagreement documented in surveys like the Global Risk Institute's
# annual Quantum Threat Timeline Report -- and NOT fitted to that report's own
# published figures. Median z = 18 years; SIGMA controls the spread.
MU = math.log(18.0)
SIGMA = 0.40

def cdf_normal(t):
    return 0.5 * (1 + math.erf(t / math.sqrt(2)))

def P_exposed(K):
    "P(z < K): probability the CRQC arrives before the migration-plus-secrecy window closes."
    d = (math.log(K) - MU) / SIGMA
    return cdf_normal(d)

def E_exposed_closed_form(K):
    "E[max(K - z, 0)], the expected number of already-exposed years, in closed form."
    d2 = (math.log(K) - MU) / SIGMA
    d1 = d2 - SIGMA
    return K * cdf_normal(d2) - math.exp(MU + SIGMA**2 / 2) * cdf_normal(d1)

def E_exposed_montecarlo(K, n=500_000, seed=1):
    "Same quantity, estimated by direct sampling -- an independent check on the closed form."
    rng = random.Random(seed)
    total = 0.0
    for _ in range(n):
        z = math.exp(rng.normalvariate(MU, SIGMA))
        total += max(K - z, 0.0)
    return total / n

print(f"median modelled z: {math.exp(MU):.1f} years")
print(f"{'x':>3} {'y':>3} {'K=x+y':>6}  {'P(exposed)':>11}  {'E[years], closed-form':>22}  {'E[years], Monte Carlo':>22}")
results = {}
for x, y in [(10, 6), (10, 5), (5, 3), (15, 7)]:
    K = x + y
    p = P_exposed(K)
    e_cf = E_exposed_closed_form(K)
    e_mc = E_exposed_montecarlo(K)
    results[(x, y)] = (p, e_cf, e_mc)
    print(f"{x:>3} {y:>3} {K:>6}  {p:>11.4f}  {e_cf:>22.4f}  {e_mc:>22.4f}")

for (x, y), (p, e_cf, e_mc) in results.items():
    assert abs(e_cf - e_mc) < 0.01, "closed-form and Monte Carlo should agree closely"
print()
print("Part B.1: closed-form and Monte Carlo agree to within a hundredth of a year across")
print("every (x, y) pair -- the same 'derive it, then verify it a second, independent way'")
print("discipline this book has applied to every other numerical claim.")
""")

md(r"""
### What shrinking $y$ actually buys you

Chapter~1 could only say, deterministically, whether a given $(x,y,z)$
triple was already lost. The probabilistic version lets you ask the
question migration planning actually needs: how much does cutting your
migration time $y$ reduce your *expected* exposure, given honest
uncertainty about $z$?
""")

code(r"""
X_FIXED = 10   # years the data must stay confidential, held fixed
sweep = {}
for y in [8, 6, 4, 2]:
    K = X_FIXED + y
    p = P_exposed(K)
    e = E_exposed_closed_form(K)
    sweep[y] = (p, e)
    print(f"y={y} years to migrate: P(exposed)={p:.3f}, E[exposed years]={e:.3f}")

# Halving y from 8 to 4 years: does expected exposure also halve?
e_at_8, e_at_4 = sweep[8][1], sweep[4][1]
reduction_fraction = 1 - (e_at_4 / e_at_8)
print()
print(f"halving y from 8 to 4 cuts E[exposed years] from {e_at_8:.3f} to {e_at_4:.3f}: "
      f"a {reduction_fraction:.1%} reduction, not merely 50%")
assert reduction_fraction > 0.5, "the reduction should be MORE than proportional here"
print()
print("Part B.2: while K=x+y sits near the modelled z distribution's median, cutting y buys")
print("a MORE than proportional reduction in expected exposure -- the return on shrinking")
print("migration time is convex here, not linear, which is exactly the argument for treating")
print("crypto-agility (S15.2) as an investment with compounding returns, not a flat compliance cost.")
""")

# --------------------------------------------------------------------- close
md(r"""
## What to take away

Part A turns §15.3 and §15.4's prose argument -- hybrid key exchange
is a cheap, almost invisible upgrade; certificate-chain migration is
not -- into a number a network engineer would recognise immediately: a
1.2KB keyshare never threatens a TCP handshake, but a 16KB
post-quantum certificate chain can cost a full extra round trip,
reconstructed here from published sizes alone and landing exactly
where a real measurement study (Kampanakis and Childs-Klein) found it
by instrumenting actual connections. Part B does the same honesty
check on Chapter~1's own Mosca-inequality calculator: replacing a
single guessed $z$ with a distribution does not resolve the
uncertainty about when a CRQC arrives -- nothing can, honestly -- but
it turns that uncertainty into an expected-value calculation instead
of a coin flip, and it is the closest this book gets to a formula for
why "migrate now" is the right answer even though nobody actually
knows $z$.
""")

code(r"""
def _selftest():
    # Part A
    assert hybrid_clienthello_increase == 1216
    assert hybrid_serverhello_increase == 1120
    assert rtt_counts["classical (ECDSA P-256)"] == 1
    assert rtt_counts["ML-DSA-44"] == 1
    assert rtt_counts["ML-DSA-65"] == 2

    # Part B
    for (x, y), (p, e_cf, e_mc) in results.items():
        assert abs(e_cf - e_mc) < 0.01
    assert 0.0 <= P_exposed(16) <= 1.0

    print("all checks passed")

_selftest()
""")

nb["cells"] = C
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11"},
}

with open("lab15.ipynb", "w") as fh:
    nbf.write(nb, fh)
print(f"wrote lab15.ipynb with {len(C)} cells")
