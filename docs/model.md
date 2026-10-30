# Model assumptions, version 0.3

The desktop model now uses **joy, sadness, fear, anger, and disgust**. This is a
chosen vocabulary for this project, not a claim that science establishes exactly
five universal emotions. Envy is no longer an independent emotion meter: social
comparison can produce sadness alongside joy, and a person can conceal distress.

## Scientific status

This is a **theory-inspired, testable prototype, not an empirically validated
society simulator**. Its appraisal → emotion → coping → reappraisal structure is
inspired by [Marsella & Gratch's EMA (2009)](https://ict.usc.edu/pubs/EMA-%20A%20process%20model%20of%20appraisal%20dynamics.pdf).
We do not implement EMA's complete causal/planning representation or reproduce
its validation. Every numerical coefficient below is a project assumption, not a
parameter estimated in that paper. No human response dataset has been fitted.

Software checks establish repeatability and whether intended mechanisms work.
They cannot establish human realism. The distinction between model comparison,
empirical validation and sensitivity analysis is discussed in
[Collins et al., Methods That Support the Validation of Agent-Based Models (2024)](https://www.jasss.org/27/1/11.html).
A later empirical study needs a specified population and task, measured responses,
calibration and held-out validation. Matching an intuitively pleasing outcome is
not a substitute for that process.

## One causal route

```text
conditions → material needs → perceived event
                               ↓
           own values + traits + beliefs + directed relationship
                               ↓
                 appraisal → five feelings → public reaction
                               ↓                   ↓
                     learning and memory    another perceived event
                               ↓
                       subsequent activity
```

`actions.py` changes material outcomes and emits facts; it does not directly add
emotion points. `perception.py` interprets those facts; `emotion.py` contains the
five equations. The observer can inspect private state. Agents can observe
conduct and public responses, not another person's hidden emotions or intentions.

## Personal appraisal

All dimensions are bounded to `[0,1]`. The full formulas live in
`dimensions_for()` in `humanity/engine/perception.py`.

| Dimension | Meaning and individual inputs |
| --- | --- |
| benefit | Perceived help or progress; own goals, belonging values, empathy and affection matter |
| loss | Perceived obstruction or loss; self-worth, esteem and social comparison matter |
| threat | Perceived danger; personal safety, energy, learned trust and relationship history matter |
| blame | Attribution based on scenario responsibility and certainty, adjusted by learned trust |
| control | Perceived coping ability: `0.15 + 0.5*self_control + 0.2*energy + 0.15*self_worth` |
| violation | Observed norm-relevant conduct weighted by personal honesty/care/fairness values |

A refusal provides no evidence of intentional harm: its blame and violation are
zero. Ordinary disagreement is not encoded as a moral violation. An explicit
insult or exposed lie is norm-relevant. Disgust here represents **moral disgust
about conduct**, not contamination disgust, and does not label people as impure.
These distinctions are model choices, not universal claims about moral judgment.

Other people's success can bring empathetic joy and comparison-related sadness.
A belief in unfair opportunities reduces perceived control over one's own future;
it does not manufacture evidence that the successful person cheated. Suspicion
is recorded separately from facts and cannot create guilt or disgust by itself.

Names, ages and role labels are descriptive. Identity influences appraisal through
synthetic formative experience and initial trust/fairness beliefs. We do not infer
personality from nationality, profession or other demographic labels. Personality
and value numbers are synthetic, not validated personality measurements.

## Five emotion algorithms

Let `r = 0.5 + sensitivity`, and let `B,L,T,A,C,V` stand for benefit, loss, threat,
blame, control and violation. `clip` bounds the result to `[0,1]`.

| Feeling | Event response |
| --- | --- |
| Joy | `clip(B*r)` |
| Sadness | `clip(L*(0.45 + 0.55*(1-C))*r)` |
| Fear | `clip(T*(1-0.65*C)*r)` |
| Anger | `clip((0.65*L+0.35*T)*A*(0.3+0.7*C)*r)` |
| Disgust | `clip(V*(0.5+0.5*A)*r)` |

Responses can coexist. Higher coping ability shifts the response to attributable
harm toward anger and away from helpless sadness/fear. These exact functional
forms are hypotheses that can be challenged and replaced independently.

Between events, emotion decays exponentially with a **four-hour half-life**.
For each observed event, `current += (1-current)*0.34*response`. Perceived benefit
also reduces fear/sadness with recovery gain `0.16`; anger recovery is moderated
by blame. These assumptions mean event frequency matters. We do not normalize
all emotions to sum to one. Memories record the response intensity and actual
before/after state separately, so an old emotion is not attributed entirely to a
new encounter.

The parameters are grouped in `EmotionParameters` in `emotion.py`. Structural
coefficients and scenario cues remain explicit in their respective functions;
none have been empirically calibrated.

## Coping, relationships and learning

Public expression uses the projected emotional state after the encounter,
self-control, learned trust and sociability. Possible responses include warmth,
protest, seeking support, distance, and a cautious response. Image management and
self-control can produce congratulations despite comparison-related distress.
This is a bounded heuristic, not general reasoning or a diagnostic rule.

A direct participant can emit one visible reply per simulated hour. Other people
appraise that reply at the next observation phase. Replies never emit more replies,
which bounds the chain. The person's strongest appraised event in an hour chooses
the displayed expression; the single emitted reply belongs to the first eligible
encounter, so it can differ from the later displayed state.

Trust learns toward an evidence estimate with rate `0.08` (bystanders use 30% of
that rate). Affection and resentment also update from personal appraisal. A giver
cannot gain evidence about the recipient's honesty merely by giving help. Another
person's success alone does not decrease trust. Directed relationships are not
implicitly symmetric. Beliefs update more slowly and influence later appraisals.

The six activity choices remain rest, reflection, creative work, contact, help and
confrontation. Their scores now include five-emotion state and learned relationships:
fear can encourage distance, sadness can encourage trusted support, anger can
encourage confrontation, disgust can discourage contact, and joy can support
creative activity. A small seeded exploration term remains. Other people's private
needs are inaccessible; help uses public presentation as an imperfect cue.

## Living conditions

- **Abundance:** affects rest recovery, creative opportunity, attainable safety,
  and personally experienced resource strain.
- **Social safety:** affects attainable personal safety and perceived environmental
  threat. Environmental threat has no human culprit by default.
- **Pressure:** costs energy, reduces perceived coping ability and contributes to
  loss/threat appraisal.

Every four hours, and on the next hour after any condition change, each resident
appraises their own living conditions. These private events have no bystanders.
Environment settings do not overwrite the entire population's emotions with one
shared value. Positive encounters can moderate distress; that effect is itself
an explicit assumption needing calibration.

## Checks and reproducible experiments

Run behavioral/invariant checks with:

```sh
python -m unittest discover -s tests_python -p 'test_engine*.py' -v
python -m humanity.experiments --seeds 12 --population 24 --steps 48 --output report.json
```

Each replicate creates one starting world and forks identical people into secure,
unsafe, scarce and pressured conditions, varying one environmental input at a
time. Seeds, all conditions, outcomes, activity counts, paired mean differences
and standard errors across seeds are saved. Agents within a society are not
counted as independent statistical samples. Seed variability is not uncertainty
about the theory or coefficients. This is a counterfactual characterization,
not causal evidence about actual societies or a complete sensitivity analysis.

A checked-in run is in `docs/experiments/model-0.3.json`. Do not turn its numerical
values into requirements for a real society. In this prototype, unsolicited
positive contact is frequent, needs recover easily and spontaneous conflict is
rare. Aggregate wellbeing therefore approaches its upper bound. Anger and disgust
can remain near zero without explicit harmful events. These are open limitations,
not evidence that scarcity or stress have no social effects in real life.

## Persistence and remaining scope

Snapshots now use format version **2**. Version-1 input is explicitly migrated:
anxiety becomes fear, sadness retains the larger of old sadness and half of envy,
and disgust starts at zero. This is a pragmatic data mapping, not a psychological
claim. Identity, traits, beliefs, needs, experiences and random state are preserved.
Old metric history is cleared because formulas changed. The old automatic session
is backed up before being replaced. New saves cannot run in the legacy browser
engine. Continuation after migration follows new rules, not the old trajectory.

Memories retain one formative record and a bounded recent window (82 total).
Events retain 400 records, metrics 240. References can outlive the corresponding
bounded log. Beliefs and small sociability/self-control adjustments can change;
other traits and values remain fixed. There is no complete narrative memory,
validated mental-health model, economic/resource allocation model, institutional
structure, country model, family system or general human intelligence.
