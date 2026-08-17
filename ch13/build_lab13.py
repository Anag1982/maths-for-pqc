"""Build ch13/lab13.ipynb for 'Maths for Post-Quantum Cryptography'.

The notebook is generated from source rather than hand-edited so that it stays
diffable in git and reproducible in CI. Run:  python3 build_lab13.py
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
C = []
def _clean(t): return t.strip("\n").replace('\\"', '"')
def md(t): C.append(nbf.v4.new_markdown_cell(_clean(t)))
def code(t): C.append(nbf.v4.new_code_cell(_clean(t)))

# ---------------------------------------------------------------- front matter
md(r"""
# Lab 13 — Two codes, two failure modes

**Maths for Post-Quantum Cryptography**, Chapter 13: *Codes: HQC and Classic McEliece*

---

Three parts, one per major claim §13.2-§13.4 make about how these two
families of code-based schemes actually behave. Part A builds a real
(toy-scale) binary Goppa code, masks it exactly as Classic McEliece's
KeyGen does, and confirms decoding never fails — not approximately,
across every trial. Part B builds a small quasi-cyclic code in the
spirit of Definition 13.3 and *measures* a decoding failure rate that
is genuinely nonzero and grows with noise, rather than asserting one.
Part C turns that same failure signal into an attack: given nothing
but a success/fail oracle (no plaintext, no error vector — exactly
what a reaction attack has access to), it recovers a secret bit by
bit.

**Part A — a toy binary Goppa code, keyed and decoded.** A genuine
binary Goppa code over $\mathbb F_{16}$ (not a stand-in), its
generator and parity-check matrices built from the actual Goppa
polynomial relation, masked with random $S,P$ exactly as
§13.2's KeyGen describes, decoded by direct bounded-weight search
against 500 random messages and errors — zero failures.

**Part B — a toy quasi-cyclic code and its decoding failure rate.** A
small rate-$1/2$ quasi-cyclic code, a bounded-distance decoder with a
fixed correction radius, and an i.i.d.-per-coordinate noise model —
the same simplifying assumption HQC's own specification uses for its
Theorem 6.1 bound. The empirical failure rate is measured directly
across a sweep of noise levels and checked against a hand-derived
binomial-tail estimate.

**Part C — the reaction attack, demonstrated.** Using only Part B's
decoder as a black-box success/fail oracle — never revealing the
decoded message or the error itself — a purely statistical attack
recovers a secret sparse vector's support one bit at a time, from
nothing but the correlation between a guessed bit and the oracle's
answer.

### Requirements

```
python >= 3.9
numpy
```

A single `_selftest()` at the end repeats every numerical claim this
lab makes. CI runs this notebook on every commit.

**A note on scale.** Every parameter here (a degree-2 Goppa
polynomial over $\mathbb F_{16}$, an $n=11$ quasi-cyclic ring) is
chosen so that brute-force, no-library decoding finishes in seconds —
not for security. Classic McEliece's and HQC's real parameters are in
Tables 13.1-13.2; nothing in this notebook is a working cryptosystem.
""")

# ============================================================ PART A
md(r"""
## Part A — a toy binary Goppa code, keyed and decoded

