# Errata

Corrections found while building the companion labs — some caught before the
book went to press, some after. Each entry names the chapter, what was wrong,
and what replaced it.

## Chapter 1 — What Quantum Computing Actually Breaks

**Success probability of the Shor factoring step.** An early draft stated the
two conditions (r even, a^(r/2) ≠ −1 mod N) hold with probability at least
3/4 for N with two distinct odd prime factors. Exhaustively enumerating the
units mod N in `ch01/lab01.ipynb` (`success_rate`) shows this is false: N = 21
and N = 33 both attain exactly 1/2. The correct bound is
1 − 2^−(m−1), where m is the number of distinct odd prime factors of N — see
Nielsen & Chuang, Theorem A4.13. Corrected in the printed text before press.

## Chapter 4 — The Number-Theoretic Transform

**§4.2's worked NTT example.** An early draft claimed the q=17, n=4, ψ=9
example gives f̂ = (6,5,3,15) for f(x)=1+2x+3x²+4x³. Direct evaluation in
`ch04/lab04.ipynb` (the `evaluate`/`fhat_worked` cell) shows this is wrong:
f(9) mod 17 = 16, not 6, and likewise for the second and third coordinates.
The correct value is f̂ = (16,11,13,15) — only the last coordinate happened
to match by coincidence. The inverse formula recovers f exactly from the
corrected value. Corrected in the printed text before press.

---

Found a mismatch between a notebook and the printed book? Please open an
issue with the chapter, the claim, and (ideally) a short script that shows
the discrepancy — that is exactly how the entry above was found.
