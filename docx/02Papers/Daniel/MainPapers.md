# Reading Assignment — Daniel Duarte Cordero

**Project:** Game-State Win Probability Estimation in the Pokémon TCG
**Course:** IC-6200 · Track A (Classical Tabular Machine Learning)
**Principal axis:** **A — Problem and domain**
**Load:** 9 papers (7 core + 2 Track A technical requirements)

---

## Why this bundle

Daniel owns the **Axis A survey** and the question the professor asked directly: *what has been done in other games, and how has this same question been posed elsewhere?* Papers 1–7 are the answer — MOBA win prediction, collectible-card-game state evaluation, competitive Pokémon, imperfect information, and metagame robustness.

Papers 8 and 9 cover two things the Track A statement demands explicitly in the technical analysis: **justified imputation strategy** and **class imbalance**. Without them, two decisions already written into the proposal have no citation behind them, and each unjustified key decision costs 5 points.

---

## What this bundle defends

| Question the professor may ask | Papers that answer it |
|---|---|
| Why is this a real research problem and not a Kaggle exercise? | 1, 2, 3 |
| Has this been done in other games? | 1, 2, 3, 5, 6 |
| Why is a probability different from a label? | 4 |
| Why will your model survive a changing metagame? | 5, 7 |
| Why don't you impute the missing fields? | 8 |
| Why don't you rebalance the classes? | 9 |

---

# Core — Axis A: problem and domain

## 1. Machine Learning Applications in Multiplayer Online Battle Arena Esports — A Systematic Review — **Axis A survey**

**Status:** ⚠️ Unverified — confirm venue, year and DOI in Scopus.

**Why we chose it.** Principal survey for Axis A. Systematically reviews ML applications in MOBA esports: prediction problems, datasets built from game mechanics and player information, common algorithms, and open challenges.

**What it does for our paper.** Gives the broad domain view against which we position the specific win-prediction papers. It is the source that lets us claim *"win prediction from game state is an established research problem"* with a systematic review behind it, not a single paper.

**Read for:** the taxonomy of prediction problems, which metrics the field uses, and any stated open challenge that our project touches.

---

## 2. Hero Featured Learning Algorithm for Winning Rate Prediction of Honor of Kings

**Status:** ⚠️ Unverified.

**Why we chose it.** Predicts match outcome from intermediate game information in a competitive videogame.

**What it does for our paper.** Direct analogue for learning win probability from evolving game states, and for comparing performance at different stages of a match — the second half of our research question.

**Read for:** how they slice the match into stages, and whether they report performance per stage. That is exactly the curve we plan to produce per turn.

---

## 3. Evolving Evaluation Functions for Collectible Card Game AI

**Status:** ⚠️ Unverified.

**Why we chose it.** Directly in the CCG domain, and studies how to assign useful values to game states.

**What it does for our paper.** The closest *conceptual* precedent for a state evaluator in card games, even though it is not supervised win-probability estimation. Useful for the framing in §2 of the proposal: a state-value function usually lives inside a search or RL loop; we isolate it and learn it supervised.

**Read for:** how they define what makes a state "good", and what information the evaluation function receives.

---

## 4. Rethinking Evaluation Metric for Probability Estimation Models Using Esports Data

**Status:** ⚠️ Unverified.

**Why we chose it.** Our output is a probability, not a win/loss label. Argues for evaluating probability-estimation models with metrics appropriate to probability quality, not only classification accuracy.

**What it does for our paper.** Justifies our metrics section from the *game domain* side, complementing Adriel's calibration bundle which argues it from the methodological side. It is why we report Log Loss, Brier Score and calibration curves alongside ROC-AUC.

**Read for:** which metrics they recommend and why, and whether they show a case where AUC and calibration disagree.

---

## 5. VGC-Bench: Towards Mastering Diverse Team Strategies in Competitive Pokémon

**Status:** ⚠️ Unverified — **check whether this is peer-reviewed or arXiv-only.** If it is a preprint, flag it and ask the professor before counting it.

**Why we chose it.** Directly about competitive Pokémon, and evaluates generalization across diverse and unseen team strategies.

**What it does for our paper.** Best support for our unseen-deck holdout protocol (§13.3): does the model learn transferable game knowledge, or memorize specific compositions?

**Read for:** how they construct the unseen-team split and what degradation they report.

---

