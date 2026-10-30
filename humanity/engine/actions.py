"""Observable actions and their outcomes. No GUI or transport code lives here."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Callable

from .agents import relationship, remember
from .catalog import ACTION_LOCATIONS, LOCATIONS
from .events import emit
from .models import Agent, Decision, Position, PublicState, World
from .randomness import between, clamp, random


@dataclass
class ActionContext:
    world: World
    agent: Agent
    target: Agent | None
    decision: Decision


@dataclass
class ActionResult:
    text: str
    kind: str
    visibility: str
    public_text: str
    warmth: float


Action = Callable[[ActionContext], ActionResult | None]


def rest(context: ActionContext) -> ActionResult:
    w, a = context.world, context.agent
    a.needs.energy = clamp(a.needs.energy + .24 * (.5 + w.settings.abundance * .5))
    return ActionResult(f"{a.identity.name} زمانی برای استراحت کنار گذاشت.", "rest", "private", "کمی برای خودم وقت می‌گذارم.", .4)


def reflect(context: ActionContext) -> ActionResult:
    w, a = context.world, context.agent
    a.needs.energy = clamp(a.needs.energy + .09)
    memory = next((m for m in reversed(a.memories) if m.source == "experience"), None)
    a.beliefs.self_worth = clamp(a.beliefs.self_worth + a.traits.openness * .004)
    if memory:
        remember(w, a, kind="reflection", text="دوباره به تجربه‌ای از زندگی‌ام فکر کردم.",
                 interpretation=f"هنوز در حال ارزیابی این برداشت هستم: {memory.interpretation}",
                 subject_id=memory.subject_id, evidence_ids=[memory.id])
    return ActionResult(f"{a.identity.name} در خلوت به تجربه‌هایش فکر کرد.", "reflection", "private", "نیاز دارم کمی فکر کنم.", .35)


def create(context: ActionContext) -> ActionResult:
    w, a = context.world, context.agent
    a.needs.energy = clamp(a.needs.energy - .09)
    success = random(w) < .35 + a.traits.openness * .3 + w.settings.abundance * .25
    if success:
        a.needs.esteem = clamp(a.needs.esteem + .21)
        a.beliefs.self_worth = clamp(a.beliefs.self_worth + .015)
    return ActionResult(
        f"{a.identity.name} در پروژهٔ شخصی‌اش پیشرفت کرد." if success else f"{a.identity.name} تلاش کرد؛ این بار به نتیجهٔ دلخواه نرسید.",
        "achievement" if success else "setback", "local", "بالاخره یک قدم جلو رفتم!" if success else "دوباره تلاش می‌کنم.", .8 if success else .35,
    )


def connect(context: ActionContext) -> ActionResult | None:
    w, a, b = context.world, context.agent, context.target
    if b is None:
        return None
    relation = relationship(b, a.id)
    accepted = random(w) < clamp(.28 + b.traits.sociability * .35 + relation.trust * .35 - b.emotions.fear * .2 - b.emotions.disgust * .15, .08, .95)
    a.needs.energy = clamp(a.needs.energy - .035)
    if accepted:
        a.needs.belonging = clamp(a.needs.belonging + .22)
        b.needs.belonging = clamp(b.needs.belonging + .14)
    return ActionResult(
        f"{a.identity.name} و {b.identity.name} گفت‌وگویی دوستانه داشتند." if accepted else f"{b.identity.name} دعوت {a.identity.name} به گفت‌وگو را نپذیرفت.",
        "connection" if accepted else "rejection", "local", "از این گفت‌وگو خوشحال شدم." if accepted else "شاید وقت دیگری صحبت کنیم.", .78 if accepted else .4,
    )


def help_person(context: ActionContext) -> ActionResult | None:
    a, b = context.agent, context.target
    if b is None:
        return None
    a.needs.energy = clamp(a.needs.energy - .10)
    a.needs.esteem = clamp(a.needs.esteem + .08)
    b.needs.safety = clamp(b.needs.safety + .16)
    b.needs.belonging = clamp(b.needs.belonging + .14)
    return ActionResult(f"{a.identity.name} برای کمک به {b.identity.name} وقت گذاشت.", "help", "local", "اگر بخواهی، کنارت هستم.", .9)


def confront(context: ActionContext) -> ActionResult | None:
    w, a, b = context.world, context.agent, context.target
    if b is None:
        return None
    resolution = random(w) < (a.traits.self_control + b.traits.empathy) * .4
    a.needs.energy = clamp(a.needs.energy - .08)
    insult = not resolution and a.traits.self_control < .35 and a.emotions.anger > .35
    return ActionResult(
        f"{a.identity.name} و {b.identity.name} دربارهٔ دلخوری‌شان صحبت کردند." if resolution else f"{a.identity.name} به {b.identity.name} توهین کرد." if insult else f"{a.identity.name} و {b.identity.name} دچار اختلاف شدند.",
        "reconciliation" if resolution else "insult" if insult else "conflict", "local", "می‌خواهم حرف همدیگر را بفهمیم." if resolution else "با این رفتار موافق نیستم.", .6 if resolution else .1,
    )


def builtin_actions() -> dict[str, Action]:
    return {"rest": rest, "reflect": reflect, "create": create, "connect": connect, "help": help_person, "confront": confront}


def perform_action(world: World, actions: dict[str, Action], agent: Agent, decision: Decision):
    if decision.action_id not in actions:
        raise ValueError(f"Unknown action: {decision.action_id}")
    target = world.person(decision.target_id)
    result = actions[decision.action_id](ActionContext(world, agent, target, decision))
    if result is None:
        return
    place_id = ACTION_LOCATIONS.get(decision.action_id, "home")
    place = next(place for place in LOCATIONS if place["id"] == place_id)
    agent.location_id = place_id
    agent.position = Position(clamp(place["x"] + between(world, -place["width"] * .4, place["width"] * .4), .05, .95),
                              clamp(place["y"] + between(world, -place["height"] * .35, place["height"] * .35), .08, .92))
    agent.public_state = PublicState(decision.action_id, result.public_text, result.warmth)
    event = emit(world, kind=result.kind, text=result.text, actor_id=agent.id,
                 target_id=target.id if target else None, visibility=result.visibility,
                 location_id=agent.location_id, decision=deepcopy(decision))
    remember(world, agent, kind=result.kind, subject_id=target.id if target else agent.id,
             event_id=event.id, text=result.text, interpretation=result.public_text,
             importance=.8 if result.kind in ("achievement", "conflict") else .35)