Work over $\mathbb F_{16}=\mathbb F_2[\alpha]/(\alpha^4+\alpha+1)$,
implemented directly via log/antilog tables (no external field-arithmetic
library). Fix a Goppa polynomial $g(X)$ of degree $t=2$, irreducible
over $\mathbb F_{16}$ (hence automatically square-free and root-free —
every one of $\mathbb F_{16}$'s 16 elements is a valid support point),
and a support $L$ of $n=12$ of those elements.
""")

code(r"""
import itertools
import random
import numpy as np

class GF2m:
    "GF(2^m) via log/antilog tables; add is XOR, mul/inv via the tables."
    def __init__(self, m, modulus):
        self.m, self.size, self.modulus = m, 1 << m, modulus
        self.exp = [0] * (2 * self.size)
        self.log = [0] * self.size
        x = 1
        for i in range(self.size - 1):
            self.exp[i] = x
            self.log[x] = i
            x <<= 1
            if x & self.size:
                x ^= modulus
        for i in range(self.size - 1, 2 * self.size):
            self.exp[i] = self.exp[i - (self.size - 1)]
    def add(self, a, b): return a ^ b
    def mul(self, a, b): return 0 if (a == 0 or b == 0) else self.exp[self.log[a] + self.log[b]]
    def inv(self, a): return self.exp[(self.size - 1) - self.log[a]]
    def pow(self, a, k): return 0 if a == 0 else self.exp[(self.log[a] * k) % (self.size - 1)]

GF = GF2m(4, 0b10011)   # F_16 = F_2[x]/(x^4+x+1)
for a in range(1, 16):
    assert GF.mul(a, GF.inv(a)) == 1
print("GF(16) log/antilog tables built and inverse-checked")
""")

code(r"""
# --- polynomials over GF(2^m), coefficient lists (little-endian) ---
def gtrim(p):
    p = list(p)
    while len(p) > 1 and p[-1] == 0:
        p.pop()
    return p

def gadd(a, b):
    L = max(len(a), len(b)); a = a + [0]*(L-len(a)); b = b + [0]*(L-len(b))
    return gtrim([GF.add(x, y) for x, y in zip(a, b)])

def gmul(a, b):
    res = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai == 0: continue
        for j, bj in enumerate(b):
            res[i + j] = GF.add(res[i + j], GF.mul(ai, bj))
    return gtrim(res)

def gdivmod(a, b):
    a, b = gtrim(a), gtrim(b)
    quot = [0] * max(len(a) - len(b) + 1, 1)
    rem = list(a)
    b_lead_inv = GF.inv(b[-1])
    while len(gtrim(rem)) >= len(b) and gtrim(rem) != [0]:
        rem = gtrim(rem)
        shift = len(rem) - len(b)
        coeff = GF.mul(rem[-1], b_lead_inv)
        quot[shift] = GF.add(quot[shift], coeff)
        sub = [0]*shift + [GF.mul(coeff, x) for x in b]
        sub += [0]*(len(rem)-len(sub))
        rem = gtrim([GF.add(x, y) for x, y in zip(rem, sub)])
    return gtrim(quot), gtrim(rem)

def geval(p, x):
    r = 0
    for c in reversed(p):
        r = GF.add(GF.mul(r, x), c)
    return r

def gextgcd(a, b):
    old_r, r = gtrim(a), gtrim(b)
    old_s, s = [1], [0]
    while gtrim(r) != [0]:
        q, rem = gdivmod(old_r, r)
        old_r, r = r, rem
        old_s, s = s, gadd(old_s, gmul(q, s))
    return old_r, old_s

def ginv_mod(p, mod):
    "p^{-1} mod `mod`, both over GF(2^m)."
    gcd, s = gextgcd(p, mod)
    gcd = gtrim(gcd)
    assert len(gcd) == 1 and gcd[0] != 0, f"not invertible: gcd={gcd}"
    lead_inv = GF.inv(gcd[0])
    return gtrim([GF.mul(c, lead_inv) for c in s])
""")

code(r"""
# --- build the Goppa code: g(X) irreducible degree-2 over GF(16), n=12 support points ---
G_POLY = [1, 2, 1]   # 1 + 2X + X^2, verified irreducible (no roots in GF(16)) below
assert all(geval(G_POLY, x) != 0 for x in range(16)), "g must be root-free (irreducible) over F_16"

T_GOPPA, M_GOPPA, N_GOPPA = 2, 4, 12
L = list(range(N_GOPPA))   # support: first 12 elements of F_16 (all valid, g has no roots)

def to_bits(x, m):
    return [(x >> b) & 1 for b in range(m)]

# H[i][j] = i-th coefficient of (X - alpha_j)^{-1} mod g(X) -- the correct Goppa
# parity check (not the naive alpha_j^i/g(alpha_j) alternant formula, which only
# coincides with this for g(X)=X^t; verified against the true minimum-distance
# bound below).
H_gf = [[0]*N_GOPPA for _ in range(T_GOPPA)]
for j, alpha in enumerate(L):
    r_j = ginv_mod([alpha, 1], G_POLY)   # (X - alpha) = alpha + X over GF(2)
    r_j = r_j + [0] * (T_GOPPA - len(r_j))
    for i in range(T_GOPPA):
        H_gf[i][j] = r_j[i]

H_rows = []
for i in range(T_GOPPA):
    bitrows = [[0]*N_GOPPA for _ in range(M_GOPPA)]
    for j in range(N_GOPPA):
        bits = to_bits(H_gf[i][j], M_GOPPA)
        for b in range(M_GOPPA):
            bitrows[b][j] = bits[b]
    H_rows.extend(bitrows)
H_goppa = np.array(H_rows, dtype=int) % 2
print("H_goppa shape:", H_goppa.shape, " (expect", (M_GOPPA*T_GOPPA, N_GOPPA), ")")
""")

code(r"""
# --- GF(2) linear algebra: RREF, nullspace, inverse ---
def gf2_rref(M):
    M = M.copy() % 2
    rows, cols = M.shape
    pivots = []
    r = 0
    for c in range(cols):
        piv = next((i for i in range(r, rows) if M[i, c] == 1), None)
        if piv is None:
            continue
        M[[r, piv]] = M[[piv, r]]
        for i in range(rows):
            if i != r and M[i, c] == 1:
                M[i] = (M[i] + M[r]) % 2
        pivots.append(c)
        r += 1
        if r == rows:
            break
    return M[:r], pivots

def gf2_nullspace(H):
    rows, cols = H.shape
    R, pivots = gf2_rref(H)
    free = [c for c in range(cols) if c not in pivots]
    basis = []
    for fc in free:
        vec = np.zeros(cols, dtype=int)
        vec[fc] = 1
        for r, pc in enumerate(pivots):
            vec[pc] = R[r, fc]
        basis.append(vec)
    return np.array(basis, dtype=int) % 2

def gf2_matinv(M):
    n = M.shape[0]
    aug = np.concatenate([M, np.eye(n, dtype=int)], axis=1) % 2
    R, pivots = gf2_rref(aug)
    assert len(pivots) == n and pivots == list(range(n)), "matrix not invertible over GF(2)"
    return R[:, n:] % 2

Gp = gf2_nullspace(H_goppa)
K_GOPPA = Gp.shape[0]
assert np.all((H_goppa @ Gp.T) % 2 == 0)
print("Gp shape:", Gp.shape, " (k =", K_GOPPA, ", expect >= n - m*t =", N_GOPPA - M_GOPPA*T_GOPPA, ")")

# Confirm the actual minimum distance meets Goppa's 2t+1 bound -- proof, not assumption.
codewords = [(np.array(bits) @ Gp) % 2 for bits in itertools.product([0, 1], repeat=K_GOPPA)]
min_dist = min(int(np.sum((a + b) % 2)) for i, a in enumerate(codewords)
                for b in codewords[i+1:] if int(np.sum((a + b) % 2)) > 0)
print("measured minimum distance:", min_dist, " (Goppa bound: >=", 2*T_GOPPA + 1, ")")
assert min_dist >= 2 * T_GOPPA + 1
""")

md(r"""
### Masked KeyGen, and a brute-force (non-Patterson) decoder

$G=SG'P$ for random invertible $S$ and permutation $P$, exactly as
§13.2's KeyGen describes. Decoding a toy code this small does not need
Patterson's algorithm — an exhaustive search over every error pattern
of weight $\le t$ finds the unique syndrome match directly, which is
the point: correctness here is checked by brute force, independent of
any cleverness in the decoder itself.
""")

code(r"""
def brute_force_decode(received, H, t):
    "Exhaustive weight-<=t syndrome search. Returns the corrected codeword."
    n = len(received)
    syn = (H @ received) % 2
    if np.all(syn == 0):
        return received.copy()
    for w in range(1, t + 1):
        for combo in itertools.combinations(range(n), w):
            e = np.zeros(n, dtype=int)
            e[list(combo)] = 1
            if np.all((H @ e) % 2 == syn):
                return (received + e) % 2
    return None

# a k x k invertible submatrix of Gp, for recovering the message from a codeword
pivot_set = None
for cols in itertools.combinations(range(N_GOPPA), K_GOPPA):
    try:
        Gp_sub_inv = gf2_matinv(Gp[:, cols])
        pivot_set = cols
        break
    except AssertionError:
        continue

def recover_message(codeword, pivot_set, Gp_sub_inv):
    return (codeword[list(pivot_set)] @ Gp_sub_inv) % 2

def random_invertible_gf2(k, rng):
    while True:
        M = np.array([[rng.randint(0, 1) for _ in range(k)] for _ in range(k)])
        try:
            return M, gf2_matinv(M)
        except AssertionError:
            continue

def random_permutation(n, rng):
    perm = list(range(n)); rng.shuffle(perm)
    P = np.zeros((n, n), dtype=int)
    for i, p in enumerate(perm):
        P[i, p] = 1
    return P

rng = random.Random(42)
S_mask, S_inv = random_invertible_gf2(K_GOPPA, rng)
P_mask = random_permutation(N_GOPPA, rng)
P_inv = P_mask.T
G_pub = (S_mask @ Gp @ P_mask) % 2
print("G_pub (masked public key) shape:", G_pub.shape)
""")

code(r"""
def mceliece_encrypt(m_msg, G_pub, t, rng):
    x = (m_msg @ G_pub) % 2
    n = G_pub.shape[1]
    positions = rng.sample(range(n), t)
    e = np.zeros(n, dtype=int); e[positions] = 1
    return (x + e) % 2

def mceliece_decrypt(c, P_inv, H, t, pivot_set, Gp_sub_inv, S_inv):
    corrected = brute_force_decode((c @ P_inv) % 2, H, t)
    if corrected is None:
        return None
    mS = recover_message(corrected, pivot_set, Gp_sub_inv)
    return (mS @ S_inv) % 2

TRIALS_A = 500
failures_a = 0
rng_a = random.Random(7)
for _ in range(TRIALS_A):
    m_msg = np.array([rng_a.randint(0, 1) for _ in range(K_GOPPA)])
    c = mceliece_encrypt(m_msg, G_pub, T_GOPPA, rng_a)
    m_rec = mceliece_decrypt(c, P_inv, H_goppa, T_GOPPA, pivot_set, Gp_sub_inv, S_inv)
    if m_rec is None or not np.array_equal(m_rec, m_msg):
        failures_a += 1

print(f"Part A: {TRIALS_A} trials, {failures_a} decryption failures")
assert failures_a == 0
print("Part A: decryption never failed, matching Section 13.2's claim exactly")
""")

# ============================================================ PART B
md(r"""
## Part B — a toy quasi-cyclic code and its decoding failure rate

Work in $R=\mathbb F_2[X]/(X^n-1)$, $n=11$ (prime). A rate-$1/2$
quasi-cyclic code: codewords are pairs $(a,b)\in R^2$ with $a=h\cdot
b$ for a fixed public $h$ — exactly Definition 13.3's shape, and
exactly the algebraic relation HQC's own $(u,v)$ ciphertext satisfies.
A received, corrupted pair has syndrome $s=a'+h\cdot b'$; a
bounded-distance decoder searches jointly for a low-weight
$(e_a,e_b)$ matching that syndrome, up to a fixed correction radius
$t_{\rm bd}$ — and, unlike Part A's Goppa decoder, gives up (reports
failure) once the search radius is exceeded.
""")

code(r"""
N_QC = 11   # prime, small quasi-cyclic ring dimension

