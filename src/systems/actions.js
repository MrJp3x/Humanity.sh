import { clamp, pick, random, range } from '../core/random.js';
import { relationship, remember } from '../domain/agent.js';
import { actionLocations, locations } from '../domain/catalog.js';
import { emit } from '../core/events.js';

function move(world, agent, actionId) {
  const place = locations.find(location => location.id === actionLocations[actionId]) ?? locations[0];
  agent.locationId = place.id;
  agent.position = { x: clamp(place.x + range(world, -place.width * .4, place.width * .4), .05, .95), y: clamp(place.y + range(world, -place.height * .35, place.height * .35), .08, .92) };
}

export function createActions() {
  return new Map([
    ['rest', ({ world, agent }) => {
      agent.needs.energy = clamp(agent.needs.energy + .24 * (.5 + world.settings.abundance * .5));
      agent.emotions.anxiety *= .87;
      return { text: `${agent.identity.name} زمانی برای استراحت کنار گذاشت.`, kind: 'rest', visibility: 'private', publicText: 'کمی برای خودم وقت می‌گذارم.', warmth: .4 };
    }],
    ['reflect', ({ world, agent }) => {
      agent.needs.energy = clamp(agent.needs.energy + .09);
      agent.emotions.anxiety *= .78;
      const memory = agent.memories.filter(m => m.source === 'experience').at(-1);
      agent.beliefs.selfWorth = clamp(agent.beliefs.selfWorth + agent.traits.openness * .004);
      if (memory) remember(agent, { kind: 'reflection', text: 'دوباره به تجربه‌ای از زندگی‌ام فکر کردم.', interpretation: `هنوز در حال ارزیابی این برداشت هستم: ${memory.interpretation}`, subjectId: memory.subjectId, evidenceIds: [memory.id] }, world);
      return { text: `${agent.identity.name} در خلوت به تجربه‌هایش فکر کرد.`, kind: 'reflection', visibility: 'private', publicText: 'نیاز دارم کمی فکر کنم.', warmth: .35 };
    }],
    ['create', ({ world, agent }) => {
      agent.needs.energy = clamp(agent.needs.energy - .09);
      const success = random(world) < .35 + agent.traits.openness * .3 + world.settings.abundance * .25;
      if (success) {
        agent.needs.esteem = clamp(agent.needs.esteem + .21);
        agent.emotions.joy = clamp(agent.emotions.joy + .28);
        agent.beliefs.selfWorth = clamp(agent.beliefs.selfWorth + .015);
      } else {
        agent.emotions.sadness = clamp(agent.emotions.sadness + .13 * agent.traits.sensitivity);
      }
      return { text: success ? `${agent.identity.name} در پروژهٔ شخصی‌اش پیشرفت کرد.` : `${agent.identity.name} تلاش کرد؛ این بار به نتیجهٔ دلخواه نرسید.`, kind: success ? 'achievement' : 'setback', visibility: 'local', publicText: success ? 'بالاخره یک قدم جلو رفتم!' : 'دوباره تلاش می‌کنم.', warmth: success ? .8 : .35 };
    }],
    ['connect', ({ world, agent, target }) => {
      if (!target) return null;
      const rel = relationship(target, agent.id);
      const accepted = random(world) < clamp(.28 + target.traits.sociability * .35 + rel.trust * .35 - target.emotions.anxiety * .2, .08, .95);
      agent.needs.energy = clamp(agent.needs.energy - .035);
      if (accepted) {
        agent.needs.belonging = clamp(agent.needs.belonging + .22);
        target.needs.belonging = clamp(target.needs.belonging + .14);
        agent.emotions.joy = clamp(agent.emotions.joy + .1);
        target.emotions.joy = clamp(target.emotions.joy + .07);
      }
      return { text: accepted ? `${agent.identity.name} و ${target.identity.name} گفت‌وگویی دوستانه داشتند.` : `${target.identity.name} دعوت ${agent.identity.name} به گفت‌وگو را نپذیرفت.`, kind: accepted ? 'connection' : 'rejection', visibility: 'local', publicText: accepted ? 'از این گفت‌وگو خوشحال شدم.' : 'شاید وقت دیگری صحبت کنیم.', warmth: accepted ? .78 : .4 };
    }],
    ['help', ({ world, agent, target }) => {
      if (!target) return null;
      agent.needs.energy = clamp(agent.needs.energy - .10);
      agent.needs.esteem = clamp(agent.needs.esteem + .08);
      target.needs.safety = clamp(target.needs.safety + .16);
      target.needs.belonging = clamp(target.needs.belonging + .14);
      return { text: `${agent.identity.name} برای کمک به ${target.identity.name} وقت گذاشت.`, kind: 'help', visibility: 'local', publicText: 'اگر بخواهی، کنارت هستم.', warmth: .9 };
    }],
    ['confront', ({ world, agent, target }) => {
      if (!target) return null;
      const resolution = random(world) < (agent.traits.selfControl + target.traits.empathy) * .4;
      agent.needs.energy = clamp(agent.needs.energy - .08);
      return { text: resolution ? `${agent.identity.name} و ${target.identity.name} دربارهٔ دلخوری‌شان صحبت کردند.` : `${agent.identity.name} و ${target.identity.name} دچار اختلاف شدند.`, kind: resolution ? 'reconciliation' : 'conflict', visibility: 'local', publicText: resolution ? 'می‌خواهم حرف همدیگر را بفهمیم.' : 'با این رفتار موافق نیستم.', warmth: resolution ? .6 : .1 };
    }],
  ]);
}

export function performAction(world, actions, agent, decision) {
  const handler = actions.get(decision.actionId);
  if (!handler) throw new Error(`Unknown action: ${decision.actionId}`);
  const target = world.agents.find(a => a.id === decision.targetId);
  const result = handler({ world, agent, target, decision });
  if (!result) return;
  move(world, agent, decision.actionId);
  agent.publicState = { action: decision.actionId, text: result.publicText, warmth: result.warmth };
  const event = emit(world, { kind: result.kind, text: result.text, actorId: agent.id, targetId: target?.id ?? null, visibility: result.visibility, locationId: agent.locationId, decision: structuredClone(decision) });
  remember(agent, { kind: result.kind, subjectId: target?.id ?? agent.id, eventId: event.id, text: result.text, interpretation: result.publicText, importance: ['achievement', 'conflict'].includes(result.kind) ? .8 : .35 }, world);
}
