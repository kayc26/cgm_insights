# Coefficient vs. Literature Comparison

Target: `peak_rise` (mmol/L), N=87 meals, single subject, no confidence intervals computed.
Per-SD effects reproduced from the ground-truth table for reference.

## 1. Comparison table

| Feature | Fitted sign & per-SD effect | Population expectation | Agree? | Source |
|---|---|---|---|---|
| GI | + , +0.198 mmol/L (+3.56 mg/dL) per SD | Positive — higher-GI meals produce higher, sharper peaks | **Direction: yes.** Magnitude not directly comparable — cited studies use GDM/at-risk populations with amplified responses (~1.9 mmol/L for a ~30-point GI gap) or report % differences (17–35%) rather than a per-point slope in healthy subjects, so this fitted magnitude can't be benchmarked precisely. | [Timing of Peak Blood Glucose after Breakfast Meals of Different GI in Women with GDM](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3571634/); [MEDGI-Carb RCT](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8838655/) |
| DietaryCarbohydrates (g) | + , +0.531 mmol/L (+9.56 mg/dL) per SD — largest effect in the model | Strongly positive; carb quantity is typically the dominant driver of postprandial glucose, ahead of GI | **Yes**, direction and relative dominance both match — carbs has the largest per-SD effect of the six features, consistent with carb content explaining more of the variance in glycemic load than GI does. | [ADA statement, Dietary Carbohydrate in Prevention/Management of Diabetes](https://diabetesjournals.org/care/article/27/9/2266/22648/Dietary-Carbohydrate-Amount-and-Type-in-the) |
| DietaryFatTotal (g) | + , +0.079 mmol/L (+1.42 mg/dL) per SD — smallest-magnitude effect | Negative on peak height — fat delays gastric emptying and blunts the peak (though it can prolong elevated glucose later) | **No — sign mismatch (flagged anomaly).** | [Effects of fat on gastric emptying / glycemic response in T2D](https://pubmed.ncbi.nlm.nih.gov/16537685/); [fat co-ingestion flattens glucose curves](https://www.sciencedirect.com/science/article/pii/S0261561422002138) |
| DietaryFiber (g) | − , −0.179 mmol/L (−3.22 mg/dL) per SD (≈ −0.83 mg/dL per gram) | Negative — fiber (esp. viscous fiber) blunts postprandial glucose peak | **Yes, direction and magnitude both plausible.** Healthy-adult RCTs report ~8% peak reduction from 11.6–24 g added fiber, i.e. roughly 0.5–1.0 mg/dL peak reduction per gram — the fitted ~0.83 mg/dL/g falls inside that range. | [Fiber RCT in healthy adults, satiety + postprandial glucose](https://pmc.ncbi.nlm.nih.gov/articles/PMC10648557/); [High-fiber cookie RCT in healthy adults](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5372900/) |
| DietaryProtein (g) | − , −0.070 mmol/L (−1.25 mg/dL) per SD — small | Small negative or ~neutral on peak in isolation; protein mainly matters when co-ingested with carbs (insulin/GLP-1 effects) | **Yes** — small negative magnitude matches "little independent effect" framing. | [Protein intake and glucose/insulin dynamics review](https://www.frontiersin.org/journals/clinical-diabetes-and-healthcare/articles/10.3389/fcdhc.2025.1712506/full); [Whey protein co-ingestion, glucose/insulin](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9370714/) |
| pre_steps | + , +0.287 mmol/L (+5.17 mg/dL) per SD — second-largest effect in the model | Population evidence: pre-meal exercise has **no significant effect** on postprandial glucose (not a strong negative prior, but not positive either) | **No — sign and magnitude both anomalous (flagged).** A large positive coefficient where the literature expects ~null is the more concerning of the two anomalies. | [Meta-analysis: "After Dinner Rest a While, After Supper Walk a Mile?"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10036272/) — pre-meal exercise SMD = −0.13 [95% CI −0.42, 0.17], non-significant; post-meal exercise SMD = 0.55, significant benefit |

## 2. The two anomalies

**Fat (small positive, expected negative).** Fat's canonical mechanism — slowed gastric emptying — blunts and delays the peak, so population science predicts a negative coefficient on peak height. The fitted effect is positive but the smallest-magnitude coefficient in the model (+1.42 mg/dL per SD), which is consistent with reading it as noise rather than a real reversal. The more likely explanation is a meal-size confound: in this person's real (non-randomized) meals, higher-fat dishes tend to be larger or more calorically dense overall, and total meal energy/size is independently associated with a higher glucose response in the literature — so `DietaryFatTotal` may be partly standing in for "this was a bigger meal" rather than capturing fat's own blunting effect, which the model can't separate at 87 meals and no randomization.

**pre_steps (positive, expected null-to-negative).** This is the more notable anomaly because it's not small — at +5.17 mg/dL per SD it's the second-largest effect in the model, behind only carbohydrates. The literature doesn't support a strong negative prior here (a 2023 meta-analysis found pre-meal exercise has no significant effect on postprandial glucose, unlike post-meal exercise which clearly helps), but it also gives no reason to expect a strong positive effect. The likely explanation is a self-selection confound analogous to the one DECISIONS.md already documents for post-meal walking: pre-meal steps aren't randomly assigned in this data either. Higher-step periods before a meal plausibly correlate with meal context — active mornings/days that precede eating out, larger or more discretionary meals, or later/skipped prior meals — any of which could independently raise the peak. As with post-meal activity, correlational single-subject data can't separate "steps caused a higher peak" from "the kind of day that produces more steps also produces bigger or more discretionary meals."

## 3. Headline answer: is this person unusually fiber-sensitive?

No — the honest answer is directional agreement, not a personalized finding. The fitted fiber effect (≈ −0.83 mg/dL peak reduction per gram, −3.22 mg/dL per ~4g SD) sits inside the range reported by healthy-adult RCTs (roughly −0.5 to −1.0 mg/dL per gram, from studies adding 11.6–24 g of fiber and observing ~8% peak reductions). That's a real check worth reporting — the fitted magnitude isn't wildly outside published bounds — but it is not evidence of unusual personal sensitivity. Three things limit that claim specifically:

1. **No confidence interval was computed** for the fitted fiber coefficient, so "falls inside the published range" is a point-estimate comparison, not a statistical one. The true coefficient could plausibly be anywhere from noticeably smaller to noticeably larger and still be consistent with N=87.
2. **The published range itself is wide and heterogeneous** — different fiber types (viscous vs. non-viscous), doses, and food matrices produce different effects, so "inside the range" is a low bar.
3. **Cross-window validation on this same model is weak-to-negative** (peak_rise R² of −0.015 training window 1 → window 2), which caps how much confidence any single coefficient — fiber included — deserves as a stable personal estimate rather than a fit that happens to land in a plausible zone for these 87 meals.

The defensible claim: this person's fiber response is *directionally and roughly magnitude-consistent* with population science. Whether they are unusually fiber-sensitive is a question this dataset cannot answer — it would need per-coefficient confidence intervals (more data) or a designed within-subject fiber-dose experiment to distinguish from population-typical.

## 4. Proposed case-study subsection

Target location: Results or Limitations section of `CASE_STUDY.md`. Plain voice, no self-congratulatory language, framed as a sanity check.

---

### Do the coefficients agree with the science?

Four of six coefficients point the direction population nutrition science predicts: carbohydrate quantity and glycemic index raise the predicted peak, fiber and protein lower it. Fiber's fitted magnitude — about 0.8 mg/dL of peak reduction per gram — also falls inside the range reported by RCTs in healthy adults (roughly 0.5–1.0 mg/dL per gram). That's a face-validity check, not a personalized finding: with 87 meals and no confidence intervals on the coefficients, "consistent with published ranges" is as far as this data supports. It is not evidence of unusual personal fiber sensitivity.

Two coefficients don't match expectation. Fat's small positive sign runs against its known peak-blunting mechanism — the likelier explanation is that fat is standing in for total meal size in this uncontrolled data, not a real reversal of fat's effect. Pre-meal steps' positive sign is the bigger flag: it's the second-largest effect in the model, where the literature expects roughly nothing. The likely cause is the same self-selection problem already found in post-meal walking — steps before a meal aren't randomly assigned, and probably track which meals were bigger or more discretionary in the first place.

---

*(150 words in the proposed subsection body.)*
