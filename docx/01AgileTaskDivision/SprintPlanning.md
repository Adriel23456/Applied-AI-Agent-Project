# Agile Sprint Planning — Applied AI Agent Project (CE-IA, TEC)

**Repository:** `Applied-AI-Agent-Project`
**Team:** Adriel S. Chaves Salazar (AC) · Daniel Duarte Cordero (DD) · Sebastián Hernández Bonilla (SH)
**Project weight:** 25 % of the final grade · 3 mandatory stages

---

## Calendar Overview

| Sprint | Dates | Focus | Epic branch | Weight |
|---|---|---|---|---|
| **Sprint 1 — Stage 1** | Fri 21/08 – Wed 27/08 (7 days) | State of the art, problem analysis, proposed design, preliminary IEEE/ACM paper | `stage1` | 30 % |
| **Sprint 2 — Stage 2** | TBD (Week 10) | Modeling and evaluation, methodological workbook (not the paper) | `stage2` | 45 % |
| **Sprint 3 — Stage 3** | TBD (Week 16) | Functional intelligent agent + final paper | `stage3` | 25 % |

**Stage 1 delivery: Wednesday 27/08.**
**Content freeze: Tuesday 26/08, end of day.** Day 7 is compilation, proofreading and submission only.

Sprints 2 and 3 are planned at the retrospective of the preceding sprint.

---

## Sprint 1 — Stage 1 (21/08 – 27/08)

### Sprint Goal
Deliver a preliminary IEEE/ACM paper with **Introduction**, **Related Work** across the three mandatory axes, and **Proposed Methodology**, backed by a reproducible repository, ≥ 21 verified peer-reviewed references, the mandatory comparative table, an explicit gap statement, a declared literature baseline, and the AI usage declaration.

### Sprint Backlog — 4 branches

| # | Branch | Owner (lead) | Window | Closes |
|---|---|---|---|---|
| 00 | `00TrackConfirmation` | AC | Day 1 (21/08) | Track approved, repo operational, search protocol defined |
| 01 | `01LiteratureReview` | SH | Days 2–3 (22–23/08) | 21 papers, three axes, comparative table, gaps, literature baseline |
| 02 | `02TechnicalDesign` | AC | Days 4–5 (24–25/08) | Track technical analysis, problem formalization, experimental protocol, baseline plan, risks, ethics |
| 03 | `03PaperAndDelivery` | DD | Days 6–7 (26–27/08) | Paper assembled, AI declaration, evidence traced, reproducibility verified, submitted |

Everyone commits inside every branch — the lead owns the merge and the PR, not the whole content.

---

## `00TrackConfirmation` — Day 1 (Fri 21/08)

**Goal:** unblock the sprint. The track must be approved and every working convention must exist before anyone writes a single paragraph of the paper.

**Work items**

| ID | Work item | Owner | Effort |
|---|---|---|---|
| #001 | Write the track/topic approval request: problem, chosen track, dataset or environment, technical rationale for the choice, and expected contribution. Send it to the professor and archive the sent message and the reply | AC | 0.4 d |
| #002 | Define the fallback topic (one paragraph) so a rejection costs at most half a day of Axis B/C rework | AC | 0.2 d |
| #003 | Bootstrap the repository: license, ignore rules, dependency manifest, and the two governance documents (git rules + this sprint plan) | AC | 0.3 d |
| #004 | Set up shared bibliography tooling (Zotero group with Better BibTeX export, or a shared `.bib`), and fix the citation key convention `author_keyword_year` | SH | 0.3 d |
| #005 | Write the **literature search protocol**: databases queried, exact search strings, inclusion/exclusion criteria, quality bar, and how a candidate becomes an accepted reference | SH | 0.4 d |
| #006 | Set up the paper build: IEEEtran or `acmart` class, section skeleton, and a verified end-to-end PDF compilation with empty content | DD | 0.4 d |
| #007 | Locate and open the dataset or environment. Confirm it downloads/installs and runs on Colab Pro. Record version, size, and license | DD | 0.3 d |

**Files this branch must produce**

