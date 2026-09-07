# Agile Sprint Planning — Applied AI Agent Project (CE-IA, TEC)

**Repository:** `Applied-AI-Agent-Project`
**Team:** Adriel S. Chaves Salazar (AC) · Daniel Duarte Cordero (DD) · Sebastián Hernández Bonilla (SH)
**Project weight:** 25 % of the final grade · 3 mandatory stages

---

## Calendar Overview

| Sprint | Dates | Focus | Epic branch | Weight |
| --- | --- | --- | --- | --- |
| **Sprint 1 — Stage 1** | Fri 21/08 – Sun 06/09 (17 days) | State of the art, problem analysis, proposed design, preliminary IEEE/ACM paper | `stage1` | 30 % |
| **Sprint 2 — Stage 2** | TBD (Week 10) | Modeling and evaluation, methodological workbook (not the paper) | `stage2` | 45 % |
| **Sprint 3 — Stage 3** | TBD (Week 16) | Functional intelligent agent + final paper | `stage3` | 25 % |

**Stage 1 delivery: Sunday 06/09.**
**Content freeze: Saturday 05/09, end of day.** The final day is compilation, proofreading and submission only.

Sprints 2 and 3 are planned at the retrospective of the preceding sprint.

---

## Sprint 1 — Stage 1 (21/08 – 06/09)

### Sprint Goal

Deliver a preliminary IEEE/ACM paper with **Introduction**, **Related Work** across the three mandatory axes, and **Proposed Methodology**, backed by a reproducible repository, ≥ 21 verified peer-reviewed references, the mandatory comparative table, an explicit gap statement, a declared literature baseline, and the AI usage declaration.

### Sprint Backlog — 3 branches

| # | Branch | Owner (lead) | Window | Closes |
| --- | --- | --- | --- | --- |
| 00 | `00TrackConfirmation` | AC | Days (21-26/08) | Track approved, repo operational, search protocol defined |
| 01 | `01LiteratureReview` | SH | Days (27/08-05/09) | 21 papers, three axes, comparative table, gaps, literature baseline |
| 02 | `02PaperAndDelivery` | DD | Days (05–06/09) | Paper assembled, AI declaration, evidence traced, reproducibility verified, submitted |

Everyone commits inside every branch — the lead owns the merge and the PR, not the whole content.

---

## `00TrackConfirmation` — Days 1–6 (21/08 – 26/08)

**Goal:** Unblock the sprint and formalize the technical design. The track must be approved, every working convention must exist, and the problem must be formally defined with an experimental protocol before anyone writes the final paper.

**Work items**

| ID | Work item | Owner | Effort |
| --- | --- | --- | --- |
| #001 | Write the track/topic approval request: problem, chosen track, dataset/environment, technical rationale, and expected contribution. Send it to the professor and archive the reply | AC | 0.4 d |
| #002 | Define the fallback topic (one paragraph) so a rejection costs minimal rework | AC | 0.2 d |
| #003 | Bootstrap the repository: license, ignore rules, dependency manifest, and the two governance documents | AC | 0.3 d |
| #004 | Set up shared bibliography tooling (Zotero group/shared `.bib`), and fix the citation key convention | SH | 0.3 d |
| #005 | Write the **literature search protocol**: databases queried, search strings, criteria, and quality bar | SH | 0.4 d |
| #006 | Set up the paper build: IEEEtran/`acmart` class, skeleton, and verified end-to-end PDF compilation | DD | 0.4 d |
| #007 | Locate and open the dataset/environment. Confirm it runs on Colab Pro. Record version, size, and license | DD | 0.3 d |
| #008 | **Track-specific technical analysis** (run only the block matching the approved track), with fixed seeds and exported figures | AC + SH | 1.2 d |
| #009 | **Problem formalization** with mathematical formulation where applicable, and the planned pipeline | AC | 0.5 d |
| #010 | **Experimental protocol**: train/validation/test splits, validation strategy, metrics — all choices justified | AC | 0.5 d |

**Files this branch must produce**

| File type | Content |
| --- | --- |
| Markdown docs | Git rules, sprint planning, README, search protocol, data/environment note |
| Repo setup | `LICENSE`, `.gitignore`, `requirements.txt` |
| LaTeX setup | `.tex` main + empty sections, `.bib` empty/seeded |
| `.ipynb` notebook | EDA, corpus analysis, or environment smoke test (fixed seeds, outputs committed) |
| Evidence | Approval request export, figure exports (PNG/PDF) for the paper |

**Done when:** the professor's approval is archived, all three members can push, the PDF compiles, the dataset is opened, and all technical design decisions (metric, splits, augmentations) have written justifications.

---

## `01LiteratureReview` — Days 7–16 (27/08 – 05/09)

**Goal:** Produce the whole evidentiary base of the paper — the three axes, the table that forces the comparison, the gap the project attacks, and the number the project must beat.

**Work items**

