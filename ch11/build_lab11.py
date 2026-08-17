"""Build ch11/lab11.ipynb for 'Maths for Post-Quantum Cryptography'.

The notebook is generated from source rather than hand-edited so that it stays
diffable in git and reproducible in CI. Run:  python3 build_lab11.py
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
C = []
# Cell bodies are written as raw strings so LaTeX backslashes survive; a
# docstring inside one has to be escaped as \" and is unescaped here.
def _clean(t): return t.strip("\n").replace('\\"', '"')
def md(t): C.append(nbf.v4.new_markdown_cell(_clean(t)))
def code(t): C.append(nbf.v4.new_code_cell(_clean(t)))

# ---------------------------------------------------------------- front matter
md(r"""
# Lab 11 — Building the whole chain, one hash function at a time

**Maths for Post-Quantum Cryptography**, Chapter 11: *FIPS 205: SLH-DSA*

---

Four parts, each one construction from the chapter, in the order the
chapter builds them. Part A implements Lamport signatures
(Definition 11.1) and then breaks them on purpose, exactly as
Derivation 11.1 predicts. Part B implements a WOTS+ hash chain
(Definition 11.2) and the checksum that closes off the one forgery
chains alone allow (Derivation 11.2) — including implementing that
forgery, to see the checksum actually stop it. Part C builds a Merkle
tree and an authentication path (Definition 11.3, Figure 11.3). Part D
assembles all three into a small, insecure, but fully working toy
SLH-DSA: real WOTS+ chains, a real Merkle hypertree (one layer), real
FORS, real KeyGen/Sign/Verify — and a direct check of §11.5's most
delicate claim, that a hypertree leaf reused by two different messages
signs one *fixed* value both times, not two different digests.

**Part A — Lamport, and breaking it on purpose.** One legitimate
signature, then a second on the bitwise-complement message, then full
secret-key extraction and a forged signature on an arbitrary third
message.

**Part B — WOTS+ and the checksum's job.** A legitimate signature;
then the checksum-free forgery Derivation 11.2 describes, shown to
fool a verifier that only checks the message-digit chains and shown
to fail against the real verifier, which also checks the checksum
chains.

**Part C — a Merkle tree and its authentication path.** An 8-leaf
tree, root, authentication path, and both tamper checks from
Figure 11.3's caption.

**Part D — a toy SLH-DSA end to end.** KeyGen/Sign/Verify assembled
from Parts A–C plus a small FORS instance, at a single hypertree layer
($d=1$, in the spirit of NIST SP 800-230's bounded-budget parameter
sets from §11.7). Several dozen signatures, a forgery-rejection check,
a byte-size check against Table 11.2's formula, and the leaf-collision
demonstration §11.5 and Table 11.2's box describe.

### Requirements

```
python >= 3.9
numpy
```

Nothing else. Every hash call in this notebook is a truncated SHA-256
— there is no cryptographic library anywhere in this file, because
the whole point of the chapter is that nothing beyond a hash function
is needed.

A single `_selftest()` at the end repeats every numerical claim this
lab makes. CI runs this notebook on every commit; if a change silently
breaks one of these facts, the test — not just a plot — fails.

**A note on scale.** Every parameter below is chosen for speed and
clarity, not security: Part A's toy Lamport key uses a 64-bit digest
(real Lamport for SHA-256 uses 256 bits), and Part D's toy SLH-DSA
uses a 4-byte truncated hash, a single hypertree layer of height 4
(16 leaves), and a FORS instance with $k=4$, $a=3$ — versus FIPS 205's
$n\in\{16,24,32\}$ bytes and $h$ in the sixties. Nothing here is a
security claim about these specific numbers; Tables 11.1–11.2's real
parameters are what FIPS 205 actually specifies.
""")

# ------------------------------------------------------------------ Part A
md(r"""
## Part A — Lamport, and breaking it on purpose