| File type | Content |
|---|---|
| Markdown — git rules | Branching, commits, PR conventions (companion document) |
| Markdown — sprint planning | This document |
| Markdown — README | Project description, team, track, how to reproduce |
| Markdown — search protocol | Databases, queries, inclusion criteria, quality bar |
| Markdown — data/environment note | Origin, version, size, license, download or install instructions. **Never the data itself** |
| `LICENSE` | MIT |
| `.gitignore` | Python, Jupyter, LaTeX artifacts, datasets, checkpoints, virtual envs |
| `requirements.txt` | Pinned dependencies |
| `.tex` — main + empty sections | Compilable paper skeleton |
| `.bib` | Empty or seeded, with the key convention documented |
| Evidence — image/PDF export | Screenshot or export of the approval request and the professor's reply |

**Done when:** the professor's approval is archived in the repo, all three members can push, the PDF compiles, and the dataset/environment has been opened at least once.

**Search sources to declare:** TEC subscribed electronic resources · Scopus · Web of Science · IEEE Xplore · ACM Digital Library · Consensus · Semantic Scholar · Connected Papers · Papers with Code.

---

## `01LiteratureReview` — Days 2–3 (Sat 22/08 – Sun 23/08)

**Goal:** produce the whole evidentiary base of the paper — the three axes, the table that forces the comparison, the gap the project attacks, and the number the project must beat.

**Work items**

| ID | Work item | Owner | Effort |
|---|---|---|---|
| #010 | **Axis A — problem/domain.** Collect and read ≥ 7 peer-reviewed papers. Per paper: approach, reported result, limitation. Close with an explicit answer to: which approaches dominate, what is considered solved, what remains open | DD | 1.0 d |
| #011 | **Axis B — techniques of our track.** Collect and read ≥ 7 peer-reviewed papers. Per paper: strengths, limits, assumptions under which the method works. Close with the **technical justification of the track backed by literature, not opinion** | AC | 1.0 d |
| #012 | **Axis C — dataset/environment.** Collect and read ≥ 7 peer-reviewed papers that use it. Per paper: metric, evaluation protocol, reported result. Close with the documented known problems: bias, leakage, size, representativeness | SH | 1.0 d |
| #013 | Build the **mandatory comparative table** and cross-check every row against the axis notes — no row without a verified source | SH | 0.4 d |
| #014 | Write the **gap section**: name the concrete gaps found, state which ones this project addresses, and state which ones stay out of scope and why | SH | 0.3 d |
| #015 | Declare the **literature baseline**: the best published result on our dataset/environment with our chosen metric (or a defensible range), the number we aim to match or beat, and the protocol differences that would make a direct comparison unfair | DD | 0.4 d |
| #016 | Formalize the **research question** (explicit, refutable, answerable with evidence by end of semester), the working hypothesis, general and specific objectives, and the **justified** primary metric | AC | 0.5 d |
| #017 | Verification pass: resolve every DOI and confirm each cited claim matches the source content before the entry enters the `.bib` | DD | 0.3 d |

**Files this branch must produce**

| File type | Content |
|---|---|
| Markdown — one note file per axis (3 files) | Per-paper summary, technique, result, limitation, `verified: yes/no`, and the axis-closing synthesis |
| Markdown — comparative table | Working version of the table, one row per reviewed work |
| Markdown — gaps | Gaps found, gaps addressed, gaps out of scope |
| Markdown — literature baseline | Target number, metric, source, protocol caveats blocking fair comparison |
| Markdown — problem statement | Research question, hypothesis, objectives, contribution, metric justification |
| `.bib` — populated | ≥ 21 verified entries, all cited from the paper |
| `.tex` — comparative table | The table rendered in the paper's format |

**Mandatory table columns — no substitutions:**

```
| Reference | Year | Technique | Dataset/Environment | Main metric | Reported result | Identified limitation |
```

**Review minimum requirements — enforced before merge**

| Requirement | Rule |
|---|---|
| Volume | ≥ 7 papers **per member** → ≥ 21 total |
| Venue | Peer-reviewed journal or conference only |
| Recency | Majority from the last 5 years |
| Preprints | arXiv **not accepted** unless relevance or novelty justifies it — ask the professor first and mark it as a preprint in the text |
| Ownership | Each member must be able to **defend their own 7 papers** orally |
| Verifiability | DOI resolves **and** the content matches what is attributed to it |
| Management | BibTeX only — no loose references, no pasted links |

