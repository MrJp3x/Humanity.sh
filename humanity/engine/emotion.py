"""Five emotion algorithms, separated from interpretation and action choice.

Appraisal/coping structure is inspired by EMA (Marsella & Gratch, 2009).
These equations and parameters are project hypotheses, NOT estimates from
that paper or a validated psychological instrument. See docs/model.md.
"""

from dataclasses import dataclass, fields
from math import exp, log

from .models import Emotions
from .randomness import clamp


@dataclass(frozen=True)
class Dimensions:
    benefit: float = 0
    loss: float = 0
    threat: float = 0
    blame: float = 0
    control: float = .5
    violation: float = 0
    affiliation: float = 0
    comparison: float = 0
    suspicion: float = 0


@dataclass(frozen=True)
class EmotionParameters:
    event_gain: float = .34
    recovery_gain: float = .16
    half_life_hours: float = 4
    learning_rate: float = .08


PARAMETERS = EmotionParameters()
EMOTION_KEYS = tuple(f.name for f in fields(Emotions))


def joy_from(d: Dimensions, reactivity: float) -> float:
    return clamp(d.benefit * reactivity)


def sadness_from(d: Dimensions, reactivity: float) -> float:
    return clamp(d.loss * (.45 + .55 * (1 - d.control)) * reactivity)


def fear_from(d: Dimensions, reactivity: float) -> float:
    return clamp(d.threat * (1 - .65 * d.control) * reactivity)


def anger_from(d: Dimensions, reactivity: float) -> float:
    return clamp((d.loss * .65 + d.threat * .35) * d.blame * (.3 + .7 * d.control) * reactivity)


def disgust_from(d: Dimensions, reactivity: float) -> float:
    # Poverty, refusal and another person's success are not moral violations.
    return clamp(d.violation * (.5 + .5 * d.blame) * reactivity)


def response(d: Dimensions, sensitivity: float) -> Emotions:
    reactivity = .5 + sensitivity
    return Emotions(joy_from(d, reactivity), sadness_from(d, reactivity),
                    fear_from(d, reactivity), anger_from(d, reactivity),
                    disgust_from(d, reactivity))


def decay(emotions: Emotions, hours=1, parameters=PARAMETERS):
    # Time is in simulated hours, independent of how many events were observed.
    retention = exp(-log(2) * hours / parameters.half_life_hours)
    for key in EMOTION_KEYS:
        setattr(emotions, key, getattr(emotions, key) * retention)


def integrate(emotions: Emotions, felt: Emotions, dimensions: Dimensions, parameters=PARAMETERS):
    for key in EMOTION_KEYS:
        current = getattr(emotions, key)
        setattr(emotions, key, clamp(current + (1 - current) * parameters.event_gain * getattr(felt, key)))
    relief = dimensions.benefit * (1 - dimensions.threat) * parameters.recovery_gain
    emotions.fear *= 1 - relief
    emotions.sadness *= 1 - relief
    emotions.anger *= 1 - relief * (1 - dimensions.blame)
