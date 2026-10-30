"""Different people can find different meanings in the very same event."""

from dataclasses import dataclass, field

from .agents import relationship, remember
from .models import Agent, Event, Factor, PublicState, Relationship, World
from .randomness import clamp, shuffle


@dataclass
class Appraisal:
    joy: float
    envy: float
    suspicion: float
    anxiety: float
    anger: float
    interpretation: str
    expression: str | None = None
    masked: bool = False
    public_text: str = ""
    warmth: float = .5
    factors: list[Factor] = field(default_factory=list)


def appraise(agent: Agent, event: Event, subject: Agent | None) -> Appraisal | None:
    relation = agent.relationships.get(subject.id, Relationship()) if subject else Relationship()
    t = agent.traits
    if event.kind == "achievement" and event.actor_id != agent.id and subject:
        joy = clamp(t.empathy * .35 + relation.affection * .3 + agent.values.care * .18)
        envy = clamp(t.ambition * (1 - agent.needs.esteem) * .65 + relation.resentment * .3 + t.sensitivity * .15)
        suspicion = clamp((1 - agent.beliefs.fairness) * agent.values.fairness * .6 + relation.resentment * .3)
        masked = envy > .26 and (t.impression_management + t.self_control) / 2 > .5
        expression = "celebrate" if masked or joy > envy else "practice" if t.self_control > .5 else "withdraw"
        if suspicion > .35:
            interpretation = "موفقیتش را دیدم، اما دربارهٔ برابر بودن فرصت‌ها مطمئن نیستم."
        elif envy > .3:
            interpretation = "از پیشرفتش خوشحالم، اما خودم را عقب‌مانده احساس می‌کنم."
        else:
            interpretation = "پیشرفت او برایم خوشحال‌کننده و امیدبخش بود."
        expressions = {"celebrate": ("تبریک! از دیدن پیشرفتت خوشحالم.", .88), "practice": ("من هم روی هدفم کار می‌کنم.", .48), "withdraw": ("فعلاً ترجیح می‌دهم تنها باشم.", .25)}
        public_text, warmth = expressions[expression]
        return Appraisal(joy, envy, suspicion, envy * .18, suspicion * .18, interpretation,
                         expression, masked, public_text, warmth,
                         [Factor("همدلی", t.empathy), Factor("مقایسه با خود", t.ambition * (1 - agent.needs.esteem)), Factor("باور به انصاف", agent.beliefs.fairness), Factor("رابطهٔ قبلی", relation.affection), Factor("مدیریت ظاهر", t.impression_management)])
    direct = agent.id in (event.actor_id, event.target_id)
    if event.kind in ("help", "connection", "reconciliation"):
        return Appraisal(.16 if direct else t.empathy * .09, 0, 0, 0, 0,
                         "این تجربه برایم نشانه‌ای از توجه و امکان اعتماد بود." if direct else "دیدن این رفتار، تصویر امیدوارکننده‌تری از این جمع به من داد.", warmth=.7)
    if event.kind == "rejection" and event.target_id == agent.id:
        return None
    if event.kind in ("conflict", "rejection", "crisis"):
        return Appraisal(0, 0, .18 if direct else .03, t.sensitivity * (.16 if direct else .06), agent.values.fairness * .11 if direct else .02,
                         "نپذیرفتن این دعوت را دیدم؛ هنوز علتش را نمی‌دانم." if event.kind == "rejection" else "این اتفاق حس امنیت و اعتمادم را تحت تأثیر قرار داد.", warmth=.3)
    return None


def perceive(world: World, agent: Agent, event: Event):
    subject_id = event.target_id if event.kind == "rejection" or event.actor_id == agent.id else event.actor_id
    subject = world.person(subject_id)
    appraisal = appraise(agent, event, subject)
    if appraisal is None:
        return None
    for key in ("joy", "envy", "anxiety", "anger"):
        setattr(agent.emotions, key, clamp(getattr(agent.emotions, key) + getattr(appraisal, key) * .38))
    direct = agent.id in (event.target_id, event.actor_id)
    positive = event.kind in ("help", "connection", "reconciliation")
    if subject and subject.id != agent.id:
        relation = relationship(agent, subject.id)
        relation.familiarity = clamp(relation.familiarity + .025)
        relation.trust = clamp(relation.trust + (.025 if positive else -appraisal.suspicion * .045) * (1 if direct else .3))
        relation.affection = clamp(relation.affection + (.018 if positive else -appraisal.envy * .008))
        relation.resentment = clamp(relation.resentment + appraisal.anger * .08 - (.018 if positive else 0))
    agent.beliefs.trust = clamp(agent.beliefs.trust + (.003 if positive else -appraisal.anxiety * .012))
    agent.beliefs.fairness = clamp(agent.beliefs.fairness - appraisal.suspicion * .006 + (.001 if positive else 0))
    if appraisal.expression and agent.last_reaction_tick != world.tick:
        agent.public_state = PublicState(appraisal.expression, appraisal.public_text, appraisal.warmth)
        agent.last_reaction_tick = world.tick
    return remember(world, agent, kind="appraisal", event_id=event.id,
                    subject_id=subject.id if subject else event.actor_id,
                    text=event.text, interpretation=appraisal.interpretation,
                    feelings={"joy": appraisal.joy, "envy": appraisal.envy, "anxiety": appraisal.anxiety, "suspicion": appraisal.suspicion},
                    expression=appraisal.expression, public_text=appraisal.public_text,
                    masked=appraisal.masked, factors=appraisal.factors, importance=.7 if direct else .45)


def observe_events(world: World):
    queued = world.pending_events[:]
    world.pending_events.clear()
    recorded = {event.id: event for event in world.events}
    for queued_event in queued:
        event = recorded.get(queued_event.id, queued_event)
        if event.visibility == "private":
            continue
        participants = [a for a in world.agents if a.id in (event.target_id, event.actor_id)]
        nearby = [a for a in world.agents if a.id not in (event.actor_id, event.target_id) and (event.visibility == "public" or a.location_id == event.location_id)]
        observers = participants + shuffle(world, nearby)[:12 if event.visibility == "public" else 4]
        for observer in observers:
            if perceive(world, observer, event):
                event.observers.append(observer.id)
