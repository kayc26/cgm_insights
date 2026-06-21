# Decisions Log

Append-only. Two lines per entry: what I decided, why.

Timeframe: 
window2: 2026/3/25 - 2026/4/8
window1: 2026/7/28 - 2026/8/11

## Data integrity: Bevel double-logging bug

Found duplicate entries from Bevel across ALL macro fields independently
(DietaryEnergyConsumed, DietaryCarbohydrates, DietaryProtein, DietaryFatTotal,
DietaryFiber) — not just energy. Values differ slightly between true duplicates
(re-parsing/rounding), so exact-match dedup misses them; used near-dupe detection
(same rtype, <10min apart, <10% value diff) + manual Bevel confirmation per
candidate. Confirmed dupes removed from raw df, meal_dataset rebuilt downstream.
Macros-only baseline R² moved from -0.34 (pre-fix, corrupted) to -0.07 (post-fix) —
the original number was not representative of the actual data.

## Feature architecture: GI × carbs split (replaces glycemic_load scalar)

Built glycemic_load (GI × carbs / 100) per plan, via manual carb-source curation
(44 distinct foods across 90 meals, photo-reviewed in Bevel, GI mapped from
published values, single reference standard used throughout).

Tested GL as combined scalar vs. GI and carbs as separate features. Separate
features won on every metric (cross-window R², both targets, both directions).
Reasoning: GL collapses two physically distinct interventions (swap food source
vs. reduce quantity) into one number the model can't distinguish. Splitting them
lets the perturbation mechanism treat "swap to lower-GI source" and "reduce
portion" as genuinely separable levers with independent coefficients.

Final feature set: GI, DietaryCarbohydrates, DietaryFatTotal, DietaryFiber,
DietaryProtein, pre_steps.

## Dropped: post-meal activity features (post_steps, post_active_energy,
## walked_after_eating)

Coefficient on post_steps came out positive (more walking → higher predicted
peak) — backwards. Root cause: self-selection confound, not bad data. I walk
after dinner specifically when I expect a meal to spike me; low-carb meals
don't get a walk because I don't expect a spike. Correlational data can't
separate "walking lowered the peak" from "I only walk on meals I already
predicted would spike" — the second effect dominates the signal.

Removing these features improved cross-window R² substantially in the features
most exposed to them (full set: w2→w1 0.141→0.048 i.e. WORSE here since other
correlated features diluted the bad coefficient; lean set: w2→w1 -0.024→0.161,
i.e. BETTER, since post_steps had undiluted influence there). Net: removed
from final feature set. Walking is NOT a counterfactual lever in v1 — would
require either more data with naturally decoupled walking decisions, or
deliberate experimentation (walk after low-carb meals sometimes, skip after
high-carb meals sometimes) to de-confound. Named as future work, not pursued.

## Validation results (final, both targets, both directions)

Train window 1 → test window 2 / Train window 2 → test window 1:
- peak_rise: -0.015 / 0.178
- iauc: 0.023 / 0.224

Robust pattern across every feature-set variant tested: w2→w1 generalizes
meaningfully better than w1→w2. Not symmetric noise — consistent direction
across ~10 independent train/test fits. Plausible explanation: window 2 has
a flatter, more spread iAUC distribution and less post-meal walking (59% vs
77% of meals) than window 1 — a model trained on window 2's noisier, wider
behavioral range may generalize to window 1's narrower range better than the
reverse. Stated as the headline cross-window finding, not a caveat.

## Perturbation mechanism: two levers, three rejected

Surviving levers (multiplicative/proportional, scaled to each meal's actual
composition — not flat deltas):
- Swap to lower-GI carb source (GI *= 0.6, gated: only offered if GI > 30,
  to avoid recommending a "lower-GI swap" on a food that's already low-GI,
  e.g. vegetables)
- Add a side of low-carb vegetables (DietaryFiber += 3, DietaryCarbohydrates
  += 4 — paired, not fiber-only, since no real food adds fiber without some
  carbs/calories)

Rejected, with reasons:
- "Eat fiber first" — model has no eating-order/sequencing feature; meal-level
  aggregated data structurally cannot represent intervention order. Different
  from "add fiber to the meal," which IS representable and is what the
  surviving veg-side lever actually tests.
- "Reduce portion by 25%" — two problems: (1) not realistic user-facing advice
  (requires pre-portioning or stopping mid-meal, high friction, low compliance);
  (2) meal-level data can't represent partial/food-specific reduction (can't
  model "skip the rice, keep the chicken") — uniform scaling assumes false
  nutritional homogeneity within a meal.
- Flat-magnitude perturbations (fixed -25 GI points, fixed +5g fiber) — produced
  near-identical deltas across very different meals (model artifact, not real
  signal: effect size driven by fixed perturbation size, not meal composition).
  Fixed by switching to proportional/multiplicative perturbations.

Spike/no-spike gate: uses baseline_glucose + predicted peak_rise, converted to
mg/dL (caught and fixed a mmol/L vs mg/dL unit bug — meal_dataset stores
mmol/L, ×18.0182 to convert), thresholded against Lingo's own published
gate (<100 mg/dL = no spike, the firm lower bound Lingo's algorithm uses;
their hard upper bound is 140 mg/dL, with an algorithmic middle zone).
Recommendations suppressed below 100 mg/dL predicted peak.

## Explored and explicitly not pursued

- Pretraining on public CGM dataset (CGMacros, 45 subjects) — would require a
  transfer-learning pipeline, different population/device/schema, and
  undercuts the project's own N=1 personalization framing. Declined.
- Binary spike classifier as primary model — would discard the continuous
  signal the perturbation mechanism depends on for ranking levers. Declined;
  kept as a side exploration only (AUC=0.68, high fold variance from n=13
  positive class, inconclusive, not pursued further).
- Time-of-day (meal_hour, sin/cos encoding) — produced unstable, wildly
  out-of-scale coefficients (-27, +2.3 vs. 0.001-0.05 range elsewhere) at this
  N. Classic small-N overfit symptom. Dropped.
- Tree-based models (random forest/GBM) — would likely fit better in-sample but
  produce discontinuous, less-interpretable perturbation responses (step
  functions vs. smooth coefficient-driven response), directly working against
  the perturbability constraint. Not tried; linear kept for v1.

## Known v1 limitations (stated, not hidden)

- Magnitude calibration uses fixed percentage assumptions (40% GI reduction,
  +3g fiber/+4g carbs for a veg side) rather than per-food-realistic
  substitution sizes — a real "swap white rice for basmati" GI delta isn't
  necessarily 40%.
- No eating-order or item-level (within-meal) granularity — meal_dataset is
  one row per meal, not per food item.
- Walking/activity excluded as a lever due to unresolved self-selection
  confound in the source data.
- Advice ceiling: a 6-feature linear model on N=90 tends to produce
  population-sound recommendations with personalized magnitudes, not
  personalized content. True novel personal insight (e.g., "you're unusually
  fiber-sensitive vs. population norms") would need a coefficient-vs-literature
  comparison not yet done, or more data.