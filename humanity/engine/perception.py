"""Fact → personal appraisal → five emotions → public coping → learning.

Only the observer's own beliefs and directed relationship supply history.
Another person's private emotions and intentions are never readable inputs.
"""

from copy import deepcopy
from dataclasses import asdict, dataclass

from .agents import relationship, remember
from .emotion import Dimensions, PARAMETERS, integrate, response
from .events import emit
from .models import Agent, Emotions, Event, Factor, PublicState, Relationship, World
from .randomness import clamp, shuffle


@dataclass(frozen=True)
class Cues:
    benefit: float = 0
    loss: float = 0
    threat: float = 0
    violation: float = 0
    responsibility: float = 0
    affiliation: float = 0
    certainty: float = 1


# Explicit scenario encodings, not universal psychological constants.
SOCIAL_CUES = {
    "help": Cues(benefit=.65, affiliation=.8),
    "connection": Cues(benefit=.45, affiliation=.65),
    "reconciliation": Cues(benefit=.5, affiliation=.6),
    "rejection": Cues(loss=.45, threat=.12, certainty=.35),
    "conflict": Cues(loss=.5, threat=.45, responsibility=.45, certainty=.65),
    "insult": Cues(loss=.6, threat=.35, violation=.8, responsibility=1),
    "betrayal": Cues(loss=.7, threat=.4, violation=1, responsibility=1),
    "crisis": Cues(loss=.6, threat=.9),
    "setback": Cues(loss=.6),
    "rest": Cues(benefit=.2),
    "reflection": Cues(benefit=.15),
}


@dataclass
class Appraisal:
    dimensions: Dimensions
    feelings: Emotions
    interpretation: str
    expression: str
    public_text: str
    warmth: float
    masked: bool
    reaction_reason: str
    factors: list[Factor]


def subject_for(world: World, agent: Agent, event: Event):
    # In a rejection, actor is inviter and target is the person declining.
    person_id = event.target_id if event.actor_id == agent.id else event.actor_id
    return world.person(person_id)


def dimensions_for(agent: Agent, event: Event, subject: Agent | None) -> Dimensions | None:
    t, v, n, b = agent.traits, agent.values, agent.needs, agent.beliefs
    relation = agent.relationships.get(subject.id, Relationship()) if subject else Relationship()
    control = clamp(.15 + t.self_control * .5 + n.energy * .2 + b.self_worth * .15)
    if event.kind == "living_conditions":
        change = event.change or {}
        strain = (1 - change["abundance"]) * (.4 + .6 * (1 - n.energy))
        danger = (1 - change["socialSafety"]) * (.35 + .65 * (1 - n.safety))
        pressure = change["pressure"] * (.35 + .65 * (1 - n.energy))
        return Dimensions(
            benefit=(change["abundance"] * .45 + change["socialSafety"] * .35) * (1 - .8 * change["pressure"]) * .35,
            loss=clamp(strain * .5 + pressure * .35),
            threat=clamp(danger * (.7 + (1 - b.trust) * .3) + pressure * .3),
            control=control * (1 - pressure * .5),
        )
    if event.kind == "achievement":
        if event.actor_id == agent.id:
            return Dimensions(benefit=.45 + v.achievement * .5, control=control)
        if subject is None:
            return None
        comparison = t.ambition * v.achievement * (1 - n.esteem)
        suspicion = (1 - b.fairness) * v.fairness
        return Dimensions(
            benefit=clamp(t.empathy * v.care * .65 + relation.affection * .35),
            loss=clamp(comparison * (.8 + suspicion * .2)), threat=comparison * .18,
            control=control * (.65 + b.fairness * .35),
            comparison=comparison, suspicion=suspicion,
        )
    if event.kind == "rejection" and event.target_id == agent.id:
        return None
    if event.actor_id == agent.id and event.kind in ("insult", "betrayal"):
        return None
    if event.kind == "help" and event.actor_id == agent.id:
        return Dimensions(benefit=v.care * t.empathy * .4, control=control)
    cues = SOCIAL_CUES.get(event.kind)
    if event.kind == "response":
        if event.actor_id == agent.id:
            return None
        reaction = (event.change or {}).get("reaction")
        cues = {"celebrate": Cues(benefit=.25, affiliation=.3),
                "appreciate": Cues(benefit=.3, affiliation=.4),
                "support": Cues(),
                "protest": Cues(loss=.2, threat=.12, certainty=.5),
                "withdraw": Cues(loss=.15, certainty=.25),
                "polite": Cues(benefit=.1, affiliation=.1)}.get(reaction)
    if cues is None:
        return None
    direct = agent.id in (event.actor_id, event.target_id)
    relevance = 1 if direct else t.empathy * v.care * .55
    trust = (relation.trust + b.trust) / 2
    moral_weight = v.honesty if event.kind == "betrayal" else (v.care + v.fairness) / 2
    esteem_relevance = .5 + (1 - n.esteem) * .5 if event.kind in ("setback", "insult") else 1
    return Dimensions(
        benefit=cues.benefit * relevance * (.5 + v.belonging * .25 + trust * .25),
        loss=clamp(cues.loss * relevance * esteem_relevance * (.7 + (1 - b.self_worth) * .3)),
        threat=clamp(cues.threat * relevance * (.65 + (1 - trust) * .35)),
        blame=cues.responsibility * cues.certainty * (.6 + (1 - trust) * .4),
        control=control,
        violation=cues.violation * moral_weight * (1 if direct else .7),
        affiliation=cues.affiliation * relevance,
        suspicion=(1 - trust) * (1 - cues.certainty),
    )


