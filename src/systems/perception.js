import { clamp, random, shuffle } from '../core/random.js';
import { relationship, remember } from '../domain/agent.js';

// Pure appraisal: the same external event can acquire a different meaning for each person.
export function appraise(agent, event, subject) {
  const relation = agent.relationships[subject?.id] ?? { affection: .45, trust: .5, resentment: 0 };
  const t = agent.traits;
  if (event.kind === 'achievement' && event.actorId !== agent.id && subject) {
    const joy = clamp(t.empathy * .35 + relation.affection * .3 + agent.values.care * .18);
    const envy = clamp(t.ambition * (1 - agent.needs.esteem) * .65 + relation.resentment * .3 + t.sensitivity * .15);
    const suspicion = clamp((1 - agent.beliefs.fairness) * agent.values.fairness * .6 + relation.resentment * .3);
    const masked = envy > .26 && (t.impressionManagement + t.selfControl) / 2 > .5;
    const expression = masked || joy > envy ? 'celebrate' : (t.selfControl > .5 ? 'practice' : 'withdraw');
    const interpretation = suspicion > .35
      ? 'موفقیتش را دیدم، اما دربارهٔ برابر بودن فرصت‌ها مطمئن نیستم.'
      : envy > .3 ? 'از پیشرفتش خوشحالم، اما خودم را عقب‌مانده احساس می‌کنم.' : 'پیشرفت او برایم خوشحال‌کننده و امیدبخش بود.';
    return { joy, envy, suspicion, anxiety: envy * .18, anger: suspicion * .18, expression, masked, interpretation,
      publicText: expression === 'celebrate' ? 'تبریک! از دیدن پیشرفتت خوشحالم.' : expression === 'practice' ? 'من هم روی هدفم کار می‌کنم.' : 'فعلاً ترجیح می‌دهم تنها باشم.',
      warmth: expression === 'celebrate' ? .88 : expression === 'practice' ? .48 : .25,
      factors: [{ label: 'همدلی', value: t.empathy }, { label: 'مقایسه با خود', value: t.ambition * (1 - agent.needs.esteem) }, { label: 'باور به انصاف', value: agent.beliefs.fairness }, { label: 'رابطهٔ قبلی', value: relation.affection }, { label: 'مدیریت ظاهر', value: t.impressionManagement }],
    };
  }
  const direct = event.actorId === agent.id || event.targetId === agent.id;
  if (['help', 'connection', 'reconciliation'].includes(event.kind)) return {
    joy: direct ? .16 : t.empathy * .09, envy: 0, suspicion: 0, anxiety: 0, anger: 0,
    interpretation: direct ? 'این تجربه برایم نشانه‌ای از توجه و امکان اعتماد بود.' : 'دیدن این رفتار، تصویر امیدوارکننده‌تری از این جمع به من داد.',
    expression: null, masked: false, publicText: '', warmth: .7, factors: [],
  };
  if (event.kind === 'rejection' && event.targetId === agent.id) return null;
  if (['conflict', 'rejection', 'crisis'].includes(event.kind)) return {
    joy: 0, envy: 0, suspicion: direct ? .18 : .03, anxiety: t.sensitivity * (direct ? .16 : .06), anger: direct ? agent.values.fairness * .11 : .02,
    interpretation: event.kind === 'rejection' ? 'نپذیرفتن این دعوت را دیدم؛ هنوز علتش را نمی‌دانم.' : 'این اتفاق حس امنیت و اعتمادم را تحت تأثیر قرار داد.',
    expression: null, masked: false, publicText: '', warmth: .3, factors: [],
  };
  return null;
}

export function perceive(world, agent, event) {
  const subjectId = event.kind === 'rejection' ? event.targetId : event.actorId === agent.id ? event.targetId : event.actorId;
  const subject = world.agents.find(person => person.id === subjectId);
  const appraisal = appraise(agent, event, subject);
  if (!appraisal) return null;
  for (const key of ['joy', 'envy', 'anxiety', 'anger']) agent.emotions[key] = clamp(agent.emotions[key] + appraisal[key] * .38);
  const direct = event.targetId === agent.id || event.actorId === agent.id;
  const positive = ['help', 'connection', 'reconciliation'].includes(event.kind);
  if (subject && subject.id !== agent.id) {
    const rel = relationship(agent, subject.id);
    rel.familiarity = clamp(rel.familiarity + .025);
    rel.trust = clamp(rel.trust + (positive ? .025 : -appraisal.suspicion * .045) * (direct ? 1 : .3));
    rel.affection = clamp(rel.affection + (positive ? .018 : -appraisal.envy * .008));
    rel.resentment = clamp(rel.resentment + appraisal.anger * .08 - (positive ? .018 : 0));
  }
  agent.beliefs.trust = clamp(agent.beliefs.trust + (positive ? .003 : -appraisal.anxiety * .012));
  agent.beliefs.fairness = clamp(agent.beliefs.fairness - appraisal.suspicion * .006 + (positive ? .001 : 0));
  if (appraisal.expression && agent.lastReactionTick !== world.tick) {
    agent.publicState = { action: appraisal.expression, text: appraisal.publicText, warmth: appraisal.warmth };
    agent.lastReactionTick = world.tick;
  }
  const memory = remember(agent, {
    kind: 'appraisal', eventId: event.id, subjectId: subject?.id ?? event.actorId,
    text: event.text, interpretation: appraisal.interpretation,
    feelings: { joy: appraisal.joy, envy: appraisal.envy, anxiety: appraisal.anxiety, suspicion: appraisal.suspicion },
    expression: appraisal.expression, publicText: appraisal.publicText, masked: appraisal.masked,
    factors: appraisal.factors, importance: direct ? .7 : .45,
  }, world);
  return memory;
}

export const perceptionSystem = {
  id: 'perception', phase: 'observe', order: 10,
  update({ world }) {
    // Remove only this phase's delivered events. Events emitted by later systems
    // remain queued for the next hour instead of being silently discarded.
    const events = world.pendingEvents.splice(0);
    for (const event of events) {
      if (event.visibility === 'private') continue;
      const participants = world.agents.filter(a => a.id === event.targetId || a.id === event.actorId);
      const nearby = world.agents.filter(a => a.id !== event.actorId && a.id !== event.targetId && (event.visibility === 'public' || a.locationId === event.locationId));
      const observers = [...participants, ...shuffle(world, nearby).slice(0, event.visibility === 'public' ? 12 : 4)];
      for (const observer of observers) {
        if (perceive(world, observer, event)) event.observers.push(observer.id);
      }
    }
  },
};
