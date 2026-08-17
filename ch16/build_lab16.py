"""Build ch16/lab16.ipynb for 'Maths for Post-Quantum Cryptography'.

The notebook is generated from source rather than hand-edited so that it stays
diffable in git and reproducible in CI. Run:  python3 build_lab16.py
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
C = []
def _clean(t): return t.strip("\n").replace('\\"', '"')
def md(t): C.append(nbf.v4.new_markdown_cell(_clean(t)))
def code(t): C.append(nbf.v4.new_code_cell(_clean(t)))

# ---------------------------------------------------------------- front matter
md(r"""
# Lab 16 — A toy MPC-in-the-head signature, and a toy oil-vinegar trapdoor

**Maths for Post-Quantum Cryptography**, Chapter 16: *The On-Ramp*

---

Two parts, independent of each other, both built entirely from the Python
standard library. Part A implements §16.3's MPC-in-the-head construction —
the paradigm behind FAEST, MQOM and SDitH — from scratch, for a toy quadratic
relation small enough to inspect by hand: real secret sharing, a real
(Beaver-triple-style) multiplication protocol for the quadratic term, a real
Fiat–Shamir challenge, and an empirical check that a prover without a valid
witness is caught at exactly the rate the derivation predicts. Part B
implements §16.4's oil-and-vinegar trapdoor — the construction behind UOV,
MAYO, QR-UOV and SNOVA — end to end: key generation, signing via the
vinegar-then-Gaussian-elimination trick, verification against the public
key alone, and a direct timing comparison against a forger who does not
know the oil/vinegar split and has to fall back on brute-force search over
the same MQ problem Chapter 16's Definition 16.1 states.

### Requirements

```
python >= 3.9
```

No third-party libraries anywhere in this notebook. All finite-field
arithmetic — including the small linear-algebra routines Part B needs for
key generation and signing — is implemented directly with the standard
library, over prime fields small enough that Python's built-in arbitrary-
precision integers need no help.

### A note on scope

Both parts are deliberately tiny compared to a real deployment. Part A uses
$N=3$ virtual parties, matching Derivation 16.2's exposition exactly, where
real FAEST/MQOM/SDitH use $N$ in the dozens to low hundreds
(Table 16.2); the point is to verify the *soundness formula*, not to
reproduce production parameter choices. Part B uses a handful of oil and
vinegar variables over a small prime field, not UOV's actual
Table 16.3 parameters; the point is to verify the *asymmetry* between
trapdoor-based signing and brute-force forgery, not to reproduce real-world
attack costs. Nothing in this notebook should be read as a security
estimate for any of the eight active Round 3 schemes.
""")

# ============================================================== PART A: MPCitH
md(r"""
## Part A — MPC-in-the-head for a toy quadratic relation

The relation being proved: given public $(a, b, y)$, prove knowledge of a
secret $x$ with $f(x) = a x^2 + b x \equiv y \pmod q$ — exactly
Derivation 16.2's running example. The construction below follows
Derivation 16.2 precisely: additive secret sharing of $x$ across $N=3$
virtual parties, a Beaver-triple-style protocol for the one genuinely
nonlinear step ($x^2$), commitments to each party's full view, a
Fiat–Shamir challenge selecting which single party stays hidden, and a
verifier that recomputes the opened parties' outputs from their views.
""")

code(r"""
import hashlib, math, random

Q = 101  # small prime field, matches Derivation 16.2's worked sharing example

def within_4sigma(empirical, predicted, n):
    \"\"\"Proper statistical tolerance rather than an eyeballed constant: the
    sample mean of n Bernoulli(p) draws has standard deviation
    sqrt(p(1-p)/n), so 4 sigma is a ~99.99% two-sided interval. This is a
    real test -- it fails if a measured rate genuinely departs from its
    predicted value, and it does NOT quietly absorb a systematic bias the
    way a hand-picked flat tolerance would.\"\"\"
    sigma = math.sqrt(predicted * (1 - predicted) / n)
    return abs(empirical - predicted) < 4 * sigma, 4 * sigma

def inv_mod(x, q=Q):
    x %= q
    if x == 0:
        raise ZeroDivisionError("no inverse of 0")
    return pow(x, q - 2, q)  # Fermat's little theorem; q is prime

