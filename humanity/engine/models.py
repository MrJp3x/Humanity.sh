"""Readable Python state models. Serialization alone handles camelCase JSON names.

The engine uses ordinary dataclasses and snake_case attributes. World state is
owned by one simulation worker; the interface receives independent projections.
"""

from dataclasses import dataclass, field
from typing import Any


def optional():
    return field(default=None, metadata={"omit_none": True})


@dataclass
class Personality:
    empathy: float
    ambition: float
    sociability: float
    sensitivity: float
    openness: float
    patience: float
    self_control: float
    impression_management: float


@dataclass
class Values:
    care: float
    achievement: float
    fairness: float
    autonomy: float
    belonging: float
    honesty: float


@dataclass
class Beliefs:
    trust: float
    fairness: float
    self_worth: float


@dataclass
class Needs:
    energy: float
    belonging: float
    safety: float
    esteem: float


@dataclass
class Emotions:
    joy: float
    anxiety: float
    envy: float
    anger: float
    sadness: float


@dataclass
class Identity:
    name: str
    age: int
    role: str
    background: str


@dataclass
class Goals:
    immediate: str
    long_term: str


@dataclass
class Position:
    x: float
    y: float


@dataclass
class Relationship:
    trust: float = 0.5
    affection: float = 0.45
    resentment: float = 0.0
    familiarity: float = 0.0


@dataclass
class PublicState:
    action: str
    text: str
    warmth: float


@dataclass
class Factor:
    label: str
    value: float


@dataclass
class Alternative:
    id: str
    score: float


@dataclass
class Decision:
    tick: int
    action_id: str
    target_id: str | None
    score: float
    factors: list[Factor]
    alternatives: list[Alternative]
    memory_ids: list[str]


@dataclass
class Memory:
    id: str
    tick: int
    source: str
    kind: str
    text: str
    interpretation: str
    subject_id: str | None
    importance: float
    event_id: str | None = optional()
    feelings: dict[str, float] | None = optional()
    expression: str | None = optional()
    public_text: str | None = optional()
    masked: bool | None = optional()
    factors: list[Factor] | None = optional()
    evidence_ids: list[str] | None = optional()


@dataclass
class Agent:
    id: str
    identity: Identity
    traits: Personality
    initial_traits: Personality
    values: Values
    beliefs: Beliefs
    needs: Needs
    emotions: Emotions
    goals: Goals
    relationships: dict[str, Relationship]
    memories: list[Memory]
    last_decision: Decision | None
    public_state: PublicState
    location_id: str
    position: Position
    extensions: dict[str, Any]
    last_reaction_tick: int | None = optional()


@dataclass
class Event:
    id: str
    tick: int
    kind: str
    text: str
    visibility: str
    actor_id: str | None = None
    target_id: str | None = None
    observers: list[str] = field(default_factory=list)
    location_id: str | None = optional()
    decision: Decision | None = optional()
    origin: str | None = optional()
    change: dict[str, Any] | None = optional()


@dataclass
class Metrics:
    tick: int
    wellbeing: float
    trust: float
    gap: float
    connections: int
    joy: float
    anxiety: float
    envy: float


@dataclass
class Conditions:
    abundance: float = 0.75
    social_safety: float = 0.72
    pressure: float = 0.25


@dataclass
class World:
    seed: str
    rng: int
    schema_version: int = 1
    tick: int = 0
    agents: list[Agent] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    pending_events: list[Event] = field(default_factory=list)
    history: list[Metrics] = field(default_factory=list)
    next_event_id: int = 1
    next_memory_id: int = 1
    settings: Conditions = field(default_factory=Conditions)
    system_ids: list[str] = field(default_factory=list)
    extensions: dict[str, Any] = field(default_factory=dict)

    def person(self, person_id: str | None) -> Agent | None:
        return next((person for person in self.agents if person.id == person_id), None)