## 6. Player Identification and Next-Move Prediction for Collectible Card Games with Imperfect Information

**Status:** ⚠️ Unverified.

**Why we chose it.** Uses dynamic game states from Legends of Code and Magic and explicitly handles imperfect information. Also studies transfer to previously unseen individuals.

**What it does for our paper.** Two jobs: it validates that a CCG game state can be turned into ML features under hidden information (our opponent's hand is `None` in 100 % of snapshots), and it supports the generalization discussion.

**Read for:** their state representation — how they encode what the player cannot see.

---

## 7. Beyond the Meta: Leveraging Game Design Parameters for Patch-Agnostic Esport Analytics

**Status:** ⚠️ Unverified.

**Why we chose it.** Addresses model degradation when a videogame changes through patches, and shows that representations built on transferable game characteristics can survive later versions.

**What it does for our paper.** Our audit found six engine versions coexisting (1.30.1 → 1.32.4), which confounds the temporal split. This is the literature that says the problem is real and points at a mitigation.

**Read for:** what they mean by "patch-agnostic" features, and whether that idea maps onto our state features.

---

# Track A technical requirements

## 8. Structured missingness — imputation

**Status:** ⚠️ **Incomplete source. Do not cite until the actual paper is found.**

This reference was surfaced only as *"Mitra et al. 2023 — structured missingness framework"* by a Consensus synthesis. Author list, title, journal and DOI are all unknown. Citing from a synthesis without reading the paper is exactly what the −10 point penalty targets.

**Search:** `"structured missingness" AND framework AND imputation`
**Fallback if it doesn't resolve:** Buczak et al. 2023, identified in the same synthesis as the *missing by design* example. It carries the same argument.

**Why we need it.** Our §11.2 distinguishes *structural* missingness from *unexpected* missingness and refuses to impute the former. That is the correct decision and currently has no citation.

**What it does for our paper.** Supplies the concept that a semantic `None` is not a statistical missing value. Our `looking` field is `None` in 98.1 % of states because the game defines it that way, not because data was lost. Imputing the mean there would invent a game state that cannot exist.

**Read for:** the definition of structured missingness, and any statement about when imputation is inappropriate rather than merely imperfect.

---

## 9. The Harm of Class Imbalance Corrections for Risk Prediction Models

**Status:** ⚠️ Peer-reviewed (*Journal of the American Medical Informatics Association*, 2022) — complete volume, number, pages and DOI.

van den Goorbergh, van Smeden, Timmerman, Van Calster.

**Why we chose it.** It reports that correcting class imbalance *harms* risk prediction models. That is the exact claim our §12.1 makes when it prefers `class_weight` over resampling.

**What it does for our paper.** **This is the paper that ties two of our arguments into one.** Resampling distorts predicted probabilities — and predicted probabilities are our output, not a by-product. It connects the imbalance decision directly to the calibration bundle Adriel owns, so the survey reads as one coherent argument instead of two separate concerns.

**Read for:** what exactly degrades under correction — discrimination, calibration, or both — and whether they recommend an alternative.

**Domain note:** it is a clinical risk-prediction study. Declare the domain gap; the argument is statistical and transfers, but do not present it as a game-domain result.

---

## Extraction template — fill for every paper

1. Problem addressed / research question
2. Technique or model used
3. Dataset / environment
4. **Unit of analysis** (game, player, snapshot, frame, subject)
5. Train / validation / test protocol
6. Main metric(s)
7. Best reported result
8. Main limitation stated by the authors
9. Possible leakage or generalization concern
10. How it relates to our Pokémon TCG project
11. Which axis it supports (A/B/C)
12. One or two sentences usable verbatim-free in Related Work

Fields 4–7 are what populate the mandatory comparative table. Do not skip them.

**Note on papers 8 and 9:** these are methodological references, not empirical studies on a comparable dataset. Fields 3–7 will often be "not applicable" — say so rather than forcing a value, and do **not** put them in the comparative table as if they were competing approaches on a game dataset.

---

## Historical antecedent — outside the paper count

**Helping AI to Play Hearthstone: AAIA'17 Data Mining Challenge** (2017). A collectible card game, intermediate game-state features, and prediction of the final winner — the closest direct precedent to our research question.

It is also the source of our literature baseline: official baseline AUC ≈ 0.7846, best solution ≈ 0.8019.

Read it even though it is not in your nine. It is the reference the professor is most likely to ask about.