def share_n(x, n, rng, q=Q):
    \"\"\"Split x into n additive shares mod q (n=3 in the main derivation;
    Exercise 16.11 reuses this with n=5).\"\"\"
    shares = [rng.randrange(q) for _ in range(n - 1)]
    shares.append((x - sum(shares)) % q)
    return shares

def share3(x, rng, q=Q):
    return share_n(x, 3, rng, q)

def commit(view):
    \"\"\"Toy commitment: SHA-256 of the view's values. A real scheme commits
    to a full transcript including protocol messages; here the view alone
    (x_i, u_i, w_i) is everything the verifier needs to recheck a party.\"\"\"
    m = ",".join(str(v) for v in view)
    return hashlib.sha256(m.encode()).hexdigest()
""")

md(r"""
### The prover: one Beaver-style multiplication triple, three views, three
### output shares

To prove $f(x) = a x^2 + b x = y$, the only nonlinear step is $x^2$. The
prover picks a single random mask $u$, its square $w = u^2 \bmod q$, shares
both across the three parties, and reveals the single public value
$d = x - u \bmod q$ — a one-time pad of $x$ by a value $u$ that is exactly
as unknown as $x$ itself, so $d$ leaks nothing on its own. Writing
$x = u + d$:
$$x^2 = u^2 + 2du + d^2 = w + 2du + d^2,$$
and since $w$ and $u$ are both additively shared as $w = w_0+w_1+w_2$,
$u = u_0+u_1+u_2$, each party $i$ can compute a local share of $x^2$ using
only its own shares and the public $d$:
$$z_i = w_i + 2 d u_i + [\,i=0\,] \, d^2 \pmod q,$$
(the $d^2$ term added to exactly one party, here party 0, so it is counted
once). Summing over $i$ recovers $x^2$ exactly. Each party's output share
is then $\text{out}_i = a z_i + b x_i \bmod q$, and $\sum_i \text{out}_i =
a x^2 + b x = f(x)$ by construction — always, honestly computed, regardless
of which party is later hidden.
""")

code(r"""
def prover_round(a, b, x, rng, q=Q, n=3):
    \"\"\"Run one full MPCitH round 'in the head' with n virtual parties
    (n=3 matches Derivation 16.2 exactly; Exercise 16.11 reuses this with
    n=5). Returns (views, outs, d) where views are the private per-party
    data (x_i, u_i, w_i), outs are the always-public broadcast output
    shares, and d is the always-public mask. The per-party formula for
    z_i does not depend on n at all -- only the sharing fan-out and the
    Fiat-Shamir modulus (below) change with n.\"\"\"
    xs = share_n(x, n, rng, q)
    u = rng.randrange(q)
    w = (u * u) % q
    us = share_n(u, n, rng, q)
    ws = share_n(w, n, rng, q)
    d = (x - u) % q

    zs, outs, views = [], [], []
    for i in range(n):
        zi = (ws[i] + 2 * d * us[i] + (d * d if i == 0 else 0)) % q
        outi = (a * zi + b * xs[i]) % q
        zs.append(zi)
        outs.append(outi)
        views.append((xs[i], us[i], ws[i]))
    return views, outs, d

def recompute_out(view, a, b, d, party_index, q=Q):
    \"\"\"What the verifier recomputes for an opened party's view.\"\"\"
    xi, ui, wi = view
    zi = (wi + 2 * d * ui + (d * d if party_index == 0 else 0)) % q
    return (a * zi + b * xi) % q
""")

md(r"""
### Non-interactivity: Fiat–Shamir picks the one hidden party

Exactly as in Chapter 10's transform, and exactly as Derivation 16.2
describes: the prover commits to all three views, hashes the commitments
together with the public $(d, \text{outs})$, and the hash output — reduced
mod 3 — determines which single party stays hidden. The verifier redoes
this same hash to check the prover did not get to choose the challenge
after the fact.
""")

code(r"""
def fiat_shamir_hide(commitments, d, outs, q=Q, n=3):
    m = ",".join(commitments) + f"|{d}|" + ",".join(str(o) for o in outs)
    h = hashlib.sha256(m.encode()).hexdigest()
    return int(h, 16) % n

