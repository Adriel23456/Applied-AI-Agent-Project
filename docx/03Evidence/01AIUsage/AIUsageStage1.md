# Declaration of AI Tool Usage

**Project:** Game-State Win Probability Estimation in the Pokémon Trading Card Game
**Course:** IC-6200 — Artificial Intelligence, ITCR · II Semester 2026 · Track A
**Team:** Adriel S. Chaves Salazar · Daniel Duarte Cordero · Sebastián Hernández Bonilla
**Covers:** Stage 1 — state of the art, problem analysis and design
**Last updated:** [TO BE COMPLETED: YYYY-MM-DD]

This declaration is mandatory in every delivery. Declaring AI use carries no penalty; concealing it aggravates any later finding. Stages 2 and 3 append their own sections rather than overwriting this one, so the record accumulates across the semester.

---

## 1. Tools used

| Tool | Purpose in this project |
|---|---|
| **Claude (Anthropic)** | Topic exploration and scoping; structuring the research question, hypotheses and objectives; drafting and reviewing project documentation; interpreting how the Stage 1 requirements map onto the paper structure |
| **Consensus** | Literature discovery — locating peer-reviewed work on win prediction from game state, calibration of probabilistic classifiers, and leakage in grouped data |

Both tools were used as **search and drafting assistants**. Neither was used to produce results, to decide the research question, or to select the final set of references without human review.

---

## 2. Where AI was used, and what was done manually afterwards

### 2.1 Topic scoping and framing

**What the tool did.** Claude was used across an extended exploratory conversation to examine candidate project directions before the team settled on this one. That conversation initially explored a reinforcement-learning direction (coverage path planning on unknown terrain) which was **abandoned**; the current Track A topic replaced it after the team's own reassessment and after the professor's feedback.

The tool contributed: sharpening the research question so it would be falsifiable, distinguishing the three review axes required by the course, and pressure-testing whether proposed differentiators against prior work were technically defensible or merely rhetorical.

**Manually verified.** The team read the professor's feedback directly and made the topic decision itself. Every framing claim that survived into the proposal was checked against the course statement and against the primary sources.

**Not AI-generated.** The choice of topic, the choice of track, the research question as finally stated, and the decision to abandon the RL direction.

### 2.2 Literature discovery

**What the tools did.** Consensus was used to surface candidate peer-reviewed work by topic. Claude was used to assess whether candidate papers actually supported the three axes, to flag which candidates were preprints rather than peer-reviewed publications, and to identify redundancy within the candidate set.

**Manually verified.** Every reference must have its DOI resolved by a team member and its content read before it enters `refs.bib`. The per-member `.bib` files carry an explicit `VERIFIED` / `UNVERIFIED` status comment on every entry; **an entry that is not marked VERIFIED does not appear in the paper.** As of this writing, 2 of 21 entries are verified and 19 are pending.

**Not AI-generated.** The final selection of the 21 papers, the axis assignment, and the reading distribution across team members — these were produced by the team.

**Explicitly not delegated.** No DOI, author list, venue or page range was accepted on a tool's assertion. Where metadata could not be confirmed against a primary source, the field is left as a placeholder rather than filled with a plausible guess.

### 2.3 Dataset assessment

**What the tool did.** Claude was used to discuss the implications of the dataset's structure — many correlated snapshots per episode, distribution drift across days, coexisting engine versions — and to reason about which of these constitute validity threats.

**Manually verified.** All quantitative statements about the dataset come from the team's own audit scripts, not from any tool. Figures such as the episode count, the snapshot count, the field-completeness rate, and the measured contamination under a random split are reproducible from `reports/audit_summary.md` and `reports/deep_probe.json` with a fixed seed.

**Not AI-generated.** The audit pipeline, its execution, and every number it produced.

### 2.4 Documentation and paper structure

**What the tool did.** Claude was used to draft and revise project documentation: the topic proposal, the reading-assignment documents, the repository conventions, and the interpretation of how the Stage 1 requirements (three axes, comparative table, gap identification, literature baseline, methodology) map onto sections of an IEEE-format paper.

**Manually verified.** Every technical claim in those documents was checked against the course statement or against a primary source. Passages that could not be substantiated were removed rather than softened.

**Not AI-generated.** The problem formalization, the feature dictionary, the leakage blacklist, the experimental protocol, the baseline ladder, and every result that will be reported.

---

## 3. Boundaries the team set

These hold regardless of which tool any member uses.

- **No reference enters the bibliography on a tool's word.** Every DOI is resolved manually and the source is read to confirm it says what we attribute to it. A reference cited without reading costs −10 points.
- **No technical decision is delegated.** The research question, the target definition, the split design, the metric choice, and the interpretation of results are the team's own reasoning. A tool may surface options; the team chooses and defends.
- **No result is generated.** Every number reported in the paper comes from code we wrote and ran.
- **Generated code is executed before it is committed.** Nothing is merged on the assumption that it works.
- **Preprints are marked as such.** Where a tool surfaced an arXiv-only work, it is either excluded from the 21 peer-reviewed papers or raised with the professor before inclusion.

---

## 4. Per-member declaration

Each member completes their own block before the delivery.

### Adriel S. Chaves Salazar
- **Tools used:** [TO BE COMPLETED]
- **Where:** [TO BE COMPLETED]
- **Purpose:** [TO BE COMPLETED]
- **Manually verified afterwards:** [TO BE COMPLETED]
- **Not AI-generated:** [TO BE COMPLETED]

### Daniel Duarte Cordero
- **Tools used:** [TO BE COMPLETED]
- **Where:** [TO BE COMPLETED]
- **Purpose:** [TO BE COMPLETED]
- **Manually verified afterwards:** [TO BE COMPLETED]
- **Not AI-generated:** [TO BE COMPLETED]

### Sebastián Hernández Bonilla
- **Tools used:** [TO BE COMPLETED]
- **Where:** [TO BE COMPLETED]
- **Purpose:** [TO BE COMPLETED]
- **Manually verified afterwards:** [TO BE COMPLETED]
- **Not AI-generated:** [TO BE COMPLETED]