def choose_expression(agent: Agent, event: Event, d: Dimensions, f: Emotions):
    if event.kind in ("rest", "reflection"):
        return ("rest" if event.kind == "rest" else "reflect"), "کمی برای خودم وقت می‌گذارم.", .45, False, "برای بازیابی توانم زمانی را به خودم اختصاص دادم."
    negative = max(f.sadness, f.fear, f.anger, f.disgust)
    mask = (d.comparison > .25 and negative > .18
            and agent.traits.impression_management * agent.traits.self_control > .45)
    if mask:
        return "celebrate", "تبریک! از پیشرفتت خوشحالم.", .85, True, "مقایسه با خودم ناراحتم کرد؛ برای حفظ رابطه ظاهر گرمی نشان می‌دهم."
    if d.violation > .2 and f.disgust > .12:
        return "withdraw", "ترجیح می‌دهم از این رفتار فاصله بگیرم.", .15, False, "این رفتار با ارزش‌هایم ناسازگار بود؛ فاصله می‌گیرم."
    if d.blame > .1 and f.anger > .1 and f.anger > f.fear:
        text = "این رفتار ناراحتم کرد؛ می‌خواهم درباره‌اش صحبت کنیم." if agent.traits.self_control > .5 else "از این رفتارت عصبانی‌ام!"
        return "protest", text, .3, False, "آسیب را به رفتار طرف مقابل نسبت دادم و امکان اعتراض می‌بینم."
    if (d.loss > .15 or d.threat > .15 or negative > f.joy) and negative > .1:
        if agent.traits.sociability * agent.beliefs.trust > .3:
            return "support", "دوست دارم با کسی که اعتماد دارم صحبت کنم.", .45, False, "ناراحتم؛ برای کنار آمدن با آن دنبال همراه می‌گردم."
        return "withdraw", "فعلاً به کمی فاصله و آرامش نیاز دارم.", .25, False, "ناراحتی یا تهدید را بیشتر از توان فعلی‌ام احساس کردم؛ فاصله می‌گیرم."
    if f.joy > .08:
        if event.kind == "living_conditions":
            return "appreciate", "فعلاً از شرایط زندگی‌ام راضی‌ام.", .7, False, "امکانات و امنیت فعلی را برای نیازهایم کافی دیدم."
        if event.kind == "achievement":
            if event.actor_id == agent.id:
                return "celebrate", "از پیشرفتم خوشحالم.", .85, False, "به هدف شخصی‌ام نزدیک شدم و خوشحالم."
            return "celebrate", "از دیدن این پیشرفت خوشحالم.", .85, False, "این اتفاق را مثبت دیدم و خوشحالی‌ام را نشان می‌دهم."
        return "appreciate", "از این همراهی خوشحالم.", .8, False, "این تجربه را نشانه‌ای مثبت دیدم و پاسخ گرم می‌دهم."
    return "polite", "متوجه شدم؛ کمی فکر می‌کنم.", .5, False, "اثر این اتفاق برایم کم یا نامطمئن بود؛ واکنش محتاطانه نشان می‌دهم."


def appraise(agent: Agent, event: Event, subject: Agent | None) -> Appraisal | None:
    d = dimensions_for(agent, event, subject)
    if d is None:
        return None
    feelings = response(d, agent.traits.sensitivity)
    projected = deepcopy(agent.emotions)
    integrate(projected, feelings, d)
    expression, public_text, warmth, masked, reason = choose_expression(agent, event, d, projected)
    if d.comparison > .25:
        interpretation = "پیشرفت او را با وضعیت خودم مقایسه کردم؛ احساس عقب‌ماندن دارم."
    elif event.kind == "rejection":
        interpretation = "دعوتم پذیرفته نشد و ناراحتم؛ دربارهٔ علت یا قصد او مطمئن نیستم."
    elif d.violation > .2:
        interpretation = "رفتار مشاهده‌شده با ارزش‌های شخصی من سازگار نبود."
    elif d.threat > d.benefit and d.threat > .1:
        interpretation = "این موقعیت را برای امنیت و آرامشم تهدیدآمیز دیدم."
    elif d.loss > d.benefit and d.loss > .1:
        interpretation = "این اتفاق را مانعی برای نیاز یا هدفم دیدم."
    else:
        interpretation = "این اتفاق برای نیازها یا رابطه‌هایم امیدوارکننده بود."
    if event.kind == "achievement" and d.suspicion > .5:
        interpretation += " با پیشینه‌ای که دارم دربارهٔ برابری فرصت‌ها تردید دارم؛ شاهدی بر بی‌انصافی در این رویداد ندارم."
    return Appraisal(d, feelings, interpretation, expression, public_text, warmth, masked, reason,
                     [Factor("حساسیت عاطفی", agent.traits.sensitivity), Factor("توان کنار آمدن", d.control),
                      Factor("سود شخصی یا همدلانه", d.benefit), Factor("زیان برداشت‌شده", d.loss),
                      Factor("تهدید برداشت‌شده", d.threat), Factor("ناسازگاری با ارزش‌ها", d.violation)])