def run_round(a, b, x, rng, q=Q, n=3):
    \"\"\"One full round: prove, challenge, open, verify. Returns True iff
    the round passes.\"\"\"
    views, outs, d = prover_round(a, b, x, rng, q, n)
    commitments = [commit(v) for v in views]
    hidden = fiat_shamir_hide(commitments, d, outs, q, n)

    y_check = sum(outs) % q
    ok = True
    for i in range(n):
        if i == hidden:
            continue
        recomputed = recompute_out(views[i], a, b, d, i, q)
        if recomputed != outs[i]:
            ok = False
        if commit(views[i]) != commitments[i]:
            ok = False
    return ok, y_check
""")

md(r"""
### Completeness: an honest prover always passes

Across many independent trials, with a genuine witness $x$, every round
must verify and the broadcast output shares must sum to the true $y$.
""")

code(r"""
rng = random.Random(2026)

def keygen(rng, q=Q):
    a = rng.randrange(1, q)
    b = rng.randrange(1, q)
    x = rng.randrange(q)
    y = (a * x * x + b * x) % q
    return a, b, x, y

N_COMPLETENESS_TRIALS = 400
completeness_failures = 0
for _ in range(N_COMPLETENESS_TRIALS):
    a, b, x, y = keygen(rng)
    ok, y_check = run_round(a, b, x, rng)
    if not (ok and y_check == y):
        completeness_failures += 1

print(f"completeness: {N_COMPLETENESS_TRIALS - completeness_failures}/{N_COMPLETENESS_TRIALS} rounds passed")
assert completeness_failures == 0
""")

md(r"""
### Soundness: a prover without a valid witness is caught at exactly the
### predicted rate

The optimal cheat: corrupt exactly one party's data so that the *broadcast*
output shares still sum to the target $y$ (so that public check always
passes) while that one party's *view* no longer matches its own broadcast
output. Concretely: run the honest protocol on a **wrong** guess
$x_{\text{guess}} \ne x$ (so the shares are generated exactly as an honest
prover would, but for the wrong secret), producing outputs that sum to
$f(x_{\text{guess}}) \ne y$; then patch the last party's broadcast output
by the difference so the sum equals $y$ exactly. This cheat evades
detection if and only if the Fiat–Shamir challenge happens to hide that
one corrupted party — probability exactly $1/N = 1/3$ per round, matching
Derivation 16.2.

**One subtlety the toy scale forces us to handle honestly.** $f(x)=ax^2+bx$
is a *quadratic*, so for almost every target $y$ there are **two** values
of $x$ with $f(x)=y$, not one. Over the tiny field $q=101$ used here, a
"cheating" prover drawing $x_{\text{guess}}$ at random therefore lands on
the genuine second root — and so is not cheating at all, but is an honest
prover with a different valid witness — with probability roughly $1/q
\approx 1\%$. At $\tau=4$ that 1% swamps the true prediction
$(1/3)^4 \approx 1.2\%$ and would make the measured rate look like a
soundness failure when it is nothing of the kind. The fix is to
require the guess to be a genuine non-witness, which the cell below does
explicitly. (This is not an artifact of the construction — it is an
artifact of $q=101$ being small enough to inspect by hand. A real scheme's
witness space is far too large for a random guess to hit a valid witness
at any measurable rate.)
""")

code(r"""
def cheat_round(a, b, x_guess, y_target, rng, q=Q, n=3, corrupt_party=None):
    if corrupt_party is None:
        corrupt_party = n - 1
    views, outs, d = prover_round(a, b, x_guess, rng, q, n)
    achieved = sum(outs) % q
    patch = (y_target - achieved) % q
    outs = list(outs)
    outs[corrupt_party] = (outs[corrupt_party] + patch) % q  # broadcast now sums to y_target

    commitments = [commit(v) for v in views]
    hidden = fiat_shamir_hide(commitments, d, outs, q, n)

    y_check = sum(outs) % q
    assert y_check == y_target  # the public sum check always passes for this cheat

    caught = False
    for i in range(n):
        if i == hidden:
            continue
        recomputed = recompute_out(views[i], a, b, d, i, q)
        if recomputed != outs[i]:
            caught = True
    return caught, hidden