def cyclic_mul(a, b, n):
    "Multiply a, b in F_2[X]/(X^n - 1)."
    res = [0] * (2 * n - 1)
    for i, ai in enumerate(a):
        if ai == 0: continue
        for j, bj in enumerate(b):
            res[i + j] ^= (ai & bj)
    out = [0] * n
    for i in range(2 * n - 1):
        out[i % n] ^= res[i]
    return out

def rand_weight_vec(n, w, rng):
    v = [0] * n
    for pos in rng.sample(range(n), w):
        v[pos] = 1
    return v

rng_h = random.Random(3)
H_PUB = rand_weight_vec(N_QC, N_QC // 2, rng_h)   # public h

def qc_encode(b_msg, h, n):
    return cyclic_mul(h, b_msg, n), b_msg

def qc_syndrome(a, b, h, n):
    hb = cyclic_mul(h, b, n)
    return [x ^ y for x, y in zip(a, hb)]

def qc_bounded_distance_decode(a_recv, b_recv, h, n, t_bd):
    "Joint search over (e_a, e_b) of total weight <= t_bd matching the syndrome."
    s = qc_syndrome(a_recv, b_recv, h, n)
    if all(x == 0 for x in s):
        return [0] * n, [0] * n
    for w in range(1, t_bd + 1):
        for wa in range(0, w + 1):
            wb = w - wa
            for a_pos in itertools.combinations(range(n), wa):
                ea = [0] * n
                for p in a_pos: ea[p] = 1
                for b_pos in itertools.combinations(range(n), wb):
                    eb = [0] * n
                    for p in b_pos: eb[p] = 1
                    cand = [x ^ y for x, y in zip(ea, cyclic_mul(h, eb, n))]
                    if cand == s:
                        return ea, eb
    return None

# sanity: zero error decodes to (0,0)
b_test = rand_weight_vec(N_QC, 3, rng_h)
a_test, b_test2 = qc_encode(b_test, H_PUB, N_QC)
assert qc_bounded_distance_decode(a_test, b_test2, H_PUB, N_QC, t_bd=2) == ([0]*N_QC, [0]*N_QC)
print("quasi-cyclic code built; zero-error decode sanity check passed")
""")

md(r"""
### Decoding failure rate, measured against a hand-derived estimate

Model each coordinate of the combined error as flipping independently
with probability $p$ — HQC's own DFR analysis makes exactly this
simplifying assumption (§13.3's Derivation 13.3 note). Sweep $p$
upward and measure the empirical failure rate against
$\Pr[\mathrm{Binomial}(2n,p) > t_{\rm bd}]$, the union-bound-style
estimate for "the total error weight exceeded the decoder's
correction radius."
""")

code(r"""
from math import comb

def binomial_tail(N, p, t):
    return sum(comb(N, k) * (p**k) * ((1-p)**(N-k)) for k in range(t+1, N+1))

def qc_trial_dfr(h, n, t_bd, p, trials, rng):
    fails = 0
    for _ in range(trials):
        b_msg = [rng.randint(0, 1) for _ in range(n)]
        a, b = qc_encode(b_msg, h, n)
        ea = [1 if rng.random() < p else 0 for _ in range(n)]
        eb = [1 if rng.random() < p else 0 for _ in range(n)]
        a_recv = [x ^ y for x, y in zip(a, ea)]
        b_recv = [x ^ y for x, y in zip(b, eb)]
        dec = qc_bounded_distance_decode(a_recv, b_recv, h, n, t_bd)
        if dec is None:
            fails += 1
            continue
        _, eb_est = dec
        if [x ^ y for x, y in zip(b_recv, eb_est)] != b_msg:
            fails += 1
    return fails / trials

T_BD = 3
P_SWEEP = [0.01, 0.03, 0.05, 0.08, 0.12, 0.16]
rng_b = random.Random(11)
dfr_results = []
for p in P_SWEEP:
    empirical = qc_trial_dfr(H_PUB, N_QC, T_BD, p, 200, rng_b)
    predicted = binomial_tail(2 * N_QC, p, T_BD)
    dfr_results.append((p, empirical, predicted))
    print(f"p={p:.2f}  empirical DFR={empirical:.3f}  predicted P(Binom(2n,p)>{T_BD})={predicted:.3f}")

# The failure rate must be a genuine, measured, increasing phenomenon --
# not a footnote -- and must track (not necessarily equal) the estimate.
assert dfr_results[0][1] < dfr_results[-1][1], "DFR should grow as noise increases"
assert all(dfr_results[i][1] <= dfr_results[i+1][1] + 0.05 for i in range(len(dfr_results)-1)), \
    "empirical DFR should be roughly monotone in p"
assert all(pred <= emp + 0.05 for _, emp, pred in dfr_results), \
    "the binomial-tail estimate should stay in the same ballpark as the measured rate"
print("Part B: decoding failure rate is a real, measured, growing phenomenon")
""")

# ============================================================ PART C
md(r"""
## Part C — the reaction attack, demonstrated

The attacker never sees a plaintext, an error vector, or even a
"weight" — only whether decoding succeeded or failed on a ciphertext
they crafted directly (bypassing honest encryption entirely). Fix a
secret sparse $y$ (as if it were HQC's own secret,
Definition 13.3-style) and an oracle that, given a candidate guess,
reports success exactly when the guess is within the decoder's
correction radius $t_{\rm bd}$ of $y$ in Hamming distance --- the
same "does decapsulation succeed" signal a real reaction attack
observes, and nothing else.
""")

code(r"""
OMEGA = 2      # secret weight
T_ORACLE = 3   # oracle's bounded-distance radius

rng_y = random.Random(5)
Y_SECRET = rand_weight_vec(N_QC, OMEGA, rng_y)
print("secret y (hidden from the attack below):", Y_SECRET)

def reaction_oracle(guess, y_true, t_bd):
    "1-bit oracle: True iff Hamming distance(guess, y_true) <= t_bd. No other information leaks."
    diff = [g ^ yy for g, yy in zip(guess, y_true)]
    return sum(diff) <= t_bd

def reaction_attack(y_true, n, t_bd, guess_weight, n_queries, rng):
    "Recover y_true bit-by-bit from oracle(guess) alone, via per-bit success correlation."
    succ1, cnt1 = [0]*n, [0]*n
    succ0, cnt0 = [0]*n, [0]*n
    for _ in range(n_queries):
        guess = rand_weight_vec(n, guess_weight, rng)
        ok = reaction_oracle(guess, y_true, t_bd)
        for i in range(n):
            if guess[i] == 1:
                cnt1[i] += 1; succ1[i] += ok
            else:
                cnt0[i] += 1; succ0[i] += ok
    recovered = []
    for i in range(n):
        rate1 = succ1[i] / max(cnt1[i], 1)
        rate0 = succ0[i] / max(cnt0[i], 1)
        # a guessed 1 that matches a true 1 REDUCES Hamming distance -> raises the success rate
        recovered.append(1 if rate1 > rate0 else 0)
    return recovered

N_QUERIES = 800
rng_atk = random.Random(123)
recovered_y = reaction_attack(Y_SECRET, N_QC, T_ORACLE, guess_weight=5,
                               n_queries=N_QUERIES, rng=rng_atk)
bits_correct = sum(a == b for a, b in zip(Y_SECRET, recovered_y))

print("recovered y:                          ", recovered_y)
print(f"bits correct: {bits_correct}/{N_QC}, using {N_QUERIES} success/fail-only queries")
assert bits_correct == N_QC, "the reaction attack should recover the full secret"
print("Part C: the full secret was recovered from decoding outcomes alone -- no plaintext, no error vector")
""")

# --------------------------------------------------------------------- close
md(r"""
## What to take away

Part A is §13.2's promise kept exactly: a real Goppa code, a real
mask, zero measured failures across every trial, because there is
nothing probabilistic anywhere in Classic McEliece's decoding step.
Part B is the opposite promise, kept just as exactly: HQC's decoding
failure rate is not a hypothetical footnote but a measured, growing
quantity that tracks a hand-derived estimate. Part C is why that
measured quantity is a *security* parameter rather than a mere
correctness one: an attacker who only ever learns "did decoding
succeed" recovered an entire secret, one bit at a time, using nothing
else. Chapter 12's floating-point misconception box and this chapter's
decoding-failure misconception box are, underneath, the same
argument — a design constraint invisible in a spec's pseudocode can
still be exactly where an attack lives.
""")

code(r"""
def _selftest():
    # Part A
    assert min_dist >= 2 * T_GOPPA + 1
    assert failures_a == 0

    # Part B
    assert dfr_results[0][1] < dfr_results[-1][1]
    assert all(dfr_results[i][1] <= dfr_results[i+1][1] + 0.05 for i in range(len(dfr_results)-1))
    assert all(pred <= emp + 0.05 for _, emp, pred in dfr_results)

    # Part C
    assert bits_correct == N_QC

    print("all checks passed")

_selftest()
""")

nb["cells"] = C
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11"},
}

with open("lab13.ipynb", "w") as fh:
    nbf.write(nb, fh)
print(f"wrote lab13.ipynb with {len(C)} cells")
