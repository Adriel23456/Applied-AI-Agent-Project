# Code Control — Applied AI Agent Project

**Repository:** `Applied-AI-Agent-Project`
**Team:** Adriel S. Chaves Salazar · Daniel Duarte Cordero · Sebastián Hernández Bonilla

---

## Branching Strategy

```
master
  └── stage1 | stage2 | stage3
        └── <NN><IssueName>
```

Three levels. No `develop/**`, no `release/**`, no personal branches.

---

## Branches

### `master`
- **Purpose:** delivered, graded state of the project. Never pushed to directly.
- **Receives PRs from:** `stage1`, `stage2`, `stage3` only.
- **Approval:** **1 approval required.** This is the only place approval is required.
- **Merge type:** merge commit — the stage history must survive.
- **Tagging:** every merge is tagged (`v1.0.0-stage1`, `v2.0.0-stage2`, `v3.0.0-stage3`).

### `stage1` / `stage2` / `stage3`
- **Purpose:** one branch per project stage (sprint / epic).
- **Receives PRs from:** issue branches only.
- **Approval:** **none.** Open the PR, merge once the work is done.
- **Lifetime:** lives until the stage is delivered, merges into `master`, then stays frozen — not deleted. It is the graded snapshot.
- **Never pushed to directly.**

### Issue branches — `<NN><IssueName>`
- **Purpose:** one branch per backlog item in `SprintPlanning.md`. Each one is a **body of work**, not a chore — it bundles the research, the writing and the artifacts that close a single sprint goal.
- **Naming:** exactly the backlog item name, two-digit prefix, PascalCase, no separators.
- **Direct pushes:** allowed. This is the working branch.
- **PR target:** the stage branch that owns it.
- **Deleted after merge.**

---

## Flow Summary

```
01LiteratureReview
    │
    │  PR → no approval needed
    ▼
stage1
    │
    │  PR → 1 approval required
    ▼
master  ← tagged v1.0.0-stage1
```

---

## Rules at a Glance

| Branch | Push directly? | PR target | Approval? | Tagged? |
|---|---|---|---|---|
| `master` | ❌ No | — | — | ✅ Yes |
| `stage1` / `stage2` / `stage3` | ❌ No | `master` | ✅ 1 approval | ❌ No |
| `<NN><IssueName>` | ✅ Yes | `stage<N>` | ❌ No | ❌ No |

---

## Naming Convention

### Stage branches

```
stage1
stage2
stage3
```

### Issue branches

`<two-digit number><PascalCaseName>`, matching the backlog item character for character.

Stage 1 branch set:

```
00TrackConfirmation
01LiteratureReview
02TechnicalDesign
03PaperAndDelivery
```

**Rules:**
- Two-digit zero-padded number, always.
- No spaces, hyphens, underscores or slashes inside the name.
- A branch that would need `And` twice in its name is two branches. A branch that closes in under half a day is not a branch — fold it into the one that owns it.
- Repo bootstrap, tooling setup and conventions are **not** branches of their own. They belong to `00TrackConfirmation`.

---

## Issue Traceability

> **Commits do NOT reference issue IDs. Pull Requests DO.**

- **Commits** describe the change: type, scope, what and why. No `Refs #` / `Closes #` footers, no issue numbers.
- **Pull Requests** carry traceability: the issue IDs go in the PR **title** and in the PR **description**.
- One issue branch bundles several work items, so its PR closes several IDs — list every one of them.

---

## Commit Message Convention

Conventional Commits:

```
<type>(<scope>): <short summary>

<optional body — what & why, not how>
```

### Types

| Type | Use for |
|---|---|
| `docs` | Paper sections, Markdown documents, README — most of Stage 1 |
| `refs` | Adding, correcting or verifying BibTeX entries |
| `feat` | New code capability (pipeline, environment wrapper, agent tool) |
| `fix` | Bug fix in code, or a factual correction in a document |
| `exp` | Experiment run, config, or logged result |
| `data` | Download scripts, data dictionary, preprocessing definitions |
| `refactor` | Restructuring with no behavior change |
| `test` | Adding or fixing tests |
| `build` | Dependencies, LaTeX build setup |
| `ci` | CI configuration |
| `chore` | Misc maintenance |
| `style` | Formatting only |