def draw_non_witness(a, b, y, rng, q=Q):
    \"\"\"Draw x_guess with f(x_guess) != y -- i.e. a genuine non-witness, not
    merely a value different from the signer's own x. Necessary because
    f is quadratic and so generally has a *second* root for the same y
    (see the note above); a prover holding that second root is honest,
    not cheating, and would skew the measured soundness rate by ~1/q.\"\"\"
    while True:
        xg = rng.randrange(q)
        if (a * xg * xg + b * xg) % q != y:
            return xg

def soundness_experiment(n_trials, rng, q=Q, n=3):
    caught_count = 0
    evaded_count = 0
    for _ in range(n_trials):
        a, b, x_true, y = keygen(rng, q)
        x_guess = draw_non_witness(a, b, y, rng, q)
        caught, hidden = cheat_round(a, b, x_guess, y, rng, q, n)
        if caught:
            caught_count += 1
        else:
            evaded_count += 1
    return caught_count, evaded_count

N_SOUNDNESS_TRIALS = 6000
caught, evaded = soundness_experiment(N_SOUNDNESS_TRIALS, rng)
observed_catch_rate = caught / N_SOUNDNESS_TRIALS
predicted_catch_rate = 2 / 3  # (N-1)/N for N=3
ok3, band3 = within_4sigma(observed_catch_rate, predicted_catch_rate, N_SOUNDNESS_TRIALS)
print(f"observed single-round catch rate: {observed_catch_rate:.4f}  (predicted {predicted_catch_rate:.4f}, 4-sigma band {band3:.4f}) -> {'OK' if ok3 else 'FAIL'}")
assert ok3, (observed_catch_rate, predicted_catch_rate)
""")

md(r"""
### Repeated rounds: forgery probability falls to $(1/N)^\tau$

A prover who wants to evade detection across $\tau$ independent rounds must
get lucky in *every* round: probability $(1/N)^\tau$. The cell below
measures this directly for several values of $\tau$ by running the
single-round cheat repeatedly and checking how often it evades detection
in all $\tau$ rounds simultaneously, then compares the empirical rate to
the closed-form prediction.
""")

code(r"""
def multi_round_forgery_trial(tau, rng, q=Q, n=3):
    \"\"\"One attempt at forging across tau independent rounds. Returns True
    iff the prover evades detection in every single round.\"\"\"
    a, b, x_true, y = keygen(rng, q)
    x_guess = draw_non_witness(a, b, y, rng, q)
    for _ in range(tau):
        caught, _ = cheat_round(a, b, x_guess, y, rng, q, n)
        if caught:
            return False
    return True

results = {}
N_FORGERY_TRIALS = 4000
for tau in (1, 2, 4):
    successes = sum(multi_round_forgery_trial(tau, rng) for _ in range(N_FORGERY_TRIALS))
    empirical = successes / N_FORGERY_TRIALS
    predicted = (1 / 3) ** tau
    results[tau] = (empirical, predicted)
    print(f"tau={tau}: empirical forgery rate={empirical:.4f}  predicted (1/N)^tau={predicted:.4f}")

for tau, (empirical, predicted) in results.items():
    ok, band = within_4sigma(empirical, predicted, N_FORGERY_TRIALS)
    print(f"  tau={tau}: |{empirical:.4f} - {predicted:.4f}| = {abs(empirical-predicted):.4f}  (4-sigma band {band:.4f}) -> {'OK' if ok else 'FAIL'}")
    assert ok, (tau, empirical, predicted)
print("all tau values within 4 sigma of the predicted (1/N)^tau")
""")

md(r"""
### Exercise 16.11: the same experiment at $N=5$

Nothing in the per-party arithmetic changes when $N$ grows — only the
sharing fan-out and the Fiat–Shamir challenge's modulus. Every function
above already takes `n` as a parameter, so the $N=5$ case is the same code
with one argument changed. The prediction is the same formula with a
different base: a cheating prover evades detection with probability
$1/5$ per round instead of $1/3$, so is caught with probability $4/5$, and
forges across $\tau$ rounds with probability $(1/5)^\tau$.
""")

code(r"""
N5 = 5
rng5 = random.Random(31415)

