# Reading Assignment — Adriel S. Chaves Salazar

**Project:** Game-State Win Probability Estimation in the Pokémon TCG
**Course:** IC-6200 · Track A (Classical Tabular Machine Learning)
**Principal axis:** **B — Techniques and evaluation**
**Load:** 11 papers (7 core + 4 calibration)

---

## Why this bundle

Adriel owns the **Axis B survey** and the methodological backbone of the project: which model families are defensible for tabular data, how win probability has been estimated in live competitive settings, why correlated observations break naive validation, and why a probability estimator has to be judged on more than discrimination.

The bundle is built so that every methodological claim in the paper has a citation behind it. If the professor asks *"why did you decide that?"*, the answer comes from this list.

Four papers (5, 7, and partly 3 and 6) also feed Axis C, since they concern the statistical structure of the data rather than the model.

---

## What this bundle defends

| Question the professor may ask | Papers that answer it |
|---|---|
| Why classical ML and not deep learning? | 1, 2 |
| Why is this a real research problem? | 3, 4, 6 |
| Why is your split grouped by episode? | 5, 7 |
| Why is ROC-AUC not enough? | 8, 9, 10, 11 |
| What do you do if the model is miscalibrated? | 10, 11 |

---

# Core — model selection, task framing, protocol

## 1. Deep Neural Networks and Tabular Data: A Survey — **Axis B survey**

**Status:** ✅ Verified — Borisov et al., *IEEE Trans. Neural Networks and Learning Systems*, 35(6), 7499–7519, 2024. DOI `10.1109/TNNLS.2022.3229161`

**Why we chose it.** Principal survey for Axis B. Reviews deep learning approaches for tabular data and compares them against traditional methods. Our replay snapshots become structured tabular data, so this survey frames the whole model-selection discussion.

**What it does for our paper.** Lets us state that we chose classical models because the literature does not establish deep learning superiority in this regime — backed by a peer-reviewed IEEE survey rather than by convenience.

**Read for:** the taxonomy of tabular DL methods (data transformation / architecture / regularization), and any statement about when tree ensembles remain competitive.

---

## 2. Why do tree-based models still outperform deep learning on typical tabular data?

**Status:** ✅ Verified — Grinsztajn, Oyallon, Varoquaux, *NeurIPS 2022, Datasets and Benchmarks Track*, vol. 35, pp. 507–520.

**Why we chose it.** Methodological support for including Random Forest and gradient boosting as baselines instead of assuming deep learning is automatically superior.

**What it does for our paper.** The strongest justification for our baseline ladder B2→B4. Benchmarks 45 datasets and reports that tree-based models remain state of the art on medium-sized tabular data.

**Read for:** the inductive-bias analysis (robustness to uninformative features, rotational invariance) — it explains *why*, not just *that*, trees win here.

---

## 3. Win Prediction in Multiplayer Esports: Live Professional Match Prediction

**Status:** ✅ Verified — Hodge et al., *IEEE Trans. Games*, 13(4), 368–379, 2021. DOI `10.1109/TG.2019.2948469`

**Why we chose it.** Live win prediction in Dota 2 using information available as the match progresses. Closest analogue to estimating win probability from an intermediate state rather than from pre-match information only.

**What it does for our paper.** Axis A support for the core task framing, and a source of reported metrics for the comparative table.

**Read for:** what features they use per time window, how they define "live", and their reported metric and value.

---

## 4. A Framework for Predicting the Impact of Game Balance Changes Through Meta Discovery

**Status:** ✅ Verified — Saravanan & Guzdial, *IEEE Trans. Games*, 16(4), 821–830, 2024. DOI `10.1109/TG.2024.3457822`

**Why we chose it.** Uses Pokémon Showdown and studies metagame changes caused by balance changes. Supports the argument that the game distribution evolves over time.

**What it does for our paper.** The Pokémon-domain justification for our temporal protocol (§13.2). Our audit measured deck JSD ≈ 1.000 between first and last day; this paper says such drift is expected in Pokémon and matters.

**Read for:** how they characterize a metagame shift, and whether they quantify it.

---

## 5. Exploring the difficulty of estimating win probability: a simulation study

**Status:** ✅ Verified — Brill, Yurko, Wyner, *Journal of Quantitative Analysis in Sports*, 22(1), 105–115, 2026. DOI `10.1515/jqas-2024-0130`

> **Cite the journal version, never arXiv:2406.16171.** The preprint would not count toward the peer-reviewed papers.

**Why we chose it.** Studies win-probability estimation when many correlated observations come from the same game.

**What it does for our paper.** **The methodological anchor of our leakage argument.** Our dataset produces ~7M snapshots from 52,085 episodes; those rows are not independent. This paper says so in the exact context of win probability, and reports that the dependence structure inflates bias and variance and lowers the effective sample size.