| ID | Work item | Owner | Effort |
| --- | --- | --- | --- |
| #011 | **Axis A — problem/domain.** Collect and read ≥ 7 peer-reviewed papers. Identify dominating approaches and open issues | DD | 1.0 d |
| #012 | **Axis B — techniques of our track.** Collect and read ≥ 7 peer-reviewed papers. Close with track justification | AC | 1.0 d |
| #013 | **Axis C — dataset/environment.** Collect and read ≥ 7 peer-reviewed papers. Document known bias/leakage/size limits | SH | 1.0 d |
| #014 | Build the **mandatory comparative table** and cross-check every row — no row without a verified source | SH | 0.4 d |
| #015 | Write the **gap section**: name gaps found, gaps addressed, and gaps out of scope | SH | 0.3 d |
| #016 | Declare the **literature baseline**: the number we aim to match/beat and protocol differences blocking fair comparison | DD | 0.4 d |
| #017 | Formalize the **research question**, hypothesis, objectives, and justified primary metric | AC | 0.5 d |
| #018 | **Explicit data-leakage prevention**: name every leakage vector and concrete mitigation measure | SH | 0.3 d |
| #019 | Verification pass: resolve every DOI and confirm cited claims before they enter the `.bib` | DD | 0.3 d |

**Files this branch must produce**

| File type | Content |
| --- | --- |
| Markdown notes | One file per axis (3 files): summaries, results, synthesis |
| Markdown docs | Comparative table, gaps, literature baseline, problem statement, experimental/leakage protocols |
| `.bib` — populated | ≥ 21 verified entries, all cited from the paper |
| `.tex` | Comparative table rendered in the paper's format |

**Review minimum requirements — enforced before merge**

* ≥ 7 papers **per member** (≥ 21 total).
* Peer-reviewed journal or conference only (majority from last 5 years).
* arXiv **not accepted** unless relevance/novelty justifies it (requires professor approval).
* Each member must be able to **defend their own 7 papers** orally.

**Done when:** ≥ 21 verified entries exist, every one has notes in its axis file, the table is complete, and the target baseline is established.

---

## `02PaperAndDelivery` — Days 16–17 (05/09 – 06/09)

**Goal:** Assemble the deliverable, prove every claim, and ship. Day 16 is final writing and verification; Day 17 touches nothing but formatting and submission.

**Work items**

| ID | Work item | Owner | Effort |
| --- | --- | --- | --- |
| #020 | Write the **Introduction**: context, relevance, explicit research question, hypothesis, objectives | DD | 0.4 d |
| #021 | Write **Related Work** organized in the three axes, embedding the table and gap subsection | SH | 0.5 d |
| #022 | Write the title, **explicitly labelled preliminary abstract** (no results), and keywords | DD | 0.2 d |
| #023 | Write **Baseline Plan & Risks/Ethics**: internal baselines, risk register, and preliminary ethical considerations | DD | 0.7 d |
| #024 | Fill the **AI usage declaration**: one block per member, mirrored into the paper as a section | AC + DD + SH | 0.3 d |
| #025 | **Evidence pass**: every figure/table traces to an artifact, every performance claim traces to a log/paper | SH | 0.3 d |
| #026 | **Reproducibility pass**: freeze dependencies, test execution instructions via clean-clone on Colab | AC | 0.4 d |
| #027 | Final read-through of compiled PDF: formatting, numbering, citation style | DD | 0.3 d |
| #028 | Merge `stage1` into `master`, tag release, and submit on TecDigital | AC | 0.2 d |

**Files this branch must produce**

| File type | Content |
| --- | --- |
| `.tex` sections | Final paper content (introduction, related work, abstract, ethics, methodology, AI declaration) |
| Markdown docs | AI usage declaration (one block per member), updated README for reproduction, retrospective |
| Compiled PDF | The preliminary paper in IEEE or ACM format |

**Submission checklist (TecDigital)**

* [ ] Repository link with commit history from all three members
* [ ] Source code without installed dependencies
* [ ] Documentation in Markdown inside the repository
* [ ] AI usage declaration
* [ ] Preliminary paper PDF in IEEE or ACM format

---

## Ownership Summary

| Member | Owns | Axis |
| --- | --- | --- |
| **Adriel S. Chaves Salazar** | `00TrackConfirmation` — approval, repo bootstrap, problem formalization, track technical analysis, experimental protocol | B — techniques |
| **Daniel Duarte Cordero** | `02PaperAndDelivery` — paper build, introduction, abstract, literature baseline, baseline plan, risks, ethics, reference verification | A — problem/domain |
| **Sebastián Hernández Bonilla** | `01LiteratureReview` — search protocol, comparative table, gaps, dataset analysis, related work section, evidence pass | C — dataset/environment |

Individual authorship is graded from commits. Each member pushes their own work — nobody commits someone else's files.

---

## Penalty Guard — verified before the merge into `master`

| Penalty | Points | Guarded by |
| --- | --- | --- |
| Confirmed data leakage | −15 | #018 |
| Absence of baselines | −10 | #023 |
| Unverifiable or unread references | −10 | #019 |
| Key decisions without technical justification | −5 each, max −15 | #008, #009, #010, #017 |
| Non-reproducible work | up to −10 | #026 |
| Late delivery | −5 per day | Content freeze 05/09 |

---

## Sprint 2 — Stage 2 (placeholder)

Planned at the Stage 1 retrospective. Scope: complete methodological cycle in a workbook (**not** the paper) — data pipeline, internal baselines, main model, ablations, experiment tracking, and comparable result tables against the three references.

## Sprint 3 — Stage 3 (placeholder)

Planned at the Stage 2 retrospective. Scope: functional intelligent agent consuming the model in a verifiable way, deployment ethics, and integration of Stage 2 results into the final paper.