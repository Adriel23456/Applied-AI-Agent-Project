# Reading Assignment — Sebastián Hernández Bonilla

**Project:** Game-State Win Probability Estimation in the Pokémon TCG
**Course:** IC-6200 · Track A (Classical Tabular Machine Learning)
**Principal axis:** **C — Dataset and validation**
**Load:** 9 papers (7 core + 2 generic leakage)

---

## Why this bundle

Sebastián owns the **Axis C survey** and the part of the project that can invalidate everything else: whether the experimental protocol is sound. Our dataset produces ~7 million correlated rows from 52,085 independent episodes, spans ten days with measured distribution drift, and mixes six engine versions. Every one of those facts is a validity threat, and this bundle is the literature that names them.

The professor singled out data leakage as the central difficulty of this topic. Papers 8 and 9 supply the foundational framework that the proposal's §9.2 is already applying without citing.

---

## What this bundle defends

| Question the professor may ask | Papers that answer it |
|---|---|
| What is data leakage, formally? | 8, 9 |
| Why must snapshots from one episode stay together? | 3, 8 |
| Why do you evaluate on later days separately? | 1, 4, 6 |
| Why does a dataset with no literature still work? | 5 |
| Why hold out unseen decks? | 7 |
| What are the state features actually telling you? | 2 |

---

# Core — Axis C: dataset, validation, distribution shift

## 1. A survey on machine learning for recurring concept drifting data streams — **Axis C survey**

**Status:** ⚠️ Unverified — confirm venue, year and DOI in Scopus.

**Why we chose it.** Principal survey for Axis C. Provides terminology and a framework for concept drift, recurring distributions, detection and adaptation strategies, evaluation issues, and open challenges.

**What it does for our paper.** Gives the vocabulary to describe precisely what our audit measured: deck JSD ≈ 1.000 and agent JSD ≈ 0.972 between the first and last day. Without this survey we can only say "the data changes"; with it we can name the phenomenon and cite an established framework.

**Read for:** the drift taxonomy (sudden, gradual, recurring) and which type best describes a metagame.

---

## 2. Explainable e-sports win prediction through Machine Learning classification in streaming

**Status:** ⚠️ Unverified.

**Why we chose it.** Performs win prediction on continuously arriving game information and adds explainability.

**What it does for our paper.** Bridges Axis A and Axis B: a game-state prediction reference *and* a justification for our explainability section (§16.1 — feature importance, SHAP, ablations by family). Supports the argument that the contribution is *which state features carry information about victory*, not a headline AUC.

**Read for:** which explainability instruments they use and what they conclude about feature relevance.

---

## 3. Participant-Aware Model Validation for Repeated-Measures Data: Comparative Cross-Validation Study

**Status:** ⚠️ Unverified.

**Why we chose it.** Shows that random splitting of repeated observations from the same participant substantially inflates measured performance.

**What it does for our paper.** The peer-reviewed analogue of our rule that all snapshots from one episode must stay in the same partition. Our own measurement — a random 70/30 split contaminates 99.995 % of episodes — is the Pokémon version of exactly what this paper reports.

**Read for:** the magnitude of the inflation they measure, so we can compare it against ours in the comparative table.

---

## 4. Evaluation of domain generalization and adaptation on improving model robustness to temporal dataset shift in clinical medicine

**Status:** ⚠️ Unverified.

**Why we chose it.** Trains on earlier time periods and evaluates on later ones. The domain is medical, but the protocol matches our planned train-on-earlier / test-on-later experiment.

**What it does for our paper.** Direct precedent for the secondary protocol (§13.2). **Declare the domain gap explicitly** — it is a methodological analogue, not a game-domain result.

**Read for:** how much performance drops under temporal evaluation, and whether they separate discrimination from calibration in that drop.

---

## 5. SC2EGSet: StarCraft II Esport Replay and Game-state Dataset

**Status:** ✅ Verified — Białecki et al., *Scientific Data*, 10, 600, 2023. DOI `10.1038/s41597-023-02510-7`

**Why we chose it.** An analogous competitive-game replay dataset transformed into structured game-state information for ML. They processed 55 replaypacks containing 17,930 files with game-state information from StarCraft II tournaments since 2016.

**What it does for our paper.** **The Axis C anchor.** Our dataset has no peer-reviewed literature (declared as gap 1), so this covers the substitution the course allows: reviewing analogous datasets in the same domain and justifying comparability.