# Completeness must still hold exactly at N=5.
n5_completeness_failures = 0
for _ in range(300):
    a, b, x, y = keygen(rng5)
    ok, y_check = run_round(a, b, x, rng5, Q, N5)
    if not (ok and y_check == y):
        n5_completeness_failures += 1
print(f"N=5 completeness: {300 - n5_completeness_failures}/300 rounds passed")
assert n5_completeness_failures == 0

caught5, evaded5 = soundness_experiment(N_SOUNDNESS_TRIALS, rng5, Q, N5)
observed_catch_rate_n5 = caught5 / N_SOUNDNESS_TRIALS
predicted_catch_rate_n5 = 1 - 1 / N5  # 4/5
print(f"N=5 observed single-round catch rate: {observed_catch_rate_n5:.4f}  (predicted {predicted_catch_rate_n5:.4f})")
ok5, band5 = within_4sigma(observed_catch_rate_n5, predicted_catch_rate_n5, N_SOUNDNESS_TRIALS)
assert ok5, (observed_catch_rate_n5, predicted_catch_rate_n5, band5)

results_n5 = {}
for tau in (1, 2, 4):
    successes = sum(multi_round_forgery_trial(tau, rng5, Q, N5) for _ in range(N_FORGERY_TRIALS))
    empirical = successes / N_FORGERY_TRIALS
    predicted = (1 / N5) ** tau
    results_n5[tau] = (empirical, predicted)
    ok, band = within_4sigma(empirical, predicted, N_FORGERY_TRIALS)
    print(f"N=5, tau={tau}: empirical={empirical:.4f}  predicted={predicted:.4f}  (4-sigma band {band:.4f}) -> {'OK' if ok else 'FAIL'}")
    assert ok, (tau, empirical, predicted)

# At fixed tau, going from N=3 to N=5 must cut the forgery rate.
for tau in (1, 2, 4):
    assert results_n5[tau][0] < results[tau][0], tau
print()
print("At every tau, N=5 forges strictly less often than N=3 -- which is why real")
print("MPCitH schemes use N in the dozens to low hundreds, not 3: each extra party")
print("multiplies the per-round evasion probability down by another factor of 1/N,")
print("so a larger N buys the same soundness with far fewer repeated rounds tau --")
print("and tau is what drives signature size (Table 16.2).")
""")

# ========================================================= PART B: OIL/VINEGAR
md(r"""
## Part B — a toy Unbalanced Oil and Vinegar trapdoor

Section 16.4's construction, in full: split $n = v + o$ variables into $v$
vinegar and $o$ oil variables, build a central quadratic map $F$ with no
oil-oil cross terms, hide it behind a random invertible linear map $T$
(public key $P = F \circ T$), and use the fact that fixing the vinegar
variables makes $F$ *linear* in the oil variables to sign efficiently.
Everything here — field arithmetic, matrix inversion, Gaussian elimination
— is implemented directly; no linear-algebra library is used.
""")

code(r"""
def mat_mult(X, Y, q=Q):
    n, k, m = len(X), len(Y), len(Y[0])
    return [[sum(X[i][t] * Y[t][j] for t in range(k)) % q for j in range(m)] for i in range(n)]

def transpose(X):
    return [list(row) for row in zip(*X)]

def mat_vec(M, v, q=Q):
    return [sum(M[i][j] * v[j] for j in range(len(v))) % q for i in range(len(M))]

def random_invertible_matrix(n, rng, q=Q, max_tries=200):
    for _ in range(max_tries):
        M = [[rng.randrange(q) for _ in range(n)] for _ in range(n)]
        Minv = mat_inverse(M, q)
        if Minv is not None:
            return M, Minv
    raise RuntimeError("failed to find an invertible matrix -- unlucky RNG")

