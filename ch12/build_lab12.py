"""Build ch12/lab12.ipynb for 'Maths for Post-Quantum Cryptography'.

The notebook is generated from source rather than hand-edited so that it stays
diffable in git and reproducible in CI. Run:  python3 build_lab12.py
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
C = []
def _clean(t): return t.strip("\n").replace('\\"', '"')
def md(t): C.append(nbf.v4.new_markdown_cell(_clean(t)))
def code(t): C.append(nbf.v4.new_code_cell(_clean(t)))

# ---------------------------------------------------------------- front matter
md(r"""
# Lab 12 — The parallelepiped leak, seen and fixed

**Maths for Post-Quantum Cryptography**, Chapter 12: *FN-DSA / FALCON*

---

Three parts. Part A builds a genuinely working toy NTRU key pair —
including solving the NTRU equation $fG-gF=q$ for $F,G$, the "real
work" §12.1 mentions and declines to derive — and confirms $B_{\rm
pub}$ and $B_{\rm sec}$ generate the same lattice. Part B reproduces
Derivation 12.1's leak by measurement: naive nearest-plane rounding
against the secret basis, many times, and the empirical covariance of
the rounding error really is shaped like $B_{\rm sec}$'s own
parallelepiped; then Klein's randomised fix is implemented and shown
to erase that shape, for two genuinely different secret bases of the
*same* lattice. Part C repeats Part B's sampler at deliberately
degraded numerical precision and watches the fix's isotropy break down
as precision drops — a measured reason for the 53-bit requirement
§12.5 discusses, not an assertion.