### Scopes

`paper`, `intro`, `related`, `method`, `ethics`, `bib`, `axis-a`, `axis-b`, `axis-c`, `table`, `gaps`, `baseline`, `protocol`, `eda`, `mdp`, `env`, `agent`, `repo`, `ai-decl`, `evidence`

### Rules

- Imperative mood, lowercase, no trailing period, ≤ 72 chars.
- One logical change per commit.
- No issue references in commits.
- **Never commit:** raw datasets, model checkpoints, `.venv`, `node_modules`, LaTeX build artifacts (`*.aux`, `*.log`, `*.out`, `*.bbl`, `*.blg`, `*.synctex.gz`), API keys.
- Every member pushes their own work. Authorship is graded from the commit history.

### Examples

```
docs(related): add axis C subsection on dataset limitations

Documents the class imbalance and the temporal split used by the original
authors, both of which constrain our comparability claim.
```

```
refs(bib): add 7 peer-reviewed entries for axis A

All DOIs resolved manually in IEEE Xplore and ACM DL before adding.
```

```
docs(baseline): declare literature target metric and protocol caveats
```

```
exp(eda): log class distribution and missing-value report with seed 42
```

```
build(paper): pin IEEEtran class and add latexmk build instructions
```

---

## Pull Request Convention

### Title

```
<type>(<scope>): <short summary> (#<issue-id>, #<issue-id>, …)
```

Example:

```
docs(related): complete three-axis literature review (#010, #011, #012, #013, #014)
```

### Description Template

```markdown
## Summary
One paragraph: what this branch closes and why.

## Linked Issues
Closes #<id>
Closes #<id>

## Type of Change
- [ ] Documentation / paper section
- [ ] Bibliography
- [ ] Code
- [ ] Experiment / results
- [ ] Infrastructure

## Changes
- Bullet list of key changes
- Files added or modified

## Academic Compliance
- [ ] All new references are peer-reviewed (journal or conference)
- [ ] All new DOIs resolve and the content matches what is attributed to them
- [ ] No arXiv preprint added without explicit justification
- [ ] Every technical decision introduced here is justified in the text
- [ ] No dataset, checkpoint or dependency folder committed
- [ ] AI usage for this work is reflected in the AI usage declaration

## Evidence
- Link to the figure, log or notebook backing every claim made here
- Compiled PDF renders without errors (if the paper was touched)

## Checklist
- [ ] Branch named per convention
- [ ] Commits follow Conventional Commits (no issue IDs in commits)
- [ ] All closed issue IDs present in title and description
- [ ] Targets the correct stage branch
```

### PR Rules

- One issue branch, one PR. Do not stack unrelated work.
- **Squash merge** for issue branch → stage branch.
- **Merge commit** for stage branch → `master`.
- The PR into `master` lists every issue closed during the stage.
- The `master` approval must come from a member who did **not** author the bulk of the stage.

---

## Ignore Rules

At minimum:

```gitignore
__pycache__/
*.py[cod]
.venv/
venv/
node_modules/
.ipynb_checkpoints/
*.aux
*.bbl
*.blg
*.log
*.out
*.synctex.gz
.env
```

Datasets, model checkpoints and any locally downloaded corpus are ignored as well — the repository stores the instructions to obtain them, never the data.

**Committed on purpose:** the `.bib` file, config files including fixed seeds, run logs, and every Markdown document.

---

## Stage Delivery Ritual

1. Content freeze the day before the deadline.
2. Clean-clone test: fresh clone, follow the README only, everything runs.
3. Verify the commit history shows all three members.
4. Verify the AI usage declaration has a block per member.
5. Open the `stage<N>` → `master` PR listing every closed issue, get 1 approval, merge.
6. Tag the merge commit.
7. Submit the repository link on TecDigital.