def mat_inverse(M, q=Q):
    \"\"\"Gauss-Jordan elimination mod prime q. Returns None if singular.\"\"\"
    n = len(M)
    A = [row[:] + [1 if i == j else 0 for j in range(n)] for i, row in enumerate(M)]
    for col in range(n):
        pivot = None
        for row in range(col, n):
            if A[row][col] % q != 0:
                pivot = row
                break
        if pivot is None:
            return None
        A[col], A[pivot] = A[pivot], A[col]
        inv_p = inv_mod(A[col][col], q)
        A[col] = [(v * inv_p) % q for v in A[col]]
        for row in range(n):
            if row == col:
                continue
            factor = A[row][col]
            if factor:
                A[row] = [(A[row][j] - factor * A[col][j]) % q for j in range(2 * n)]
    return [row[n:] for row in A]

def gauss_solve(M, b, q=Q):
    \"\"\"Solve M x = b mod q for square M. Returns None if singular.\"\"\"
    n = len(M)
    A = [M[i][:] + [b[i]] for i in range(n)]
    for col in range(n):
        pivot = None
        for row in range(col, n):
            if A[row][col] % q != 0:
                pivot = row
                break
        if pivot is None:
            return None
        A[col], A[pivot] = A[pivot], A[col]
        inv_p = inv_mod(A[col][col], q)
        A[col] = [(v * inv_p) % q for v in A[col]]
        for row in range(n):
            if row == col:
                continue
            factor = A[row][col]
            if factor:
                A[row] = [(A[row][j] - factor * A[col][j]) % q for j in range(n + 1)]
    return [A[i][n] for i in range(n)]
""")

md(r"""
### Key generation, signing, and verification

The central map's $k$-th component is stored as an upper-triangular matrix
$A_k$ with $A_k[i][j] = 0$ whenever $i \ge v$ (an oil row) — since $i \le j$
is enforced by only ever filling the upper triangle, this automatically
forces every oil-oil pair to coefficient zero, which is Section 16.4's
entire oil-vinegar rule stated as a single indexing constraint. The public
key is the *expanded* quadratic form $B_k = T^\top A_k T \bmod q$ for each
$k$ — computed once, at key generation, so that verification never touches
the secret $T$ or $A$ again.
""")

code(r"""
def central_map(v, o, rng, q=Q):
    \"\"\"m = o upper-triangular matrices A_k, oil-oil entries forced to 0
    because row i >= v never gets any nonzero entries filled in.\"\"\"
    n = v + o
    A_list = []
    for _ in range(o):
        A = [[0] * n for _ in range(n)]
        for i in range(v):          # only vinegar rows are ever filled
            for j in range(i, n):   # i <= j, so oil-oil (i>=v,j>=v) never reached
                A[i][j] = rng.randrange(q)
        A_list.append(A)
    return A_list

def eval_quad_upper(A, x, q=Q):
    n = len(x)
    total = 0
    for i in range(n):
        if x[i] == 0:
            continue
        for j in range(i, n):
            if A[i][j]:
                total += A[i][j] * x[i] * x[j]
    return total % q

def eval_quad_full(B, x, q=Q):
    n = len(x)
    total = 0
    for i in range(n):
        if x[i] == 0:
            continue
        for j in range(n):
            if B[i][j]:
                total += B[i][j] * x[i] * x[j]
    return total % q

def uov_keygen(v, o, rng, q=Q):
    n = v + o
    A_list = central_map(v, o, rng, q)
    T, Tinv = random_invertible_matrix(n, rng, q)
    Tt = transpose(T)
    B_list = [mat_mult(mat_mult(Tt, A, q), T, q) for A in A_list]  # public key
    return {"v": v, "o": o, "n": n, "q": q, "A": A_list, "T": T, "Tinv": Tinv, "B": B_list}

def uov_sign(sk, y, rng, max_tries=200):
    v, o, n, q = sk["v"], sk["o"], sk["n"], sk["q"]
    for attempt in range(max_tries):
        vinegar = [rng.randrange(q) for _ in range(v)]
        M = [[0] * o for _ in range(o)]
        rhs = [0] * o
        for k in range(o):
            A = sk["A"][k]
            const = 0
            row = [0] * o
            for i in range(v):
                for j in range(i, n):
                    c = A[i][j]
                    if not c:
                        continue
                    if j < v:
                        const += c * vinegar[i] * vinegar[j]
                    else:
                        row[j - v] = (row[j - v] + c * vinegar[i]) % q
            M[k] = row
            rhs[k] = (y[k] - const) % q
        oil = gauss_solve(M, rhs, q)
        if oil is not None:
            x = vinegar + oil
            s = mat_vec(sk["Tinv"], x, q)
            return s, attempt + 1
    return None, max_tries

