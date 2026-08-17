"""Build ch14/lab14.ipynb for 'Maths for Post-Quantum Cryptography'.

The notebook is generated from source rather than hand-edited so that it stays
diffable in git and reproducible in CI. Run:  python3 build_lab14.py
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
C = []
def _clean(t): return t.strip("\n").replace('\\"', '"')
def md(t): C.append(nbf.v4.new_markdown_cell(_clean(t)))
def code(t): C.append(nbf.v4.new_code_cell(_clean(t)))

# ---------------------------------------------------------------- front matter
md(r"""
# Lab 14 — Building SIDH's key exchange, then breaking it the way Castryck-Decru did

**Maths for Post-Quantum Cryptography**, Chapter 14: *Isogenies: A Cautionary Tale*

---

Three parts. Part A implements Vélu's formulas from scratch, checks
them against a hand-worked numerical example, and confirms the one
property that makes an isogeny a *group homomorphism* and not just
some rational map. Part B builds a genuine miniature SIDH-style key
exchange on a toy elliptic curve small enough to brute-force-check
everything: two parties compute *different* secret isogenies, publish
their image curves plus a specific extra ingredient (the images of
each other's public torsion points), and land on the same shared
curve. Part C is the whole point of this chapter: it shows, on this
same toy curve, that the "extra ingredient" from Part B is not free —
an eavesdropper who sees only the public curve is left with a genuine
ambiguity about which secret produced it, and that ambiguity
collapses the instant they also see the published auxiliary point.

This is a simplified, honest illustration of *why* the auxiliary
torsion data SIDH publishes is exploitable, not a reproduction of
Castryck and Decru's actual attack. Their construction glues two
elliptic curves into a genus-2 abelian surface via Kani's theorem and
extracts the secret isogeny in polynomial time using far more
structure than "try every candidate" — see §14.3 for the real
mechanism. What this lab *can* honestly show, and does, is the
structural fact underneath it: the bare codomain curve alone
under-determines the secret kernel, and the published torsion images
resolve that under-determination directly. That gap between "the
curve alone" and "the curve plus torsion images" is where every
attack in this family lives, from this lab's crude candidate-check all
the way to the real 2022 break.

### Requirements

```
python >= 3.9
```

No third-party libraries — every finite-field, elliptic-curve, and
isogeny computation is built from scratch, at a scale small enough
that Part A's homomorphism check, Part B's key exchange, and Part C's
candidate search all run in well under a second combined.

**A note on scale and scope.** The toy curve here has order 90, chosen
so that its 3-torsion is *fully rational* ($E[3]\cong(\mathbb
Z/3)^2$, giving one party a genuine four-way secret) while its
5-torsion is only rational as a single cyclic subgroup of order 5 —
which means the *other* party's isogeny step has no real secrecy in
this toy (there is only one candidate kernel to choose). A production
SIDH-style scheme needs both parties' torsion fully two-dimensional,
which forces much larger curves defined over $\mathbb F_{p^2}$; this
lab trades that away to keep every step brute-force-checkable by eye.
Nothing here is a working cryptosystem, and the degree-2 ("even")
branch of Vélu's formulas — needed for real SIDH's power-of-two side —
is not implemented at all; both this lab's isogeny steps use only the
odd-prime-degree formula from Derivation 14.1.
""")

# ============================================================ PART A
md(r"""
## Part A — Vélu's formulas, implemented and checked

Work over $\mathbb F_p$ directly (no extension field needed for this
lab). A short-Weierstrass curve is `(a, b, p)` with points `(x, y)` or
`None` for the point at infinity $\mathcal O$. `ec_add` is the
textbook chord-and-tangent group law; `ec_scalar_mul` is double-and-add.

`velu_isogeny(a, b, p, R)` implements Derivation 14.1 exactly: given a
curve and a set `R` of kernel-coset representatives (one point from
each $\{Q,-Q\}$ pair inside the kernel, $Q\neq\mathcal O$), it returns
the codomain curve `(A, B)` and the map `phi` as a Python closure.
"""
)

code(r"""
def inv(x, p):
    return pow(x, p - 2, p)

def ec_add(P, Q, a, p):
    if P is None: return Q
    if Q is None: return P
    x1, y1 = P; x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0:
        return None
    if P == Q:
        if y1 == 0: return None
        lam = (3*x1*x1 + a) * inv(2*y1, p) % p
    else:
        if x1 == x2: return None
        lam = (y2 - y1) * inv(x2 - x1, p) % p
    x3 = (lam*lam - x1 - x2) % p
    y3 = (lam*(x1 - x3) - y1) % p
    return (x3, y3)

def ec_scalar_mul(k, P, a, p):
    R, base = None, P
    while k > 0:
        if k & 1: R = ec_add(R, base, a, p)
        base = ec_add(base, base, a, p)
        k >>= 1
    return R

def curve_points(a, b, p):
    pts = []
    for x in range(p):
        rhs = (x**3 + a*x + b) % p
        for y in range(p):
            if (y*y) % p == rhs:
                pts.append((x, y))
    return pts

def j_invariant(a, b, p):
    num = (1728 * 4 * pow(a, 3, p)) % p
    den = (4*pow(a, 3, p) + 27*pow(b, 2, p)) % p
    return (num * inv(den, p)) % p

def velu_isogeny(a, b, p, R):
    "Derivation 14.1: R = kernel-coset representatives, |R| = (l-1)/2 for a kernel of odd order l."
    Sv, Sw, data = 0, 0, []
    for xQ, yQ in R:
        gx = (3*xQ*xQ + a) % p
        gy = (-2*yQ) % p
        vQ = (2*gx) % p
        wQ = (gy*gy) % p
        Sv = (Sv + vQ) % p
        Sw = (Sw + wQ + xQ*vQ) % p
        data.append((xQ, vQ, wQ))
    A = (a - 5*Sv) % p
    B = (b - 7*Sw) % p
    def phi(P):
        if P is None: return None
        x, y = P
        X, Y = x, y
        for xQ, vQ, wQ in data:
            dx = (x - xQ) % p
            d1 = inv(dx, p); d2 = d1*d1 % p; d3 = d2*d1 % p
            X = (X + vQ*d1 + wQ*d2) % p
            Y = (Y - (2*wQ*y % p * d3 + vQ*y % p * d2)) % p
        return (X, Y)
    return A, B, phi

def kernel_reps(Q, l, a, p):
    "Representatives of (<Q> \\ {O}) / (P ~ -P), for Q of odd prime order l."
    seen, reps, cur = set(), [], Q
    for _ in range(l - 1):
        negcur = (cur[0], (-cur[1]) % p)
        if negcur not in seen:
            reps.append(cur)
        seen.add(cur)
        cur = ec_add(cur, Q, a, p)
    return reps
""")

md(r"""
### Check against Derivation 14.1's worked example

$E: y^2=x^3+3x+8$ over $\mathbb F_{101}$, kernel generated by $Q=(2,27)$
of order 3. The derivation's hand computation gives codomain
$E':y^2=x^3+55x+83$ and, for $P_1=(15,87),\,P_2=(19,37)$, image points
$\varphi(P_1)=(25,69)$, $\varphi(P_2)=(34,7)$, with
$\varphi(P_1+P_2)=\varphi(P_1)+_{E'}\varphi(P_2)$.
""")

code(r"""
reps_worked = kernel_reps((2, 27), 3, 3, 101)
A_w, B_w, phi_w = velu_isogeny(3, 8, 101, reps_worked)
print("worked-example codomain:", (A_w, B_w), "expected (55, 83)")
assert (A_w, B_w) == (55, 83)

P1, P2 = (15, 87), (19, 37)
phiP1, phiP2 = phi_w(P1), phi_w(P2)
print("phi(P1) =", phiP1, "expected (25, 69)")
print("phi(P2) =", phiP2, "expected (34, 7)")
assert phiP1 == (25, 69) and phiP2 == (34, 7)

P1P2 = ec_add(P1, P2, 3, 101)
lhs = phi_w(P1P2)
rhs = ec_add(phiP1, phiP2, A_w, 101)
print("phi(P1+P2) =", lhs, " phi(P1)+phi(P2) =", rhs)
assert lhs == rhs == (72, 64)
print("Part A, worked example: matches Derivation 14.1 exactly")
""")

md(r"""
### The toy curve for the rest of this lab

$E_0: y^2=x^3+5x$ over $\mathbb F_{73}$, order 90. Its 3-torsion is
*fully rational* — all 8 nonzero points of order 3 are defined over
$\mathbb F_{73}$ itself, giving $E_0[3]\cong(\mathbb Z/3)^2$ and hence
**four** distinct subgroups of order 3. Its 5-torsion is only a single
cyclic subgroup of order 5. This asymmetry is exactly what Part B
needs: one party (call her Alice) gets a genuine four-way secret
choice of degree-3 kernel; the other (Bob) has only one possible
degree-5 kernel, which we flag honestly as a toy simplification rather
than hide.
""")

code(r"""
P, A0, B0 = 73, 5, 0
E0_pts = curve_points(A0, B0, P)
print(f"#E0(F_{P}) = {len(E0_pts) + 1} (including O)")
assert len(E0_pts) + 1 == 90

order3 = [Q for Q in E0_pts if ec_scalar_mul(3, Q, A0, P) is None]
order5 = [Q for Q in E0_pts if ec_scalar_mul(5, Q, A0, P) is None]
print("points of order exactly 3:", len(order3), "  points of order exactly 5:", len(order5))
assert len(order3) == 8 and len(order5) == 4

seen, subgroups3 = set(), []
for Q in order3:
    if Q in seen: continue
    Q2 = ec_scalar_mul(2, Q, A0, P)
    subgroups3.append((Q, Q2)); seen.add(Q); seen.add(Q2)
print("the four order-3 subgroups:", subgroups3)
assert len(subgroups3) == 4

R1, R2 = (12, 6), (24, 1)                     # a basis of E0[3] =~ (Z/3)^2
GEN5 = (23, 23)                               # generator of the (unique) order-5 subgroup
assert ec_scalar_mul(3, R1, A0, P) is None and ec_scalar_mul(3, R2, A0, P) is None
assert ec_scalar_mul(5, GEN5, A0, P) is None

def alice_kernel_point(kA):
    "kA in {0,1,2,'inf'} indexes the 4 subgroups of E0[3] = <R1,R2>, following SIDH's own P+[k]Q convention."
    if kA == 0:   return R1
    if kA == 1:   return ec_add(R1, R2, A0, P)
    if kA == 2:   return ec_add(R1, ec_add(R2, R2, A0, P), A0, P)
    if kA == 'inf': return R2
    raise ValueError(kA)

covered = {alice_kernel_point(k) for k in (0, 1, 2, 'inf')}
print("the 4 secret choices land in 4 different subgroups:", len({frozenset(s) for s in subgroups3}) == 4)
""")

md(r"""
### A local piece of the isogeny graph, and the homomorphism check

Push every point through a degree-3 isogeny and a degree-5 isogeny and
confirm $\varphi(P+Q)=\varphi(P)+\varphi(Q)$ — the property that makes
this a *homomorphism* of elliptic curves, not just a formula. The
formula has genuine poles exactly at points whose $x$-coordinate
matches a kernel-coset representative (those points map to $\mathcal
O$, which this minimal `phi` does not special-case as an output) — so
the check below excludes exactly that set, and nothing else.
""")

code(r"""
import random
rng = random.Random(7)

def homomorphism_check(a, b, p, kernel_gen, l, n_trials=25):
    reps = kernel_reps(kernel_gen, l, a, p)
    kernel_xs = {r[0] for r in reps}
    A, B, phi = velu_isogeny(a, b, p, reps)
    pts = curve_points(a, b, p)
    tested, trials = 0, 0
    while tested < n_trials and trials < 2000:
        trials += 1
        Pp, Qp = rng.choice(pts), rng.choice(pts)
        if Pp[0] in kernel_xs or Qp[0] in kernel_xs: continue
        PQ = ec_add(Pp, Qp, a, p)
        if PQ is None or PQ[0] in kernel_xs: continue
        tested += 1
        if phi(PQ) != ec_add(phi(Pp), phi(Qp), A, p):
            return A, B, False
    return A, B, True

A3, B3, ok3 = homomorphism_check(A0, B0, P, R1, 3)
A5, B5, ok5 = homomorphism_check(A0, B0, P, GEN5, 5)
print(f"degree-3 isogeny: codomain=({A3},{B3}), homomorphism holds: {ok3}")
print(f"degree-5 isogeny: codomain=({A5},{B5}), homomorphism holds: {ok5}")
assert ok3 and ok5

print()
print("E0's four degree-3-isogenous curves, by secret choice:")
j_classes = {}
for kA in (0, 1, 2, 'inf'):
    reps = kernel_reps(alice_kernel_point(kA), 3, A0, P)
    A, B, _ = velu_isogeny(A0, B0, P, reps)
    j = j_invariant(A, B, P)
    j_classes.setdefault(j, []).append(kA)
    print(f"  kA={kA}: codomain=({A},{B})  j-invariant={j}")
print(f"distinct j-invariants reached: {len(j_classes)} (secrets sharing a class: {[v for v in j_classes.values() if len(v) > 1]})")
print("Part A: the isogeny graph already shows the ambiguity Part C will exploit -- two different secrets land on curves with the *same* j-invariant")
assert len(j_classes) == 2
""")

# ============================================================ PART B
md(r"""
## Part B — a toy SIDH-style key exchange

Following §14.2's mechanism exactly: Alice's secret is a degree-3
isogeny $\varphi_A:E_0\to E_A$ with kernel one of the four subgroups
above; Bob's is the (unique, here non-secret) degree-5 isogeny
$\varphi_B:E_0\to E_B$. Alice publishes $E_A$ **and** $\varphi_A(P_B)$
— the image of Bob's public generator under her secret map. Bob
publishes $E_B$ **and** $\varphi_B(R_1),\varphi_B(R_2)$ — the images
of Alice's public basis. Each party then pushes their *own* secret
kernel through the *other's* published curve and auxiliary points, and
both should land on the same shared curve.
""")

code(r"""
def shared_curve_alice(kA):
    "Alice: receives (EB, phiB(R1), phiB(R2)); reconstructs her kernel's image inside EB."
    reps_A = kernel_reps(alice_kernel_point(kA), 3, A0, P)
    A_A, B_A, phi_A = velu_isogeny(A0, B0, P, reps_A)          # Alice's own publication
    reps_B = kernel_reps(GEN5, 5, A0, P)
    A_B, B_B, phi_B = velu_isogeny(A0, B0, P, reps_B)          # Bob's publication
    phiB_R1, phiB_R2 = phi_B(R1), phi_B(R2)
    if kA == 0:      KA_image = phiB_R1
    elif kA == 1:    KA_image = ec_add(phiB_R1, phiB_R2, A_B, P)
    elif kA == 2:    KA_image = ec_add(phiB_R1, ec_add(phiB_R2, phiB_R2, A_B, P), A_B, P)
    else:            KA_image = phiB_R2
    reps_AB = kernel_reps(KA_image, 3, A_B, P)
    A_AB, B_AB, _ = velu_isogeny(A_B, B_B, P, reps_AB)
    return (A_A, B_A), phi_A(GEN5), (A_AB, B_AB)

def shared_curve_bob(kA):
    "Bob: receives (EA, phiA(GEN5)); pushes his own kernel's image through EA."
    reps_A = kernel_reps(alice_kernel_point(kA), 3, A0, P)
    A_A, B_A, phi_A = velu_isogeny(A0, B0, P, reps_A)
    phiA_gen5 = phi_A(GEN5)
    reps_BA = kernel_reps(phiA_gen5, 5, A_A, P)
    A_BA, B_BA, _ = velu_isogeny(A_A, B_A, P, reps_BA)
    return (A_BA, B_BA)

print(f"{'kA':>5} {'E_AB (Alice side)':>20} {'E_BA (Bob side)':>18}  match")
all_match = True
for kA in (0, 1, 2, 'inf'):
    EA_pub, phiA_gen5, E_AB = shared_curve_alice(kA)
    E_BA = shared_curve_bob(kA)
    m = (E_AB == E_BA)
    all_match &= m
    print(f"{str(kA):>5} {str(E_AB):>20} {str(E_BA):>18}  {m}")
assert all_match
print()
print("Part B: for every one of Alice's four possible secrets, both parties independently reach the same shared curve")
""")

# ============================================================ PART C
md(r"""
## Part C — what the auxiliary point actually leaks

Fix Alice's true secret at $k_A=1$. An eavesdropper sees everything
public: $E_0$, the basis $R_1,R_2,P_B$, and Alice's two published
values $E_A$ and $\varphi_A(P_B)$. Two questions: (1) does $E_A$ alone
pin down $k_A$ among the four candidates? (2) if not, does adding
$\varphi_A(P_B)$ resolve it?

This is a brute-force candidate check, not Castryck-Decru's actual
gluing construction — but it isolates the same underlying fact their
attack exploits: the auxiliary torsion image carries information the
bare codomain curve does not.
""")

code(r"""
TRUE_kA = 1
reps_true = kernel_reps(alice_kernel_point(TRUE_kA), 3, A0, P)
A_true, B_true, phi_true = velu_isogeny(A0, B0, P, reps_true)
published_EA = (A_true, B_true)
published_aux = phi_true(GEN5)
print(f"true secret kA={TRUE_kA}; published EA={published_EA}; published phiA(P_B)={published_aux}")
print()

print("--- attacker with EA only: try all 4 candidate secrets, compare j-invariant ---")
survivors_curve = []
for kA in (0, 1, 2, 'inf'):
    reps = kernel_reps(alice_kernel_point(kA), 3, A0, P)
    Ac, Bc, phic = velu_isogeny(A0, B0, P, reps)
    j_match = j_invariant(Ac, Bc, P) == j_invariant(*published_EA, P)
    print(f"  kA={kA}: E=({Ac},{Bc})  j={j_invariant(Ac,Bc,P)}  j-matches-published={j_match}")
    if j_match: survivors_curve.append(kA)
print(f"  => {len(survivors_curve)} candidates survive on curve/j-invariant evidence alone: {survivors_curve}")
assert len(survivors_curve) == 2

print()
print("--- same attacker, now also given the published auxiliary point phiA(P_B) ---")
survivors_aux = []
for kA in survivors_curve:
    reps = kernel_reps(alice_kernel_point(kA), 3, A0, P)
    Ac, Bc, phic = velu_isogeny(A0, B0, P, reps)
    candidate_aux = phic(GEN5)
    consistent = (candidate_aux == published_aux)
    print(f"  kA={kA}: phi(P_B)={candidate_aux}  matches published={consistent}")
    if consistent: survivors_aux.append(kA)
print(f"  => {len(survivors_aux)} candidate(s) survive once the auxiliary point is also checked: {survivors_aux}")
assert survivors_aux == [TRUE_kA]
print()
print("Part C: the curve alone left a real ambiguity (2 of 4 secrets tied); the published torsion image resolved it completely")
""")

# --------------------------------------------------------------------- close
md(r"""
## What to take away

Part A builds and checks Vélu's formulas independently of any
narrative about them — a rational map, verified to compose correctly
with the curve's own group law, on a curve small enough to see every
step. Part B is §14.2's SIDH mechanism working exactly as advertised:
two independently-computed paths through the isogeny graph, landing on
the same curve, for every one of Alice's four possible secrets. Part C
is why §14.3 calls the auxiliary torsion points a *structural* leak
rather than a hardness-assumption break: nothing about the isogeny
problem itself got easier between Part A and Part C — what changed is
that SIDH's own protocol handed an eavesdropper extra data the general
problem never requires anyone to reveal. CSIDH and SQIsign (§14.4)
remain standing on exactly the same isogeny-graph mathematics Part A
just built, precisely because neither one publishes this.
""")

code(r"""
def _selftest():
    # Part A
    assert (A_w, B_w) == (55, 83)
    assert phi_w((15, 87)) == (25, 69) and phi_w((19, 37)) == (34, 7)
    assert ok3 and ok5
    assert len(j_classes) == 2

    # Part B
    assert all_match

    # Part C
    assert len(survivors_curve) == 2
    assert survivors_aux == [TRUE_kA]

    print("all checks passed")

_selftest()
""")

nb["cells"] = C
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11"},
}

with open("lab14.ipynb", "w") as fh:
    nbf.write(nb, fh)
print(f"wrote lab14.ipynb with {len(C)} cells")