> If the dataset is proprietary or has no prior literature, #015 is replaced by: review analogous datasets in the same domain and justify why they are or are not comparable.

**Done when:** ≥ 21 verified entries exist, every one has notes in its axis file, the table is complete, and the target number is written down.

---

## `02TechnicalDesign` — Days 4–5 (Mon 24/08 – Tue 25/08)

**Goal:** turn the approved track into a defensible design — formalized problem, analyzed data or environment, and an experimental protocol a third party could execute without asking us anything.

**Work items**

| ID | Work item | Owner | Effort |
|---|---|---|---|
| #020 | **Track-specific technical analysis** (run only the block matching the approved track — see table below), with fixed seeds and exported figures | AC + SH | 1.2 d |
| #021 | **Problem formalization** with mathematical formulation where applicable, and the planned pipeline end to end | AC | 0.5 d |
| #022 | **Experimental protocol**: train/validation/test splits with strict separation (temporal split if the data is time-dependent), validation strategy, metrics — each choice justified against the alternatives it beat | AC | 0.5 d |
| #023 | **Explicit data-leakage prevention**: name every leakage vector considered and the concrete measure taken against each | SH | 0.3 d |
| #024 | **Baseline plan**: ≥ 2 internal baselines (one trivial, one competitive classical) plus the literature baseline from #015 as the third reference. Include the reproducibility contract: fixed seeds, saved configs, run logs, comparable tables | DD | 0.4 d |
| #025 | **Risk register**: technical, computational and schedule risks, each with a mitigation and a trigger condition | DD | 0.3 d |
| #026 | **Preliminary ethical considerations**: sensitive data, bias risk, and the mitigation planned before training. Deployment ethics is deferred to Stage 3 | DD | 0.3 d |

**Track-specific analysis required by #020**

| Track | Required content |
|---|---|
| **A — Classical ML (tabular)** | Deep EDA, data dictionary, quality assessment, justified imputation strategy, outlier detection, class imbalance analysis, explicit leakage prevention |
| **B — Deep Learning (NLP/vision)** | Corpus or image-set analysis (distributions, resolutions, documented biases), augmentation strategy, tokenization/preprocessing, hardware and memory considerations |
| **C — Reinforcement Learning** | Formal MDP: state space, action space, transition dynamics, **justified reward function design**, discount factor, episode termination |

**Files this branch must produce**

| File type | Content |
|---|---|
| `.ipynb` notebook | EDA, corpus analysis, or environment smoke test — run with fixed seeds, outputs committed |
| Markdown — track analysis | The block above, written up with references to the exported figures |
| Markdown — experimental protocol | Splits, validation, metrics, justification, leakage prevention |
| Markdown — baseline plan | Internal baselines, literature baseline, reproducibility contract |
| Markdown — risk register | Risk, likelihood, impact, mitigation, trigger |
| Markdown — ethics | Risks identified and mitigation planned |
| `.yaml` config | Fixed seeds, split definitions, and any environment or preprocessing parameters |
| Python module(s) | Environment wrapper or data-loading stub, only if the analysis needed one |
| Evidence — figure exports (PNG/PDF) | Every figure used in the paper, exported from the notebook |
| `.tex` — methodology section | Formalization, pipeline, protocol, baseline plan, risks |

**Done when:** every key decision in this branch (metric, split, reward function, augmentation, architecture) has a written justification. Unjustified critical decisions cost −5 points each, up to −15.

---

## `03PaperAndDelivery` — Days 6–7 (Wed 26/08 – Thu 27/08)

**Goal:** assemble the deliverable, prove every claim, and ship. Day 6 is writing and verification; Day 7 touches nothing but formatting and submission.

**Work items**