def uov_verify(pk_B, s, y, q=Q):
    return all(eval_quad_full(B, s, q) == yk for B, yk in zip(pk_B, y))
""")

md(r"""
### Sign, verify, and confirm the trapdoor actually works
""")

code(r"""
rng2 = random.Random(7)
V, O = 6, 4
sk = uov_keygen(V, O, rng2)
target_y = [rng2.randrange(Q) for _ in range(O)]
sig, tries_used = uov_sign(sk, target_y, rng2)
assert sig is not None
verified = uov_verify(sk["B"], sig, target_y)
print(f"UOV toy instance: v={V}, o={O}, n={V+O}, field size q={Q}")
print(f"signature found after {tries_used} vinegar attempt(s); verifies: {verified}")
assert verified

# Tampering with the signature must break verification.
bad_sig = sig[:]
bad_sig[0] = (bad_sig[0] + 1) % Q
assert not uov_verify(sk["B"], bad_sig, target_y)
print("a single-coordinate-tampered signature correctly fails verification")
""")

md(r"""
### The trapdoor's value: legitimate signing against brute-force forgery

A legitimate signer solves one $o \times o$ linear system. A forger without
the oil/vinegar split sees only the public $B_k$ matrices and has no
structure to exploit — the best available strategy is to search the full
$n$-variable space, exactly Definition 16.1's worst-case-NP-hard,
average-case-conjectured MQ problem. The cell below times both sides
directly, over a small sweep of sizes, using a smaller field
($q=7$) so that brute-force search is small enough to actually finish in
this notebook while still growing visibly with $o$.
""")

code(r"""
import time

def uov_keygen_q(v, o, rng, q):
    n = v + o
    A_list = central_map(v, o, rng, q)
    T, Tinv = random_invertible_matrix(n, rng, q)
    Tt = transpose(T)
    B_list = [mat_mult(mat_mult(Tt, A, q), T, q) for A in A_list]
    return {"v": v, "o": o, "n": n, "q": q, "A": A_list, "T": T, "Tinv": Tinv, "B": B_list}

def uov_sign_q(sk, y, rng, q, max_tries=200):
    v, o, n = sk["v"], sk["o"], sk["n"]
    for attempt in range(max_tries):
        vinegar = [rng.randrange(q) for _ in range(v)]
        M = [[0] * o for _ in range(o)]
        rhs = [0] * o
        for k in range(o):
            A = sk["A"][k]
            const = 0
            row = [0] * o
            for i in range(v):
                for j in range(i, n):
                    c = A[i][j]
                    if not c:
                        continue
                    if j < v:
                        const += c * vinegar[i] * vinegar[j]
                    else:
                        row[j - v] = (row[j - v] + c * vinegar[i]) % q
            M[k] = row
            rhs[k] = (y[k] - const) % q
        oil = gauss_solve(M, rhs, q)
        if oil is not None:
            x = vinegar + oil
            s = mat_vec(sk["Tinv"], x, q)
            return s, attempt + 1
    return None, max_tries

def brute_force_forge(pk_B, y, q, rng, max_trials):
    \"\"\"Uniform random search over the full n-variable space -- the naive
    baseline for the same MQ problem MQOM's security rests on directly.\"\"\"
    n = len(pk_B[0])
    for trial in range(1, max_trials + 1):
        candidate = [rng.randrange(q) for _ in range(n)]
        if all(eval_quad_full(B, candidate, q) == yk for B, yk in zip(pk_B, y)):
            return candidate, trial
    return None, max_trials