**Read for:** how they quantify the effect of correlation, and whether they recommend a grouping strategy.

---

## 6. Analyzing the Differences between Professional and Amateur Esports through Win Probability

**Status:** ✅ Verified — Xenopoulos, Freeman, Silva, *Proc. ACM Web Conference 2022 (WWW '22)*, pp. 3418–3427. DOI `10.1145/3485447.3512277`

**Why we chose it.** Uses win probability to compare different player populations.

**What it does for our paper.** Supports the discussion of whether a model learned on one population still works when skill or behavior changes — our analogue is generalization across agents under the Kaggle rating-based selection bias.

**Read for:** whether performance transfers across populations, how they measure the gap, and which features matter at different skill levels.

---

## 7. Analyzing Information Leakage on Video Object Detection Datasets by Splitting Images Into Clusters With High Spatiotemporal Correlation

**Status:** ✅ Verified — Figueiredo & Mendes, *IEEE Access*, 12, 47646–47655, 2024. DOI `10.1109/ACCESS.2024.3383047`

**Why we chose it.** Consecutive video frames are highly correlated, like sequential game snapshots. Shows why random splitting leaks and why correlated observations must be grouped before partitioning.

**What it does for our paper.** Second pillar of the leakage argument, complementary to paper 5. **Declare the domain gap explicitly** — it is a vision result, not a game-domain one.

**Read for:** their measured inflation of performance under random splitting, so we can compare it against our own measured 99.995 % episode contamination.

---

# Calibration — why AUC is not enough

## 8. Classifier Calibration: A Survey on How to Assess and Improve Predicted Class Probabilities

**Status:** ✅ Verified — Silva Filho et al., *Machine Learning*, 112(9), 3211–3260, 2023. DOI `10.1007/s10994-023-06336-7`

> **The year is 2023, not 2021.** The 2021 date belongs to the arXiv preprint.

**Why we chose it.** The anchor reference for calibration. Covers proper scoring rules, evaluation metrics, visualization approaches, and post-hoc calibration methods for binary classification.

**What it does for our paper.** Justifies the entire metrics section: why we report Log Loss, Brier Score and reliability curves alongside ROC-AUC. It also subsumes several narrower calibration papers, which is why the bundle stays at four.

**Read for:** the binary-classification sections only — skip the multiclass material, our problem is binary. Focus on proper scoring rules and post-hoc calibration.

---

## 9. Predicting Good Probabilities with Supervised Learning

**Status:** ⚠️ Peer-reviewed (ICML 2005) — complete pages and DOI from the ACM Digital Library.

**Why we chose it.** The canonical study of which model families produce well-calibrated probabilities out of the box and which do not.

**What it does for our paper.** **This is the concrete reason our project needs calibration, not a generic one.** It reports that boosted trees and other max-margin methods are systematically miscalibrated — and boosted trees are exactly our B4 baseline. It converts "calibration matters in general" into "calibration matters for the model we are going to use".

**Read for:** the reliability diagrams for boosted trees and Random Forest, and how Platt scaling and isotonic regression change them.

---

## 10. Calibrating Machine Learning Approaches for Probability Estimation: A Comprehensive Comparison

**Status:** ⚠️ Peer-reviewed (*Statistics in Medicine*, 2023) — complete volume, number, pages and DOI from Wiley.

**Why we chose it.** Systematic comparison of calibration methods for probability estimation in a peer-reviewed journal.

**What it does for our paper.** Our decision guide if the model turns out miscalibrated. Instead of picking a recalibration method arbitrarily, we cite a comparison that evaluated several.

**Read for:** which method performs best under which conditions, and whether recalibration costs discrimination (AUC).

---

## 11. Stable Reliability Diagrams for Probabilistic Classifiers

**Status:** ⚠️ Peer-reviewed (*PNAS*) — complete year, volume, number, pages and DOI.

**Why we chose it.** Fixed-bin reliability diagrams are unstable; this paper provides a more reproducible alternative.

**What it does for our paper.** Solves a problem we had already identified: our calibration curves should not depend on an arbitrary choice of bins. Gives the method, and the citation that makes the choice defensible.

**Read for:** what makes standard reliability diagrams unstable, and what the proposed alternative requires.

---

## Pending before submission

- [ ] Complete `pages` and `doi` for Niculescu-Mizil & Caruana (ACM DL)
- [ ] Complete `volume`, `number`, `pages`, `doi` for Ojeda et al. (Wiley)
- [ ] Complete `year`, `volume`, `number`, `pages`, `doi` for Dimitriadis et al. (PNAS)
- [ ] Confirm every DOI resolves and the content matches what we attribute to it

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

**Note on papers 8–11:** the extraction template applies loosely here. These are methodological references, not empirical studies on a comparable dataset, so fields 3–7 will often be "not applicable". Say so rather than forcing a value — and do **not** put them in the comparative table as if they were competing approaches on a game dataset.