def learn(agent: Agent, event: Event, subject: Agent | None, appraisal: Appraisal):
    d = appraisal.dimensions
    if subject is None or subject.id == agent.id:
        return
    if event.kind == "help" and event.actor_id == agent.id:
        return  # Giving help is not evidence about its recipient's conduct.
    relation = relationship(agent, subject.id)
    relation.familiarity = clamp(relation.familiarity + .025)
    if event.kind == "achievement":
        return  # Achievement provides no evidence about someone's honesty.
    relevance = 1 if agent.id in (event.actor_id, event.target_id) else .3
    evidence = clamp(.5 + d.affiliation * .45 - d.blame * d.loss * .45 - d.violation * .4)
    rate = PARAMETERS.learning_rate * relevance
    relation.trust = clamp(relation.trust + rate * (evidence - relation.trust))
    relation.affection = clamp(relation.affection + rate * (d.benefit - d.loss * .5))
    relation.resentment = clamp(relation.resentment + rate * (appraisal.feelings.anger + d.violation * .4 - d.affiliation * .4))
    agent.beliefs.trust = clamp(agent.beliefs.trust + rate * .1 * (evidence - agent.beliefs.trust))
    agent.beliefs.fairness = clamp(agent.beliefs.fairness + rate * .05 * (1 - d.violation - agent.beliefs.fairness))


def perceive(world: World, agent: Agent, event: Event):
    subject = subject_for(world, agent, event)
    appraisal = appraise(agent, event, subject)
    if appraisal is None:
        return None
    before = asdict(agent.emotions)
    integrate(agent.emotions, appraisal.feelings, appraisal.dimensions)
    learn(agent, event, subject, appraisal)
    salience = max(asdict(appraisal.feelings).values())
    recent = agent.extensions.get("emotionModel", {})
    displayed = recent.get("tick") != world.tick or salience >= recent.get("salience", 0)
    if displayed:
        agent.public_state = PublicState(appraisal.expression, appraisal.public_text, appraisal.warmth)
        agent.extensions["emotionModel"] = {"tick": world.tick, "salience": salience}
    memory = remember(world, agent, kind="appraisal", event_id=event.id,
                      subject_id=subject.id if subject else event.actor_id,
                      text=event.text, interpretation=appraisal.interpretation,
                      feelings=asdict(appraisal.feelings), expression=appraisal.expression,
                      public_text=appraisal.public_text, masked=appraisal.masked,
                      factors=appraisal.factors, importance=clamp(.25 + salience * .6),
                      appraisal=asdict(appraisal.dimensions), emotions_before=before,
                      emotions_after=asdict(agent.emotions), reaction_reason=appraisal.reaction_reason)
    if displayed:
        agent.extensions["emotionModel"]["memoryId"] = memory.id
    direct = agent.id in (event.actor_id, event.target_id)
    # One visible reply/person/hour. Replies are appraised next hour, but never
    # generate further replies, preventing infinite emotional reaction chains.
    recipient = event.target_id == agent.id or event.kind in ("connection", "conflict", "reconciliation", "rejection")
    if (direct and recipient and subject and subject.id != agent.id and event.visibility != "private"
            and event.kind not in ("response", "achievement") and agent.last_reaction_tick != world.tick):
        emit(world, kind="response", visibility="local", actor_id=agent.id, target_id=subject.id,
             location_id=event.location_id, text=f"{agent.identity.name}: «{appraisal.public_text}»",
             change={"causeId": event.id, "reaction": appraisal.expression})
        agent.last_reaction_tick = world.tick
    return memory


def observe_events(world: World):
    queued = world.pending_events[:]
    world.pending_events.clear()
    recorded = {event.id: event for event in world.events}
    for queued_event in queued:
        event = recorded.get(queued_event.id, queued_event)
        if event.visibility == "private":
            owner = world.person(event.target_id or event.actor_id)
            observers = [owner] if owner else []
        else:
            participants = [a for a in world.agents if a.id in (event.target_id, event.actor_id)]
            nearby = [a for a in world.agents if a.id not in (event.actor_id, event.target_id) and (event.visibility == "public" or a.location_id == event.location_id)]
            observers = participants + shuffle(world, nearby)[:12 if event.visibility == "public" else 4]
        for observer in observers:
            if perceive(world, observer, event) and observer.id not in event.observers:
                event.observers.append(observer.id)