FORGE_Q = 7
sizes = [(6, 3), (8, 4), (10, 5)]  # (v, o) pairs; q^o grows 7^3, 7^4, 7^5
rng3 = random.Random(99)
timing_rows = []
for v, o in sizes:
    sk_f = uov_keygen_q(v, o, rng3, FORGE_Q)
    y_f = [rng3.randrange(FORGE_Q) for _ in range(o)]

    t0 = time.perf_counter()
    sig_f, tries = uov_sign_q(sk_f, y_f, rng3, FORGE_Q)
    signer_time = time.perf_counter() - t0
    assert sig_f is not None and uov_verify(sk_f["B"], sig_f, y_f, FORGE_Q)

    max_trials = 6 * (FORGE_Q ** o)  # a few multiples of the expected q^o hitting time
    t0 = time.perf_counter()
    forged, forge_trials = brute_force_forge(sk_f["B"], y_f, FORGE_Q, rng3, max_trials)
    forger_time = time.perf_counter() - t0

    timing_rows.append((v, o, signer_time, forger_time, tries, forge_trials, forged is not None))
    print(f"v={v:2d} o={o}  q^o={FORGE_Q**o:6d}  signer: {signer_time*1000:7.3f} ms ({tries} attempt(s))  "
          f"forger: {forger_time*1000:9.3f} ms ({forge_trials} trial(s), found={forged is not None})")

# The legitimate signer's cost is dominated by one small o x o linear solve
# and stays roughly flat across this sweep; the forger's cost grows with
# the search space q^o and is, in every row, orders of magnitude larger.
for v, o, signer_time, forger_time, tries, forge_trials, found in timing_rows:
    assert found, (v, o, "brute force did not find a forgery within the trial budget")
    assert forger_time > signer_time
ratios = [forger_time / max(signer_time, 1e-9) for (_, _, signer_time, forger_time, *_ ) in timing_rows]
print(f"forger/signer time ratios across the sweep: {[round(r) for r in ratios]}")
assert ratios[-1] > ratios[0]  # the gap widens as o grows, not shrinks
""")

# --------------------------------------------------------------------- closing
md(r"""
### What this lab does and does not show

Part A verified Derivation 16.2's soundness formula exactly, for the exact
$N=3$ construction the derivation describes, and then again at $N=5$ to
confirm the formula's dependence on $N$ is the one the derivation claims —
not FAEST, MQOM or SDitH themselves, which use VOLE-in-the-head or TCitH
refinements over much larger $N$ (Table 16.2), but the same underlying
argument. Part B verified
that a trapdoor turns a hard search problem into a fast linear solve for
whoever holds it, and left it exponentially hard for whoever does not — at
a toy scale where "exponentially hard" still means milliseconds, not the
$2^{128}$-class hardness Table 16.3's real parameter sets are chosen to
guarantee. Neither part should be read as, or used as, a security estimate
for any live scheme.
""")

code(r"""
def _selftest():
    # Part A, N=3
    assert completeness_failures == 0
    assert within_4sigma(observed_catch_rate, 2 / 3, N_SOUNDNESS_TRIALS)[0]
    for tau, (empirical, predicted) in results.items():
        assert within_4sigma(empirical, predicted, N_FORGERY_TRIALS)[0], tau
        assert abs(predicted - (1 / 3) ** tau) < 1e-12  # the prediction really is (1/N)^tau

    # Part A, N=5 (Exercise 16.11)
    assert n5_completeness_failures == 0
    assert within_4sigma(observed_catch_rate_n5, 4 / 5, N_SOUNDNESS_TRIALS)[0]
    for tau, (empirical, predicted) in results_n5.items():
        assert within_4sigma(empirical, predicted, N_FORGERY_TRIALS)[0], tau
        assert abs(predicted - (1 / 5) ** tau) < 1e-12
        assert results_n5[tau][0] < results[tau][0]

    # Part B
    assert verified
    assert not uov_verify(sk["B"], bad_sig, target_y)
    for v, o, signer_time, forger_time, tries, forge_trials, found in timing_rows:
        assert found
        assert forger_time > signer_time
    assert ratios[-1] > ratios[0]

    print("all checks passed")

_selftest()
""")

nb["cells"] = C
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11"},
}

with open("lab16.ipynb", "w") as fh:
    nbf.write(nb, fh)
print(f"wrote lab16.ipynb with {len(C)} cells")