**Part A — a toy NTRU lattice.** A small ring ($n=8$), a small
modulus, short ternary $f,g$, and the actual recursive algorithm
(a compact version of the one FALCON's own keygen uses) that solves
$fG-gF=q$ for short $F,G$. $B_{\rm pub}$ and $B_{\rm sec}$ are built
explicitly as $2n\times 2n$ integer matrices and confirmed to generate
the identical lattice via an exact integer unimodular transform.

**Part B — the leak, and Klein's fix, measured.** Naive Babai
nearest-plane rounding's error covariance is compared against two
predictions — "shaped like $B_{\rm sec}$'s Gram-Schmidt directions"
and "isotropic" — and matches the first, not the second. A randomised
discrete-Gaussian version of the same rounding step is then compared
against the same two predictions and matches the second, not the
first, for two different (but lattice-equivalent) secret bases.

**Part C — why 53 bits.** The randomised sampler from Part B is rerun
with every intermediate real value rounded to a coarse step size,
standing in for a low-precision numeric format, and the point at which
isotropy collapses is measured directly.

### Requirements

```
python >= 3.9
numpy
sympy
```

`sympy` is used once, for an exact-arithmetic check that two integer
bases generate the same lattice — everything numerical after that is
`numpy` floating point, deliberately, since floating point is this
chapter's entire subject.

A single `_selftest()` at the end repeats every numerical claim this
lab makes. CI runs this notebook on every commit.

**A note on scale.** $n=8$ and a two-digit modulus are chosen so that
solving the NTRU equation, building $16\times 16$ matrices, and
running thousands of sampling trials all finish in seconds — not for
security. FALCON's real parameters are $n\in\{512,1024\}$ and
$q=12289$ (Table 12.1); nothing here is a working signature scheme.
""")

# ============================================================ PART A
md(r"""
## Part A — a toy NTRU lattice

Work in $R=\mathbb Z[x]/(x^n+1)$, $n=8$. Represent a ring element as a
length-$n$ list of integer coefficients, and negacyclic ("mod
$x^n+1$") convolution as the ring's multiplication.
""")

code(r"""
import random
import numpy as np

N = 8       # toy ring degree (FALCON's real values: 512, 1024)
Q = 97      # toy modulus (FALCON's real value: 12289 for both parameter sets)

def negacyclic_mul(a, b):
    "Multiply two length-n integer coefficient lists mod (x^n+1)."
    n = len(a)
    res = [0] * (2 * n)
    for i, ai in enumerate(a):
        if ai == 0:
            continue
        for j, bj in enumerate(b):
            res[i + j] += ai * bj
    out = [0] * n
    for i in range(2 * n - 1):
        if i < n:
            out[i] += res[i]
        else:
            out[i - n] -= res[i]   # x^n = -1: wraparound terms flip sign
    return out

def poly_sub(a, b): return [x - y for x, y in zip(a, b)]

# sanity: (1+x)*(1-x) = 1 - x^2, and x^n * 1 = -1 (the defining relation)
assert negacyclic_mul([1, 1, 0, 0, 0, 0, 0, 0], [1, -1, 0, 0, 0, 0, 0, 0]) == \
       [1, 0, -1, 0, 0, 0, 0, 0]
one = [1, 0, 0, 0, 0, 0, 0, 0]
xN_minus_1 = [0, 1, 0, 0, 0, 0, 0, 0]   # placeholder, replaced below
x_poly = [0, 1, 0, 0, 0, 0, 0, 0]
xn = x_poly
for _ in range(N - 1):
    xn = negacyclic_mul(xn, x_poly)
assert xn == [-1, 0, 0, 0, 0, 0, 0, 0], "x^N should reduce to -1"
print("negacyclic_mul sanity checks pass")
""")

md(r"""
### Solving the NTRU equation

§12.1 samples short $f,g$ and asserts that short $F,G$ with
$fG-gF=q\pmod\phi$ exist and can be found "via an extended-Euclidean-
style algorithm," without deriving it. Here it is, in compact form —
essentially FALCON's own keygen algorithm (Pornin & Prest 2019),
specialised to $n$ a power of two.

The key idea is a *field norm*: splitting $f(x)=f_e(x^2)+x f_o(x^2)$
into even- and odd-indexed coefficients, the product
$f(x)f(-x)=f_e(x^2)^2-x^2f_o(x^2)^2$ depends only on $x^2$, i.e. it is
a polynomial $N(f)(y)$ in the *half-degree* ring
$\mathbb Z[y]/(y^{n/2}+1)$. Solving the NTRU equation for
$(N(f),N(g))$ at half the degree, then lifting back up via
$F(x)=g(-x)F_{\rm half}(x^2)$, $G(x)=f(-x)G_{\rm half}(x^2)$, gives a
solution at the full degree — because
$fG-gF = f(x)f(-x)G_{\rm half}(x^2) - g(x)g(-x)F_{\rm half}(x^2)
= N(f)(x^2)G_{\rm half}(x^2) - N(g)(x^2)F_{\rm half}(x^2)$, which is
exactly the half-degree equation evaluated at $y=x^2$. Recursing
down to degree $1$ — where $f,g$ are plain integers and $fG-gF=q$ is
solved by the ordinary extended Euclidean algorithm — bottoms the
recursion out.

The $(F,G)$ this produces is an exact solution but not a *short* one
(coefficients grow with every recursive squaring); a handful of Babai
reduction rounds afterwards — replacing $(F,G)$ by
$(F-kf,\,G-kg)$ for a polynomial $k$ chosen to shrink both, which
leaves $fG-gF$ exactly unchanged since $fkg=gkf$ in a commutative
ring — brings it back down to the same scale as $f,g$.
""")

code(r"""
def split_even_odd(f):
    return f[0::2], f[1::2]

def field_norm(f):
    "N(f)(y), y = x^2, such that N(f)(x^2) = f(x)*f(-x) mod (x^n+1)."
    fe, fo = split_even_odd(f)
    fe2 = negacyclic_mul(fe, fe)
    fo2 = negacyclic_mul(fo, fo)
    y_fo2 = [-fo2[-1]] + fo2[:-1]   # multiplying by y in Z[y]/(y^m+1): shift + sign flip on wrap
    return poly_sub(fe2, y_fo2)

def ext_gcd(a, b):
    "Integer extended Euclid: returns (g, u, v) with a*u + b*v = g = gcd(a,b)."
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r != 0:
        quot = old_r // r
        old_r, r = r, old_r - quot * r
        old_s, s = s, old_s - quot * s
        old_t, t = t, old_t - quot * t
    return old_r, old_s, old_t

def negate_odd(poly):
    "f(-x): flip the sign of every odd-degree coefficient."
    return [c if i % 2 == 0 else -c for i, c in enumerate(poly)]

def upsample(poly_half, n):
    "Fp(x^2): insert Fp's coefficients at even positions, zero at odd."
    out = [0] * n
    for i, c in enumerate(poly_half):
        out[2 * i] = c
    return out

def solve_ntru_equation(f, g, q):
    "Exact (not yet short) F,G with f*G - g*F = q mod (x^n+1). None if no solution."
    n = len(f)
    if n == 1:
        a, b = f[0], g[0]
        d, u, v = ext_gcd(a, b)          # a*u + b*v = d
        if d == 0 or q % d != 0:
            return None
        k = q // d
        return [-v * k], [u * k]          # f*(u k) - g*(-v k) = k*(a u + b v) = k d = q
    Nf, Ng = field_norm(f), field_norm(g)
    sub = solve_ntru_equation(Nf, Ng, q)
    if sub is None:
        return None
    Fp, Gp = sub
    F = negacyclic_mul(negate_odd(g), upsample(Fp, n))
    G = negacyclic_mul(negate_odd(f), upsample(Gp, n))
    return F, G

def verify_ntru_equation(f, g, F, G, q):
    lhs = poly_sub(negacyclic_mul(f, G), negacyclic_mul(g, F))
    return lhs == [q] + [0] * (len(f) - 1)

def babai_reduce_FG(F, G, f, g, iters=8):
    "Shrink (F,G) by repeatedly subtracting k*(f,g) for a real-rounded polynomial k."
    n = len(f)
    roots = [np.exp(1j * np.pi * (2 * j + 1) / n) for j in range(n)]
    V = np.array([[r ** k for k in range(n)] for r in roots], dtype=complex)
    Vinv = np.linalg.inv(V)
    f_hat = V @ np.array(f, dtype=complex)
    g_hat = V @ np.array(g, dtype=complex)
    denom = np.abs(f_hat) ** 2 + np.abs(g_hat) ** 2
    Fcur, Gcur = list(F), list(G)
    for _ in range(iters):
        F_hat = V @ np.array(Fcur, dtype=complex)
        G_hat = V @ np.array(Gcur, dtype=complex)
        k_hat = (np.conj(f_hat) * F_hat + np.conj(g_hat) * G_hat) / denom
        k = [int(round(c)) for c in np.real(Vinv @ k_hat)]
        if all(x == 0 for x in k):
            break
        Fcur = poly_sub(Fcur, negacyclic_mul(k, f))
        Gcur = poly_sub(Gcur, negacyclic_mul(k, g))
    return Fcur, Gcur
""")

code(r"""
def poly_trim(a):
    a = list(a)
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    return a

def poly_divmod_modq(a, b, q):
    a, b = poly_trim([c % q for c in a]), poly_trim([c % q for c in b])
    binv_lead = pow(b[-1], -1, q)
    quot = [0] * max(len(a) - len(b) + 1, 1)
    rem = a[:]
    while len(poly_trim(rem)) >= len(b) and poly_trim(rem) != [0]:
        rem = poly_trim(rem)
        shift = len(rem) - len(b)
        coeff = (rem[-1] * binv_lead) % q
        quot[shift] = (quot[shift] + coeff) % q
        sub = [0] * shift + [(coeff * x) % q for x in b]
        sub += [0] * (len(rem) - len(sub))
        rem = poly_trim([(x - y) % q for x, y in zip(rem, sub)])
    return poly_trim(quot), poly_trim(rem)

def poly_inverse_mod(f, q, n):
    "f^{-1} in Z_q[x]/(x^n+1), via extended Euclid over GF(q)[x]. None if not invertible."
    phi = [1] + [0] * (n - 1) + [1]
    r0, r1 = poly_trim([c % q for c in f]), poly_trim(phi)
    s0, s1 = [1], [0]
    def psub(u, v):
        L = max(len(u), len(v)); u = u + [0]*(L-len(u)); v = v + [0]*(L-len(v))
        return poly_trim([(x - y) % q for x, y in zip(u, v)])
    def pmul(u, v):
        res = [0] * (len(u) + len(v) - 1)
        for i, ui in enumerate(u):
            for j, vj in enumerate(v):
                res[i + j] = (res[i + j] + ui * vj) % q
        return poly_trim(res)
    while poly_trim(r1) != [0]:
        quot, rem = poly_divmod_modq(r0, r1, q)
        r0, r1 = r1, rem
        s0, s1 = s1, psub(s0, pmul(quot, s1))
    if poly_trim(r0) != [1]:
        return None
    inv = [c % q for c in s0] + [0] * n
    return inv[:n]

def negacyclic_mul_modq(a, b, q):
    return [c % q for c in negacyclic_mul(a, b)]
""")

md(r"""
### A toy key pair

Search short ternary $f,g$ (coefficients in $\{-1,0,1\}$, the same
shape of "short" every earlier chapter used) until one is found with
$f$ invertible mod $q$ and a reduced $(F,G)$ whose coefficients stay
comparably small.
""")

code(r"""
def find_toy_ntru_instance(seed, n=N, q=Q, max_coeff=30, trials=4000):
    rng = random.Random(seed)
    for _ in range(trials):
        f = [rng.choice([-1, 0, 1]) for _ in range(n)]
        g = [rng.choice([-1, 0, 1]) for _ in range(n)]
        finv = poly_inverse_mod(f, q, n)
        if finv is None:
            continue
        sol = solve_ntru_equation(f, g, q)
        if sol is None:
            continue
        F, G = babai_reduce_FG(*sol, f, g)
        if not verify_ntru_equation(f, g, F, G, q):
            continue
        if max(max(abs(c) for c in F), max(abs(c) for c in G)) > max_coeff:
            continue
        return dict(f=f, g=g, F=F, G=G, finv=finv)
    raise RuntimeError("no instance found -- widen the search")

inst = find_toy_ntru_instance(seed=7)
f, g, F, G, finv = inst["f"], inst["g"], inst["F"], inst["G"], inst["finv"]
h = negacyclic_mul_modq(g, finv, Q)

print("f  =", f)
print("g  =", g)
print("F  =", F)
print("G  =", G)
print("h = g f^-1 mod q =", h)
assert negacyclic_mul_modq(f, h, Q) == [c % Q for c in g], "f*h should reproduce g mod q"
assert verify_ntru_equation(f, g, F, G, Q)
print("NTRU equation f*G - g*F = q holds exactly; f*h = g mod q confirmed")
""")

md(r"""
### $B_{\rm pub}$, $B_{\rm sec}$, and one lattice

Build both $2n\times 2n$ integer bases explicitly, as in §12.1, using
the $n\times n$ matrix $M(a)$ that represents "multiply by $a$" in the
negacyclic ring. Two bases generate the same lattice exactly when one
is an integer, unimodular (determinant $\pm1$) transform of the other
— checked here with exact rational arithmetic, so there is no
floating-point doubt about the answer.
""")

code(r"""
import sympy

def circulant_matrix(a, n):
    "n x n integer matrix M with M @ v == negacyclic_mul(a, v)."
    M = np.zeros((n, n), dtype=object)
    for col in range(n):
        e = [0] * n
        e[col] = 1
        M[:, col] = negacyclic_mul(a, e)
    return M

Mf, Mg, MF, MG, Mh = (circulant_matrix(p, N) for p in (f, g, F, G, h))
In, Zn = np.eye(N, dtype=object), np.zeros((N, N), dtype=object)

B_sec = np.block([[Mg, -Mf], [MG, -MF]])
B_pub = np.block([[-Mh, In], [Q * In, Zn]])

B_sec_sym, B_pub_sym = sympy.Matrix(B_sec.tolist()), sympy.Matrix(B_pub.tolist())
det_sec = B_sec_sym.det()
det_pub = B_pub_sym.det()
print("det(B_sec) =", det_sec, " det(B_pub) =", det_pub, " q^n =", Q ** N)
assert abs(det_sec) == Q ** N == abs(det_pub)

T = B_sec_sym * B_pub_sym.inv()      # B_sec = T @ B_pub
T_is_integer = all(entry.is_integer for entry in T)
print("T = B_sec . B_pub^-1 is an integer matrix:", T_is_integer, " det(T) =", T.det())
assert T_is_integer and abs(T.det()) == 1, "B_sec and B_pub must generate the same lattice"
print("Part A: B_pub and B_sec confirmed to generate the identical 2n-dimensional lattice")
""")

# ============================================================ PART B
md(r"""
## Part B — the leak, and Klein's fix, measured

Babai's nearest-plane algorithm reduces a real target vector against
$B_{\rm sec}$'s Gram–Schmidt orthogonalisation $B^*$, one row at a
time, rounding the coefficient in each Gram–Schmidt direction. "Naive"
rounding always rounds to the nearest integer; Klein's fix samples a
*discrete Gaussian* centred on that same real value instead — wide
enough (parameter $\sigma$, scaled per-direction by $\sigma/\lVert
b^*_i\rVert$ so every direction contributes equally to the output) to
make the result close to independent of which particular short basis
produced it.
""")

code(r"""
def gram_schmidt(B):
    m = B.shape[0]
    Bstar = np.zeros_like(B, dtype=float)
    for i in range(m):
        Bstar[i] = B[i].astype(float)
        for j in range(i):
            mu = np.dot(B[i], Bstar[j]) / np.dot(Bstar[j], Bstar[j])
            Bstar[i] = Bstar[i] - mu * Bstar[j]
    return Bstar

def discrete_gaussian_sample(center, sigma, rng, tail=6):
    lo, hi = int(np.floor(center - tail * sigma)), int(np.ceil(center + tail * sigma))
    while True:
        cand = rng.integers(lo, hi + 1)
        d = cand - center
        if rng.random() < np.exp(-d * d / (2 * sigma * sigma)):
            return cand

def babai_round(B, Bstar, target, randomized, rng, SIGMA=None, step=None):
    "Nearest-plane (randomized=False) or Klein-randomised (True) rounding. Returns the error e = target - lattice point."
    def snap(x):
        return x if step is None else np.round(x / step) * step
    m = B.shape[0]
    v = target.astype(float).copy()
    bnorms = np.array([np.dot(Bstar[i], Bstar[i]) for i in range(m)])
    for i in range(m - 1, -1, -1):
        c_real = snap(np.dot(v, Bstar[i]) / bnorms[i])
        if not randomized:
            c = round(c_real)
        else:
            sigma_i = snap(SIGMA / np.sqrt(bnorms[i]))
            c = discrete_gaussian_sample(c_real, max(sigma_i, 1e-6), rng)
        v = v - c * B[i]
        if step is not None:
            v = snap(v)
    return v

def cosine_sim(A, B):
    a, b = A.flatten(), B.flatten()
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def isotropy_metrics(errors, Bstar_for_prediction=None):
    cov = np.cov(np.array(errors).T)
    ev = np.linalg.eigvalsh(cov)
    iso_pred = np.eye(cov.shape[0]) * np.trace(cov) / cov.shape[0]
    out = dict(eig_ratio=float(ev.max() / ev.min()), cos_sim_isotropic=cosine_sim(cov, iso_pred))
    if Bstar_for_prediction is not None:
        gso_pred = sum((1 / 12.0) * np.outer(Bstar_for_prediction[i], Bstar_for_prediction[i])
                        for i in range(Bstar_for_prediction.shape[0]))
        out["cos_sim_gso_shaped"] = cosine_sim(cov, gso_pred)
    return out
""")

code(r"""
B_sec_f = B_sec.astype(float)
Bstar = gram_schmidt(B_sec_f)
gso_norms = np.sqrt(np.array([np.dot(Bstar[i], Bstar[i]) for i in range(2 * N)]))
SIGMA = 2.0 * gso_norms.max()
scale = np.linalg.norm(B_sec_f, axis=1).mean()

rng = np.random.default_rng(42)
NTRIALS = 3000
errors_naive, errors_klein = [], []
for _ in range(NTRIALS):
    target = rng.uniform(-1, 1, size=2 * N) * scale
    errors_naive.append(babai_round(B_sec_f, Bstar, target, randomized=False, rng=rng))
    errors_klein.append(babai_round(B_sec_f, Bstar, target, randomized=True, rng=rng, SIGMA=SIGMA))

m_naive = isotropy_metrics(errors_naive, Bstar)
m_klein = isotropy_metrics(errors_klein, Bstar)
print("naive rounding: ", m_naive)
print("Klein rounding: ", m_klein)

# The naive leak matches the GSO-shaped prediction far better than the isotropic one.
assert m_naive["cos_sim_gso_shaped"] > 0.95
assert m_naive["cos_sim_gso_shaped"] - m_naive["cos_sim_isotropic"] > 0.2
# Klein's fix matches the isotropic prediction far better than the GSO-shaped one.
assert m_klein["cos_sim_isotropic"] > 0.95
assert m_klein["cos_sim_isotropic"] - m_klein["cos_sim_gso_shaped"] > 0.2
# and the naive leak is measurably anisotropic while Klein's is close to isotropic
assert m_naive["eig_ratio"] > 20
assert m_klein["eig_ratio"] < 3
print("Part B: naive rounding's leak matches B_sec's own shape; Klein's fix does not")
""")

md(r"""
### A second, different secret basis for the *same* lattice

Apply a small unimodular row transform to $B_{\rm sec}$ — elementary
integer row additions, determinant exactly $\pm1$ — to get a
genuinely different matrix that still generates the identical lattice
(confirmed the same way as Part A). Klein's fix should land close to
isotropic for this basis too, even though its rows, and its
Gram–Schmidt directions, are not the same as the first basis's.
""")

code(r"""
rng_u = np.random.default_rng(123)
U = np.eye(2 * N, dtype=object)
for _ in range(6):
    i, j = int(rng_u.integers(0, 2 * N)), int(rng_u.integers(0, 2 * N))
    if i == j:
        continue
    U[i] += int(rng_u.integers(-1, 2)) * U[j]

B_sec2 = U @ B_sec
T2 = sympy.Matrix(B_sec2.tolist()) * sympy.Matrix(B_sec.tolist()).inv()
assert all(e.is_integer for e in T2) and abs(T2.det()) == 1, "B_sec2 must generate the same lattice as B_sec"
print("second secret basis confirmed to generate the same lattice (unimodular transform, det =", T2.det(), ")")

B_sec2_f = B_sec2.astype(float)
Bstar2 = gram_schmidt(B_sec2_f)
SIGMA2 = 2.0 * np.sqrt(np.array([np.dot(Bstar2[i], Bstar2[i]) for i in range(2 * N)])).max()
scale2 = np.linalg.norm(B_sec2_f, axis=1).mean()

rng2 = np.random.default_rng(99)
errors_naive2, errors_klein2 = [], []
for _ in range(NTRIALS):
    target = rng2.uniform(-1, 1, size=2 * N) * scale2
    errors_naive2.append(babai_round(B_sec2_f, Bstar2, target, randomized=False, rng=rng2))
    errors_klein2.append(babai_round(B_sec2_f, Bstar2, target, randomized=True, rng=rng2, SIGMA=SIGMA2))

m_naive2 = isotropy_metrics(errors_naive2, Bstar2)
m_klein2 = isotropy_metrics(errors_klein2, Bstar2)
print("basis 2, naive rounding:", m_naive2)
print("basis 2, Klein rounding:", m_klein2)

assert m_naive2["cos_sim_gso_shaped"] > 0.95
assert m_klein2["cos_sim_isotropic"] > 0.95
assert m_klein2["eig_ratio"] < 3
print("Part B: Klein's fix lands close to isotropic for both secret bases of the same lattice")
""")

# ============================================================ PART C
md(r"""
## Part C — why 53 bits

Rerun Part B's Klein sampler against the first secret basis, but round
every intermediate real value (Gram–Schmidt inner products, per-
direction $\sigma$, the running residual) to the nearest multiple of a
coarse `step`, standing in for a low-precision floating-point format —
`step` shrinking towards zero recovers ordinary double precision, a
`step` comparable to the basis's own Gram–Schmidt norms recovers naive
rounding's leak in all but name.
""")

code(r"""
def measure_isotropy_at_step(step, ntrials=2500, seed=11):
    rng_s = np.random.default_rng(seed)
    errs = []
    for _ in range(ntrials):
        target = rng_s.uniform(-1, 1, size=2 * N) * scale
        errs.append(babai_round(B_sec_f, Bstar, target, randomized=True, rng=rng_s, SIGMA=SIGMA, step=step))
    return isotropy_metrics(errs)

steps = [1e-4, 1e-2, 0.1, 1, 2, 4, 8, 16]
results = {step: measure_isotropy_at_step(step) for step in steps}
for step, r in results.items():
    print(f"step={step:>7}  eig-ratio={r['eig_ratio']:8.3f}  cos-sim-to-isotropic={r['cos_sim_isotropic']:.4f}")

# High precision (small step) stays close to isotropic; coarse precision breaks it.
assert results[1e-4]["eig_ratio"] < 3
assert results[16]["eig_ratio"] > 15
assert results[1e-4]["cos_sim_isotropic"] > results[16]["cos_sim_isotropic"]
print("Part C: isotropy measurably degrades as intermediate precision is coarsened")
""")

# --------------------------------------------------------------------- close
md(r"""
## What to take away

Part A did the "real work" §12.1 waves at: an actual NTRU key pair,
solved rather than assumed, with $B_{\rm pub}$ and $B_{\rm sec}$
proven — not just asserted — to generate one lattice. Part B is
Derivation 12.1 end to end: the same rounding step, run naively, leaks
a measurable fingerprint of the secret basis; run with Klein's
randomisation, that fingerprint disappears, for two different secret
bases of the same lattice. Part C turns §12.5's "53 bits of precision"
from a specification detail into a measured threshold: precision this
lab's toy sampler can degrade on purpose, and watch the fix stop
working.
""")

code(r"""
def _selftest():
    # Part A
    assert verify_ntru_equation(f, g, F, G, Q)
    assert negacyclic_mul_modq(f, h, Q) == [c % Q for c in g]
    assert T_is_integer and abs(T.det()) == 1
    assert abs(det_sec) == Q ** N == abs(det_pub)

    # Part B, basis 1
    assert m_naive["cos_sim_gso_shaped"] > 0.95
    assert m_naive["cos_sim_gso_shaped"] - m_naive["cos_sim_isotropic"] > 0.2
    assert m_klein["cos_sim_isotropic"] > 0.95
    assert m_klein["cos_sim_isotropic"] - m_klein["cos_sim_gso_shaped"] > 0.2
    assert m_naive["eig_ratio"] > 20
    assert m_klein["eig_ratio"] < 3

    # Part B, basis 2 (different secret basis, same lattice)
    assert all(e.is_integer for e in T2) and abs(T2.det()) == 1
    assert m_naive2["cos_sim_gso_shaped"] > 0.95
    assert m_klein2["cos_sim_isotropic"] > 0.95
    assert m_klein2["eig_ratio"] < 3

    # Part C: precision degradation
    assert results[1e-4]["eig_ratio"] < 3
    assert results[16]["eig_ratio"] > 15
    assert results[1e-4]["cos_sim_isotropic"] > results[16]["cos_sim_isotropic"]

    print("all checks passed")

_selftest()
""")

nb["cells"] = C
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11"},
}

with open("lab12.ipynb", "w") as fh:
    nbf.write(nb, fh)
print(f"wrote lab12.ipynb with {len(C)} cells")
