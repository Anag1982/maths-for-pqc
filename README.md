# Maths for Post-Quantum Cryptography — companion labs

Companion Jupyter notebooks for *Maths for Post-Quantum Cryptography*
(Mathematics for Everything, Book 4), by Avishek Nag, School of Computer Science, University College Dublin.

This repository holds the **labs only** — the runnable code referenced from
each chapter. The book text itself is not here.

| Chapter | Lab | Needs |
|---|---|---|
| 1 — What Quantum Computing Actually Breaks | [`ch01/lab01.ipynb`](ch01/lab01.ipynb) | numpy, matplotlib |
| 2 — Modular Arithmetic and Finite Fields | [`ch02/lab02.ipynb`](ch02/lab02.ipynb) | numpy, matplotlib |
| 3 — Polynomial Rings | [`ch03/lab03.ipynb`](ch03/lab03.ipynb) | numpy, matplotlib |
| 4 — The Number-Theoretic Transform | [`ch04/lab04.ipynb`](ch04/lab04.ipynb) | numpy, matplotlib |
| 5 — Lattices | [`ch05/lab05.ipynb`](ch05/lab05.ipynb) | numpy, matplotlib |
| 6 — Hard Problems | [`ch06/lab06.ipynb`](ch06/lab06.ipynb) | numpy, matplotlib |
| 7 — SIS and LWE | [`ch07/lab07.ipynb`](ch07/lab07.ipynb) | numpy, matplotlib |
| 8 — How Hard Is It Really? | [`ch08/lab08.ipynb`](ch08/lab08.ipynb) | numpy, matplotlib |
| 9 — FIPS 203: ML-KEM | [`ch09/lab09.ipynb`](ch09/lab09.ipynb) | numpy, matplotlib, mpmath |
| 10 — FIPS 204: ML-DSA | [`ch10/lab10.ipynb`](ch10/lab10.ipynb) | numpy, matplotlib |
| 11 — FIPS 205: SLH-DSA | [`ch11/lab11.ipynb`](ch11/lab11.ipynb) | numpy |
| 12 — FN-DSA / FALCON | [`ch12/lab12.ipynb`](ch12/lab12.ipynb) | numpy, sympy |
| 13 — Codes: HQC and Classic McEliece | [`ch13/lab13.ipynb`](ch13/lab13.ipynb) | numpy |
| 14 — Isogenies: A Cautionary Tale | [`ch14/lab14.ipynb`](ch14/lab14.ipynb) | — |
| 15 — Migration Mathematics | [`ch15/lab15.ipynb`](ch15/lab15.ipynb) | — |
| 16 — The On-Ramp | [`ch16/lab16.ipynb`](ch16/lab16.ipynb) | — |

Each chapter is self-contained: its own `requirements.txt`, its own
`README.md`, its own notebook. A chapter never depends on an earlier
chapter's code — copy-paste a single `chXX/` folder and it runs.

## Quickstart

```bash
git clone https://github.com/<you>/<repo>.git
cd <repo>/ch01
pip install -r requirements.txt
jupyter lab lab01.ipynb
```

Or open any notebook directly on GitHub — every notebook in this repo is
committed **already executed**, so figures and output render without running
anything.

## How the notebooks are built

Every `labNN.ipynb` is generated from `build_labNN.py`, not hand-edited. This
keeps the notebook diffable (`nbdiff`-friendly, and plain `git diff` on the
build script is actually readable) and makes it trivial to regenerate after a
correction:

```bash
cd chNN/
python3 build_labNN.py                                    # rewrites labNN.ipynb
python3 -m jupyter nbconvert --to notebook --execute \
    --inplace --ExecutePreprocessor.timeout=300 labNN.ipynb   # runs it, embeds outputs
```

If you send a pull request, edit the `build_labNN.py` and regenerate — please
don't hand-edit the `.ipynb` directly, the diff becomes unreadable.

## Continuous integration

[`.github/workflows/notebooks.yml`](.github/workflows/notebooks.yml) executes
every chapter's notebook headlessly on every push and pull request, so a
library update (a numpy release, a matplotlib API change) that breaks a lab
is caught immediately rather than discovered by a reader. Each notebook ends
with a `_selftest()` cell that asserts every numerical claim made in the
corresponding chapter — if a fact in the book is wrong, CI is designed to
fail, not just the plot to look odd.

## Errata

Corrections found while building these labs sometimes catch errors in the
printed book before press time — see [`ERRATA.md`](ERRATA.md). If you find a
mismatch between a notebook and the book, please open an issue; a repository
that runs the exact claims in a cryptography textbook is only useful if it
stays honest about disagreements between the two.

## Standards status

Several claims in this series are anchored to standards that were still
moving as of writing (FN-DSA/FIPS 206, HQC finalisation, the NIST round-3
signature portfolio). A maintained, dated snapshot is at
<https://mathsforeverything.com/pqc/standards>.

## License

Code in this repository (notebooks, build scripts) is released under the MIT
License — see [`LICENSE`](LICENSE). This covers the *code*; it does not grant
any licence to the text of the book itself, which is © Avishek Nag, all
rights reserved, and is not reproduced here beyond the section headers and
exercise numbers needed to navigate between the two.

## Citing

```bibtex
@book{nag2027pqc,
  title     = {Maths for Post-Quantum Cryptography},
  subtitle  = {Lattices, Learning With Errors and the NIST Standards},
  author    = {Nag, Avishek},
  series    = {Mathematics for Everything},
  number    = {4},
  year      = {2027},
  publisher = {self-published},
  note      = {Companion code: \url{https://github.com/<you>/<repo>}}
}
```