**Read for:** how they document replay processing, game versions and dates. Our data section should mirror that structure — it is a published template for exactly the thing we have to write. Note also that it is a *Scientific Data* descriptor, so its structure is the canonical way to present a dataset in a peer-reviewed venue.

---

## 6. Systematic Review of Approaches to Preserve Machine Learning Performance in the Presence of Temporal Dataset Shift in Clinical Medicine

**Status:** ⚠️ Unverified.

**Why we chose it.** Broad evidence that discrimination *and* calibration deteriorate when the data distribution changes over time.

**What it does for our paper.** Strengthens paper 4 with a systematic review rather than a single study. Supports reporting the temporal protocol as a separate result instead of averaging it away.

**Read for:** whether calibration degrades faster than AUC — if so, that is a prediction we can test on our own data.

---

## 7. Learning With Generalised Card Representations for "Magic: The Gathering"

**Status:** ⚠️ Unverified.

**Why we chose it.** Studies a collectible card game whose card pool changes over time, and evaluates performance on previously unseen cards.

**What it does for our paper.** Supports the unseen-deck holdout (§13.3) from the CCG side, complementing VGC-Bench from the Pokémon side. Also relevant to our deck-encoding decision: 2,376 decks with the top 10 covering 39.94 % of instances is a memorization risk.

**Read for:** how they represent a card so the model generalizes to cards it never saw. That idea may apply directly to our `deck_hash` problem.

---

# Generic data leakage — the foundational framework

## 8. Leakage in Data Mining: Formulation, Detection, and Avoidance

**Status:** ✅ Verified — Kaufman, Rosset, Perlich, Stitelman. *ACM Transactions on Knowledge Discovery from Data*, 6(4), Article 15, pp. 1–21, December 2012. DOI `10.1145/2382577.2382579`

> **Use this version, not the KDD '11 one.** The conference version has three authors; this journal version adds Stitelman and is the extended, canonical reference.

**Why we chose it.** The canonical formulation of leakage. Calls it *"one of the top ten data mining mistakes"* and notes that existing literature had largely left the idea unexplored, particularly for complex cases where the i.i.d. assumption is violated.

**What it does for our paper.** **This is the paper the professor is most likely to look for.** Our §9.2 is organized as a leakage taxonomy; this is the source that taxonomy descends from. It also proposes *learn-predict separation* as the avoidance strategy, which is precisely what our grouped split implements.

Note the direct relevance: our snapshots violate i.i.d. in exactly the way this paper singles out as under-explored.

**Read for:** the formal definition of leakage, the learn-predict separation, and the detection strategies for when the modeler did not control data collection — which is our situation with a Kaggle-published dataset.

---

## 9. Overview of Leakage Scenarios in Supervised Machine Learning

**Status:** ⚠️ Peer-reviewed (*Journal of Big Data*, 2023) — complete volume, number, pages and DOI.

Sasse, Nicolaisen-Sobesky, Dukart, Eickhoff, Goetz, Hamdan, Komeyer, Kulkarni, Lahnakoski, Love, Raimondo, Patil.

**Why we chose it.** A modern catalogue of leakage scenarios in supervised ML, complementing the 2012 formal framework with the scenarios practitioners actually hit.

**What it does for our paper.** Maps onto the six-row taxonomy in our §9.2 (episode, temporal, agent, deck memorization, hidden-information, metadata leakage). Lets us present that table as an instance of a published catalogue rather than a list we invented.

**Read for:** which of their scenarios match our six, and whether they name any we missed.

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

**Note on papers 8 and 9:** methodological references, not empirical studies on a comparable dataset. Fields 3–7 will often be "not applicable" — say so rather than forcing a value, and keep them out of the comparative table.

---

## Gap to declare in the survey

No paper in the selection studies data leakage **within the game domain**. Our leakage references are: a formal framework from data mining (8), a scenario catalogue from general supervised ML (9), a repeated-measures analogue from health (3), and a spatiotemporal analogue from vision (Adriel's paper 7).

That is not a flaw — the argument is domain-independent, and papers 8 and 9 are general by construction rather than borrowed from another field. But the two *analogues* must be labelled as such in the related-work section. Presenting a clinical repeated-measures study as if it were a game-domain result would be a misattribution, and the course penalizes that.