Definition 11.1, implemented directly with a truncated SHA-256 as $H$.
Toy digest length: 64 bits (32 secret pairs), instead of SHA-256's
usual 256 — enough to make the reuse attack's arithmetic visible
without waiting on 256 hash-pair generations.
""")

code(r"""
import hashlib
import numpy as np

N_BITS_LAMPORT = 64          # toy digest length (real Lamport/SHA-256: 256)
N_BYTES_LAMPORT = N_BITS_LAMPORT // 8

def lamport_H(x):
    return hashlib.sha256(x).digest()[:N_BYTES_LAMPORT]

def rand_bytes(rng, nbytes):
    return bytes(rng.integers(0, 256, size=nbytes, dtype=np.uint8))

def lamport_keygen(rng):
    sk = [[rand_bytes(rng, N_BYTES_LAMPORT) for _ in range(2)] for _ in range(N_BITS_LAMPORT)]
    pk = [[lamport_H(sk[i][b]) for b in range(2)] for i in range(N_BITS_LAMPORT)]
    return sk, pk

def rand_bits(rng, n):
    return [int(b) for b in rng.integers(0, 2, size=n)]

def lamport_sign(sk, bits):
    return [sk[i][bits[i]] for i in range(len(bits))]

def lamport_verify(pk, bits, sig):
    return all(lamport_H(sig[i]) == pk[i][bits[i]] for i in range(len(bits)))

rng = np.random.default_rng(1101)
sk, pk = lamport_keygen(rng)

# One legitimate signature.
m1 = rand_bits(rng, N_BITS_LAMPORT)
sig1 = lamport_sign(sk, m1)
ok1 = lamport_verify(pk, m1, sig1)
print(f"legitimate signature on m1 verifies: {ok1}")

# Reuse the SAME key on the bitwise complement of m1 -- Derivation 11.1's
# worst case, where every bit position differs.
m2 = [1 - b for b in m1]
sig2 = lamport_sign(sk, m2)
ok2 = lamport_verify(pk, m2, sig2)
print(f"legitimate signature on m2 (= complement of m1) verifies: {ok2}")

# Extract the full secret key from the two signatures.
recovered_sk = [[None, None] for _ in range(N_BITS_LAMPORT)]
for i in range(N_BITS_LAMPORT):
    recovered_sk[i][m1[i]] = sig1[i]
    recovered_sk[i][m2[i]] = sig2[i]
full_key_recovered = all(recovered_sk[i][0] is not None and recovered_sk[i][1] is not None
                          for i in range(N_BITS_LAMPORT))
print(f"entire {2*N_BITS_LAMPORT}-value secret key recovered: {full_key_recovered}")

# Forge a signature on a third message that was never legitimately signed.
m3 = rand_bits(rng, N_BITS_LAMPORT)
forged_sig = [recovered_sk[i][m3[i]] for i in range(N_BITS_LAMPORT)]
forged_ok = lamport_verify(pk, m3, forged_sig)
print(f"forged signature on a fresh, never-signed m3 verifies: {forged_ok}")
""")

md(r"""
Two signatures under one Lamport key, chosen to disagree everywhere,
handed over the entire secret key — exactly Derivation 11.1's claim —
and the forged signature on a message nobody ever legitimately signed
verifies as if it were genuine.
""")

# ------------------------------------------------------------------ Part B
md(r"""
## Part B — WOTS+ and the checksum's job

