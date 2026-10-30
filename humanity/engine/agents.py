"""Creation-time identity and state; memory and relationship operations."""

from copy import deepcopy
from dataclasses import fields

from .catalog import BACKGROUNDS, FIRST_NAMES, LAST_NAMES, LOCATIONS, ROLES
from .models import (Agent, Beliefs, Emotions, Goals, Identity, Memory, Needs,
                     Personality, Position, PublicState, Relationship, Values, World)
from .randomness import between, clamp, pick


def create_agent(world: World, index: int) -> Agent:
    background = pick(world, BACKGROUNDS)
    traits = Personality(**{f.name: between(world, .15, .90) for f in fields(Personality)})
    values = Values(**{f.name: between(world, .2, .95) for f in fields(Values)})
    place = LOCATIONS[index % len(LOCATIONS)]
    family_index = (index + index // len(FIRST_NAMES)) % len(LAST_NAMES)
    name = f"{FIRST_NAMES[index % len(FIRST_NAMES)]} {LAST_NAMES[family_index]}"
    # Keep random draws in a documented order for version-1 compatibility.
    identity = Identity(name, int(between(world, 19, 63)), pick(world, ROLES), background["story"])
    beliefs = Beliefs(clamp(.5 + background["trust"] + between(world, -.08, .08)),
                      clamp(.5 + background["fairness"]), between(world, .35, .8))
    needs = Needs(between(world, .5, .95), between(world, .3, .8), between(world, .45, .85), between(world, .35, .8))
    emotions = Emotions(between(world, .2, .55), between(world, .05, .3), between(world, .01, .15), .02, .08)
    position = Position(clamp(place["x"] + between(world, -.10, .10), .06, .94),
                        clamp(place["y"] + between(world, -.1, .1), .08, .92))
    return Agent(
        id=f"person-{index + 1}", identity=identity, traits=traits,
        initial_traits=deepcopy(traits), values=values, beliefs=beliefs,
        needs=needs, emotions=emotions,
        goals=Goals("پیدا کردن یک فعالیت معنادار", "رشد و ساختن چیزی ارزشمند" if values.achievement > values.belonging else "پیدا کردن رابطه‌های ماندگار"),
        relationships={},
        memories=[Memory(f"origin-{index}", 0, "background", "formative", background["memory"], "بخشی از پیشینهٔ اولیهٔ من است.", None, .8)],
        last_decision=None, public_state=PublicState("reflect", "در حال آشنا شدن با جهان", .5),
        location_id=place["id"], position=position, extensions={},
    )


def relationship(agent: Agent, other_id: str) -> Relationship:
    if other_id not in agent.relationships:
        agent.relationships[other_id] = Relationship()
    return agent.relationships[other_id]


def remember(world: World, agent: Agent, **details) -> Memory:
    defaults = {"tick": world.tick, "source": "experience", "importance": .5}
    memory = Memory(id=f"m-{world.tick}-{agent.id}-{world.next_memory_id}", **(defaults | details))
    world.next_memory_id += 1
    agent.memories.append(memory)
    if len(agent.memories) > 82:
        del agent.memories[1:len(agent.memories) - 81]
    return memory


def wellbeing(agent: Agent) -> float:
    n, e = agent.needs, agent.emotions
    return clamp((n.energy + n.belonging + n.safety + n.esteem) / 4 + e.joy * .12 - e.anxiety * .12 - e.sadness * .1)


def mask_gap(agent: Agent) -> float:
    e = agent.emotions
    return clamp(agent.public_state.warmth - (e.joy - e.envy * .65 - e.anger * .6))