| ID | Work item | Owner | Effort |
|---|---|---|---|
| #030 | Write the **Introduction**: context, relevance, explicit research question, hypothesis, objectives with expected contribution, document structure | DD | 0.4 d |
| #031 | Write **Related Work** organized in the three axes, embedding the comparative table and closing with the gap subsection | SH | 0.5 d |
| #032 | Write the title, the **explicitly labelled preliminary abstract** (problem, motivation, proposed approach, **no results of any kind**), and the keywords | DD | 0.2 d |
| #033 | Fill the **AI usage declaration**: one block per member, mirrored into the paper as its own section | AC + DD + SH | 0.3 d |
| #034 | **Evidence pass**: every figure and table in the paper traces to a committed artifact, and every performance claim traces to a run log or a cited paper | SH | 0.3 d |
| #035 | **Reproducibility pass**: freeze dependencies, confirm no installed dependencies or datasets are committed, write execution instructions a third party can follow without asking us anything, and run a clean-clone test on a fresh Colab runtime | AC | 0.4 d |
| #036 | Final read-through of the compiled PDF: formatting, figure and table numbering, citation style, section ordering | DD | 0.3 d |
| #037 | Merge `stage1` into `master` with 1 approval, tag the release, and submit on TecDigital | AC | 0.2 d |

**Files this branch must produce**

| File type | Content |
|---|---|
| `.tex` — introduction, related work, abstract, ethics, AI declaration sections | Final paper content |
| Markdown — AI usage declaration | One block per member (structure below) |
| Compiled PDF | The preliminary paper, IEEE or ACM format |
| Markdown — README update | Final reproduction instructions, verified by the clean-clone test |
| Markdown — retrospective | Filled at the end of Day 7 |

**AI usage declaration — required structure, one block per member**

```markdown
## <Member name>

### Tools used
- <tool + model/version>

### Where it was used
- <specific sections, files, or tasks>

### Purpose
- <e.g. candidate topic brainstorming, paragraph rephrasing, plotting snippet>

### What was manually verified afterwards
- <e.g. every DOI resolved manually in IEEE Xplore; every reported metric checked
   against the source PDF; every generated snippet executed and inspected>

### What was NOT AI-generated
- <e.g. the research question, the MDP formulation, all experimental results>
```

> Declaring AI use carries **no penalty**. Hiding it aggravates any later finding.

**Submission checklist (TecDigital)**
- [ ] Repository link with commit history from all three members
- [ ] Source code without installed dependencies (`.venv`, `node_modules` excluded)
- [ ] Documentation in Markdown inside the repository
- [ ] AI usage declaration
- [ ] Preliminary paper PDF in IEEE or ACM format

---

## Ownership Summary

| Member | Owns | Axis |
|---|---|---|
| **Adriel S. Chaves Salazar** | `00TrackConfirmation`, `02TechnicalDesign` — approval, repo bootstrap, problem formalization, track technical analysis, experimental protocol | B — techniques |
| **Daniel Duarte Cordero** | `03PaperAndDelivery` — paper build, introduction, abstract, literature baseline, baseline plan, risks, ethics, reference verification | A — problem/domain |
| **Sebastián Hernández Bonilla** | `01LiteratureReview` — search protocol, comparative table, gaps, dataset analysis, related work section, evidence pass | C — dataset/environment |

Individual authorship is graded from commits. Each member pushes their own work — nobody commits someone else's files.

---

## Penalty Guard — verified before the merge into `master`

| Penalty | Points | Guarded by |
|---|---|---|
| Confirmed data leakage | −15 | #023 |
| Absence of baselines | −10 | #024 |
| Unverifiable or unread references | −10 | #017 |
| Key decisions without technical justification | −5 each, max −15 | #016, #020, #021, #022 |
| Non-reproducible work | up to −10 | #035 |
| Late delivery | −5 per day | Content freeze 26/08 |

---

## Sprint 2 — Stage 2 (placeholder)

Planned at the Stage 1 retrospective. Scope: complete methodological cycle in a workbook (**not** the paper) — data pipeline, internal baselines, main model, ablations, experiment tracking, and comparable result tables against the three references.

## Sprint 3 — Stage 3 (placeholder)

Planned at the Stage 2 retrospective. Scope: functional intelligent agent consuming the model in a verifiable way, deployment ethics, and integration of Stage 2 results into the final paper.

---

## Stage 1 Retrospective — fill on 27/08

| Question | Answer |
|---|---|
| What went well? | |
| What blocked us? | |
| Which estimates were wrong, and by how much? | |
| What changes for Sprint 2? | |