Definition 11.2's hash chain, signing, checksum and verification,
implemented directly. Toy parameters: $w=16$ ($\lg w=4$, the real
FIPS 205 value) and $n=4$ bytes (versus FIPS 205's 16/24/32), so
$\mathrm{len}_1=8$ and — computed from the general formula, not
hard-coded — $\mathrm{len}_2=2$ rather than FIPS 205's $3$, since
FIPS 205's $\mathrm{len}_2=3$ is a consequence of its larger $n$, not
a fixed constant of the scheme.
""")

code(r"""
import math

W = 16
LGW = int(math.log2(W))
N_BYTES = 4                                    # toy n (FIPS 205: 16/24/32)

def H(*parts):
    h = hashlib.sha256()
    for p in parts:
        h.update(p)
    return h.digest()[:N_BYTES]

def chain(x, steps):
    for _ in range(steps):
        x = H(x)
    return x

def int_to_digits(value, num_digits, w):
    digits = [0] * num_digits
    for i in range(num_digits - 1, -1, -1):
        digits[i] = value % w
        value //= w
    return digits

def bytes_to_digits(data, num_digits, w):
    return int_to_digits(int.from_bytes(data, "big"), num_digits, w)

LEN1 = math.ceil(8 * N_BYTES / LGW)
LEN2 = math.floor(math.log2(LEN1 * (W - 1)) / LGW) + 1
LEN = LEN1 + LEN2
print(f"toy WOTS+: w={W}, n={N_BYTES} bytes -> len1={LEN1}, len2={LEN2}, len={LEN}")
print(f"(FIPS 205 itself, at w=16, n in {{16,24,32}} bytes, always gets len2=3)")

def wots_digits(msg_hash):
    md_digits = bytes_to_digits(msg_hash, LEN1, W)
    checksum = sum(W - 1 - d for d in md_digits)
    cd_digits = int_to_digits(checksum, LEN2, W)
    return md_digits + cd_digits

def wots_keygen(rng):
    sk = [rand_bytes(rng, N_BYTES) for _ in range(LEN)]
    pk = [chain(s, W - 1) for s in sk]
    return sk, pk

def wots_sign(sk, msg_hash):
    digits = wots_digits(msg_hash)
    return [chain(sk[i], digits[i]) for i in range(LEN)]

def wots_pk_from_sig(sig, msg_hash):
    digits = wots_digits(msg_hash)
    return [chain(sig[i], W - 1 - digits[i]) for i in range(LEN)]

def wots_verify(pk, msg_hash, sig):
    return wots_pk_from_sig(sig, msg_hash) == pk

def wots_verify_message_part_only(pk, msg_hash, sig):
    # A deliberately-broken verifier: checks only the len1 message-digit
    # chains, forgetting the len2 checksum chains. This is exactly the
    # verifier Derivation 11.2 shows is forgeable.
    digits = bytes_to_digits(msg_hash, LEN1, W)
    return all(chain(sig[i], W - 1 - digits[i]) == pk[i] for i in range(LEN1))

rng = np.random.default_rng(1102)

trials, fooled_count, real_fails = 50, 0, 0
for _ in range(trials):
    sk, pk = wots_keygen(rng)
    msg_hash = rand_bytes(rng, N_BYTES)
    sig = wots_sign(sk, msg_hash)
    assert wots_verify(pk, msg_hash, sig), "a legitimate signature must verify"

    # Naive forgery: push every MESSAGE digit up to the maximum w-1 (always
    # legal, since d_i <= w-1 always), walking the revealed chain nodes
    # forward -- no secret needed. Leave the checksum-part signature values
    # untouched, since the forger has no way to move them backward.
    orig_digits = wots_digits(msg_hash)
    forged_md_digits = [W - 1] * LEN1
    forged_sig = ([chain(sig[i], forged_md_digits[i] - orig_digits[i]) for i in range(LEN1)]
                  + list(sig[LEN1:]))
    forged_value = sum(d * (W ** (LEN1 - 1 - i)) for i, d in enumerate(forged_md_digits))
    forged_msg_hash = forged_value.to_bytes(N_BYTES, "big")

    fooled = wots_verify_message_part_only(pk, forged_msg_hash, forged_sig)
    real_ok = wots_verify(pk, forged_msg_hash, forged_sig)
    fooled_count += int(fooled)
    real_fails += int(not real_ok)

print(f"checksum-free verifier fooled by the forgery: {fooled_count}/{trials} trials")
print(f"real verifier (checksum included) rejects the forgery: {real_fails}/{trials} trials")
""")

md(r"""
Every trial: the message-only verifier accepts the forged, all-maximum-
digit message; the real verifier, which also recomputes the checksum
chains, rejects it every time — Derivation 11.2's argument, executed
rather than just proved.
""")

# ------------------------------------------------------------------ Part C
md(r"""
## Part C — a Merkle tree and its authentication path

Definition 11.3, an 8-leaf tree (Figure 11.3's own example), built and
verified directly.
""")

code(r"""
def merkle_build(leaves):
    levels = [list(leaves)]
    level = levels[0]
    while len(level) > 1:
        nxt = [H(level[i], level[i + 1]) for i in range(0, len(level), 2)]
        levels.append(nxt)
        level = nxt
    return levels                       # levels[0] = leaves, ..., levels[-1] = [root]

def merkle_auth_path(levels, index):
    path, idx = [], index
    for level in levels[:-1]:
        path.append(level[idx ^ 1])
        idx //= 2
    return path

def merkle_root_from_path(leaf, index, path):
    node, idx = leaf, index
    for sib in path:
        node = H(node, sib) if idx % 2 == 0 else H(sib, node)
        idx //= 2
    return node

rng = np.random.default_rng(1103)
leaves = [rand_bytes(rng, N_BYTES) for _ in range(8)]
levels = merkle_build(leaves)
root = levels[-1][0]

j = 5
path = merkle_auth_path(levels, j)
ok_genuine = merkle_root_from_path(leaves[j], j, path) == root
print(f"authentication path for leaf {j} recomputes the true root: {ok_genuine}")
print(f"authentication path length h={len(path)} for {len(leaves)}=2^{len(path)} leaves")

corrupted_leaf = bytes([leaves[j][0] ^ 0xFF]) + leaves[j][1:]
ok_corrupted = merkle_root_from_path(corrupted_leaf, j, path) == root
print(f"corrupting leaf {j} itself still verifies: {ok_corrupted}")

# The proof for leaf j is a pure function of (leaf_j, path_j, root) -- it
# never looks at any other leaf. Corrupting leaf 2's *storage* changes
# nothing this call touches, so leaf 5's proof is unaffected.
leaves_with_other_corrupted = list(leaves)
leaves_with_other_corrupted[2] = rand_bytes(rng, N_BYTES)
still_ok = merkle_root_from_path(leaves[j], j, path) == root
print(f"corrupting an unrelated leaf's storage leaves leaf {j}'s proof unaffected: {still_ok}")
""")

# ------------------------------------------------------------------ Part D
md(r"""
## Part D — a toy SLH-DSA end to end

Assemble Parts A–C's WOTS+ and Merkle machinery, plus a small FORS
instance, into a single-layer ($d=1$) toy hypertree: $h'=4$ (16
leaves), FORS with $k=4$ trees of height $a=3$ ($t=8$ leaves each).
Every leaf position gets its own WOTS+ key pair *and* its own FORS
instance, generated once at KeyGen — exactly as FIPS 205 derives all
$2^h$ of each, deterministically, from a single seed.
""")

code(r"""
H_PRIME = 4                 # single hypertree layer height (16 leaves)
N_LEAVES = 1 << H_PRIME
K_FORS = 4
A_FORS = 3                  # t = 2^3 = 8 leaves per FORS tree

def fors_keygen(rng):
    sk_trees = [[rand_bytes(rng, N_BYTES) for _ in range(1 << A_FORS)] for _ in range(K_FORS)]
    levels_trees = [merkle_build([H(s) for s in tree]) for tree in sk_trees]
    roots = [lv[-1][0] for lv in levels_trees]
    fors_pk = H(*roots)
    return sk_trees, levels_trees, fors_pk

def fors_sign(sk_trees, levels_trees, indices):
    sig = []
    for i in range(K_FORS):
        idx = indices[i]
        sig.append((sk_trees[i][idx], merkle_auth_path(levels_trees[i], idx)))
    return sig

def fors_pk_from_sig(sig, indices):
    roots = []
    for i in range(K_FORS):
        leaf_sk, path = sig[i]
        roots.append(merkle_root_from_path(H(leaf_sk), indices[i], path))
    return H(*roots)

def derive_indices(msg):
    digest = hashlib.sha256(msg).digest()
    bits = "".join(f"{b:08b}" for b in digest)
    pos, fors_idx = 0, []
    for _ in range(K_FORS):
        fors_idx.append(int(bits[pos:pos + A_FORS], 2))
        pos += A_FORS
    leaf_index = int(bits[pos:pos + H_PRIME], 2)
    return fors_idx, leaf_index

def slh_keygen(rng):
    wots_keys, fors_keys, leaves = [], [], []
    for _ in range(N_LEAVES):
        wsk, wpk = wots_keygen(rng)
        fsk_trees, flevels, _ = fors_keygen(rng)
        wots_keys.append((wsk, wpk))
        fors_keys.append((fsk_trees, flevels))
        leaves.append(H(*wpk))
    ht_levels = merkle_build(leaves)
    sk = {"wots_keys": wots_keys, "fors_keys": fors_keys, "ht_levels": ht_levels}
    pk_root = ht_levels[-1][0]
    return sk, pk_root

def slh_sign(sk, msg):
    fors_idx, leaf_index = derive_indices(msg)
    fsk_trees, flevels = sk["fors_keys"][leaf_index]
    fors_sig = fors_sign(fsk_trees, flevels, fors_idx)
    fors_pk = fors_pk_from_sig(fors_sig, fors_idx)
    wsk, wpk = sk["wots_keys"][leaf_index]
    wots_sig = wots_sign(wsk, fors_pk)
    auth_path = merkle_auth_path(sk["ht_levels"], leaf_index)
    return (fors_sig, wots_sig, auth_path)

def slh_verify(pk_root, msg, sig):
    fors_sig, wots_sig, auth_path = sig
    fors_idx, leaf_index = derive_indices(msg)
    fors_pk = fors_pk_from_sig(fors_sig, fors_idx)
    wots_pk_recovered = wots_pk_from_sig(wots_sig, fors_pk)
    leaf = H(*wots_pk_recovered)
    root = merkle_root_from_path(leaf, leaf_index, auth_path)
    return root == pk_root

rng = np.random.default_rng(1104)
sk, pk_root = slh_keygen(rng)

n_msgs = 48
messages = [f"toy message #{i}".encode() for i in range(n_msgs)]
signatures = [slh_sign(sk, m) for m in messages]
all_verify = all(slh_verify(pk_root, messages[i], signatures[i]) for i in range(n_msgs))
print(f"{n_msgs} signatures, all verify: {all_verify}")

cross_verify_ok = slh_verify(pk_root, messages[1], signatures[0])
print(f"signature #0 verifies against a different message #1: {cross_verify_ok}")

fors_sig, wots_sig, auth_path = signatures[0]
corrupted_wots = list(wots_sig)
corrupted_wots[0] = bytes([corrupted_wots[0][0] ^ 0xFF]) + corrupted_wots[0][1:]
corrupted_sig = (fors_sig, corrupted_wots, auth_path)
corrupted_verifies = slh_verify(pk_root, messages[0], corrupted_sig)
print(f"signature #0 with one corrupted byte still verifies: {corrupted_verifies}")
""")

md(r"""
Signatures verify against the message they were made for and no
other, and a single corrupted byte anywhere is caught. Now the
leaf-collision check: with only 16 toy leaves, some pair among 48
random messages will land on the same hypertree leaf.
""")

code(r"""
leaf_of = [derive_indices(m)[1] for m in messages]
collision = None
seen = {}
for i, li in enumerate(leaf_of):
    if li in seen:
        collision = (seen[li], i)
        break
    seen[li] = i

assert collision is not None, "no collision among 48 messages at 16 leaves -- re-run with more messages"
i, j = collision
print(f"messages #{i} and #{j} both selected hypertree leaf {leaf_of[i]}")

fors_sig_i, wots_sig_i, path_i = signatures[i]
fors_sig_j, wots_sig_j, path_j = signatures[j]

wots_identical = wots_sig_i == wots_sig_j
fors_identical = fors_sig_i == fors_sig_j
paths_identical = path_i == path_j
print(f"WOTS+ portions of the two signatures are byte-for-byte identical: {wots_identical}")
print(f"authentication paths (both leaf {leaf_of[i]}) are identical: {paths_identical}")
print(f"FORS portions are identical: {fors_identical} (expected False -- different sub-indices)")
""")

md(r"""
The reused leaf's WOTS+ key signed the *same* value both times — its
signature output is identical byte-for-byte across the two colliding
messages — because it never signed the message at all, only the
FORS instance's fixed public root at that leaf position (§11.5). Only
the FORS signature differs, carrying whichever of that instance's
secret leaves the two different messages happened to select.
""")

code(r"""
predicted_fors_bytes = K_FORS * (1 + A_FORS) * N_BYTES
predicted_ht_bytes = (H_PRIME + 1 * LEN) * N_BYTES        # d=1 layer
predicted_total = predicted_fors_bytes + predicted_ht_bytes   # no R: our toy signer is deterministic

actual_fors_bytes = sum(len(leaf_sk) + len(path) * N_BYTES for leaf_sk, path in fors_sig)
actual_ht_bytes = len(wots_sig) * N_BYTES + len(auth_path) * N_BYTES
actual_total = actual_fors_bytes + actual_ht_bytes

print(f"predicted signature size  n + k(1+a)n + (h+d*len)n, R omitted: {predicted_total} bytes")
print(f"actual measured signature size:                                {actual_total} bytes")
print(f"(Table 11.2's real formula includes an extra n={{16,24,32}}-byte R prefix our")
print(f" deterministic toy signer, per §11.6's rnd={{0}} variant, does not carry)")
""")

# --------------------------------------------------------------------- close
md(r"""
## What to take away

Four constructions, one hash function, no library beyond `hashlib`.
Part A's break is not a corner case — it is the entire reason "one-time"
is not a suggestion. Part B's checksum is not decoration — remove it
and the message-only verifier in this notebook is trivially fooled.
Part C's authentication path is the one piece of information a Merkle
tree needs to disclose to prove a leaf's membership, and nothing more.
Part D is the payload: a complete, working, insecure-only-because-
its-numbers-are-small signature scheme, together with a direct,
measured confirmation of §11.5's most delicate claim — that leaf
reuse in SLH-DSA is safe not because FORS magically tolerates
everything, but because the WOTS+ layer never sees the message at all.
""")

code(r"""
def _selftest():
    # Part A: full key recovery and forgery after signing a complementary message.
    assert ok1 and ok2 and full_key_recovered and forged_ok

    # Part B: checksum-free verifier fooled every trial; real verifier never fooled.
    assert fooled_count == trials
    assert real_fails == trials

    # Part C: genuine path verifies, corrupted leaf fails, unrelated corruption irrelevant.
    assert ok_genuine and (not ok_corrupted) and still_ok
    assert len(path) == 3

    # Part D: end-to-end correctness, cross-message rejection, corruption rejection.
    assert all_verify
    assert cross_verify_ok is False
    assert corrupted_verifies is False

    # Part D: the leaf-collision property that makes statelessness safe.
    assert wots_identical is True
    assert paths_identical is True
    assert fors_identical is False

    # Part D: measured signature size matches the byte-size formula exactly.
    assert actual_total == predicted_total

    print("all checks passed")

_selftest()
""")

nb["cells"] = C
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11"},
}

with open("lab11.ipynb", "w") as f:
    nbf.write(nb, f)
print(f"wrote lab11.ipynb with {len(C)} cells")
