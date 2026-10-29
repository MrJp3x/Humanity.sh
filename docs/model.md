# Model assumptions, version 0.1

This document describes implementation choices. These weights are not empirically estimated psychological parameters.

## People

Each person has synthetic identity and background, eight personality dimensions, six value preferences, three beliefs, four needs, and five emotions. These continuous values are bounded to `[0, 1]`. The dimensions form a project-specific vocabulary, not a validated clinical or personality instrument.

Backgrounds introduce initial belief differences. They are synthetic starting conditions rather than rules about real demographic groups. Each person also receives independent trait and value variation. A role such as artist or teacher is descriptive in v0.1; it is not a profession-specific economic model.

## Decisions

Every hour, needs and emotions update first. Each person scores available actions using explicit factors: unmet needs, trait/value preferences, available energy, social history, emotions, environmental conditions, and a small seeded exploration term. The highest-scoring action wins. This is a utility heuristic, not optimal planning or human cognition in full.

Contact candidates are sampled from known people; unfamiliar contacts are sampled if no acquaintances exist. A person's private needs are not available to another person's decision policy. Help decisions use public presentation as an imperfect outward cue. Low trust learned from experience can lower the appeal of contact; envy can contribute to creative effort or reflection.

## Outcomes and observation

Actions may change needs, emotions, and public presentation, and emit factual events. A conversation can be accepted or declined based on the recipient's state and relationship. Creative work can produce an achievement or setback. Help consumes time/energy and supports the recipient. Conflict can resolve or persist.

Participants and bounded nearby witnesses interpret observable events individually. Successful help and contact can increase trust and affection; negative experiences may reduce trust and add resentment. Public success can elicit both joy and envy. Someone with sufficient image-management and self-control may congratulate another person while feeling envy. This is one possible modeled reaction, not an inevitable mapping from a label to an action.

No social media, rumor propagation, deception detection, or global knowledge model is implemented yet. The observer can inspect private state; residents cannot inspect one another's emotion arrays.

## Change over time

Emotions decay each step and can be reinforced by events. Beliefs change in small increments from perceived experiences. Sociability and self-control have small bounded development rules. Other traits and values currently retain their initial values. Reflection records reconsideration and slightly affects self-worth, but does not provide general reasoning or reconstruct a worldview. Long-term goals are initialized and descriptive; immediate goals track current needs.

Memories retain an initial formative memory and a bounded recent window, not a learned semantic memory system. The code limits storage rather than simulating biological forgetting. The log can therefore outlive a particular referenced recent memory or vice versa.

## Environment

- **Abundance:** modifies rest recovery, creative success, and safety.
- **Social safety:** gradually influences felt safety.
- **Pressure:** drains more energy, increases anxiety, and lowers creative-action utility.

These scalar conditions stand for a few explicit mechanisms, not a complete theory of resources or social structure. No money, trade, countries, law, family structure, reproduction, illness, or mortality is present in v0.1.

## Interpreting metrics

- Wellbeing is a bounded heuristic combining need fulfillment and emotion.
- Relationship trust is the mean of directed stored relationships, including initially assigned acquaintances.
- The internal/public gap compares public warmth with joy adjusted by envy and anger. It is an illustrative display index, not a measure of deceit or hypocrisy.
- A familiar connection counts a directed record; mutual connections can count twice.

The same seed and intervention sequence reproduce a run with the same system code. That reproducibility does not establish external validity. Comparing different rules, seeds, group distributions, and eventually empirical observations is necessary before making claims beyond this fictional model.
