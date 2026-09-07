# Applied AI Agent Project

Semester project for **IC-6200 — Artificial Intelligence**, Escuela de Ingeniería en Computación, Instituto Tecnológico de Costa Rica. II Semester, 2026.

An applied AI solution built under research methodology, consumed by an intelligent agent in a verifiable way. The project runs across 16 weeks in three mandatory stages.

---

## Status

| Stage | Deliverable | Deadline | Weight | Status |
| --- | --- | --- | --- | --- |
| **Stage 1** | State of the art, problem analysis, preliminary IEEE paper | 06/09/2026 | 30% | In progress |
| **Stage 2** | Methodological workbook: pipeline, baselines, model, ablations | Week 10 | 45% | Not started |
| **Stage 3** | Functional intelligent agent + final paper | Week 16 | 25% | Not started |

**Track:** Track A — Classical machine learning on tabular data.
**Topic:** Estimating Win Probability from Game State in the Pokémon Trading Card Game: A Tabular Classification Study with Explicit Data Leakage Control.
**Dataset / Environment:** PTCG AI Battle Challenge replay dataset.

---

## Team

| Member | ID | Review axis |
| --- | --- | --- |
| Adriel S. Chaves Salazar | 2021031465 | Axis B — techniques of the selected track |
| Daniel Duarte Cordero | 2022012866 | Axis A — problem domain |
| Sebastián Hernández Bonilla | 2022093651 | Axis C — dataset / environment |

**Professor:** Kenneth Roberto Obando Rodríguez

Individual authorship is determined by commit history. Shared files count as shared authorship.

---

## Repository Guide

| Path | Contents |
| --- | --- |
| `docx/00GitRules/` | Branching, commit and PR conventions |
| `docx/01AgileTaskDivision/` | Sprint planning and backlog |
| `docx/02Papers/` | Reviewed literature per member, and the LaTeX source of the paper |
| `docx/02Papers/00MainPaperLatex/` | IEEE paper: `MainPaper.tex`, sections, bibliography |
| `docx/03Evidence/` | Meeting notes, agreements, milestones, and the `AI_USAGE.md` declarations — raw material for the work journal |

Some folder carries a `WhatThisContains.md` describing its purpose.

---

## Building the Paper

Requires a TeX distribution with `IEEEtran` (MiKTeX, TeX Live) and `latexmk`.

```bash
cd docx/02Papers/00MainPaperLatex
latexmk -C
latexmk -pdf MainPaper.tex

```

Output: MainPaper.pdf.

To verify no placeholders remain, redefine the `\todo` macro in `preamble.tex` as `\newcommand{\todo}[1]{}` and recompile — any section that renders empty is unfinished.

---

## Building the Work Journal

```bash
cd docx/02Papers/00WorkJournalLatex
latexmk -C
latexmk -pdf WorkJournal.tex

```

---

## Reproducing the Experiments

> Applies from Stage 2 onward. Not yet available.

[TO BE COMPLETED: environment setup, dependency installation, dataset download, and the exact command that reproduces each reported number.]

**Reproducibility contract.** Every reported result must be reproducible by a third party following this section alone, without contacting the team. Seeds are fixed and committed. Configurations are stored, not passed as ad-hoc flags. Raw data is never committed — only the instructions to obtain it.

---

## Conventions

* **Git:** See `docx/00GitRules/CodeControl.md`. Three branch levels: `master` → `stage<N>` → `<NN><IssueName>`. PR for every branch change; approval required only for merges into `master`.
* **Bibliography:** BibTeX only, key format `author_keyword_year`. Peer-reviewed journal or conference sources; a DOI must resolve and its content must match what is attributed to it before an entry is committed.
* **Documentation:** Markdown inside the repository. The paper is the deliverable; the Markdown is the working record.

---

## License

MIT. See `LICENSE`.

The license covers this repository's own code and documentation. It does not extend to third-party datasets, environments, or the PDFs of reviewed papers stored under `docx/02Papers/`, each of which retains its original license and terms.
