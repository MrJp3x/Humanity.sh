import { hashSeed, random, shuffle, clamp } from './random.js';
import { emit } from './events.js';
import { createAgent, relationship } from '../domain/agent.js';
import { needsSystem } from '../systems/needs.js';
import { decisionSystem } from '../systems/decision.js';
import { createActions, performAction } from '../systems/actions.js';
import { perceptionSystem } from '../systems/perception.js';
import { developmentSystem, metrics } from '../systems/development.js';
import { validateSnapshot } from './snapshot.js';

export const PHASES = ['before', 'act', 'observe', 'after'];
export const BUILTIN_SYSTEMS = [needsSystem, decisionSystem, perceptionSystem, developmentSystem];

export class Simulation {
  constructor({ seed = 'hello-friend', population = 48, systems = [], actions = [], world = null } = {}) {
    if (!Number.isInteger(population) || population < 2 || population > 300) throw new Error('Population must be between 2 and 300.');
    this.systems = [];
    this.actions = createActions();
    for (const [id, handler] of actions) this.registerAction(id, handler);
    this.world = world ?? {
      schemaVersion: 1, seed: String(seed), rng: hashSeed(seed), tick: 0, agents: [],
      events: [], pendingEvents: [], history: [], nextEventId: 1, nextMemoryId: 1,
      settings: { abundance: .75, socialSafety: .72, pressure: .25 },
      systemIds: [], extensions: {},
    };
    for (const system of [...BUILTIN_SYSTEMS, ...systems]) this.registerSystem(system);
    if (!world) {
      this.world.agents = Array.from({ length: population }, (_, i) => createAgent(this.world, i));
      for (const agent of this.world.agents) {
        const acquaintances = shuffle(this.world, this.world.agents.filter(a => a.id !== agent.id)).slice(0, 4);
        for (const other of acquaintances) {
          const rel = relationship(agent, other.id);
          rel.trust = clamp(agent.beliefs.trust + (random(this.world) - .5) * .25);
          rel.affection = .25 + random(this.world) * .5;
          rel.familiarity = .15 + random(this.world) * .35;
        }
      }
      this.world.history.push(metrics(this.world));
    }
  }
  registerAction(id, handler) {
    if (this.actions.has(id) || typeof handler !== 'function') throw new Error(`Invalid or duplicate action: ${id}`);
    this.actions.set(id, handler);
  }
  registerSystem(system) {
    if (!system.id || !PHASES.includes(system.phase) || typeof system.update !== 'function') throw new Error('Invalid system contract.');
    if (this.systems.some(s => s.id === system.id)) throw new Error(`Duplicate system: ${system.id}`);
    this.systems.push(system);
    this.world.systemIds = this.systems.map(s => s.id);
  }
  step(count = 1) {
    if (!Number.isInteger(count) || count < 1 || count > 1000) throw new Error('Step count must be between 1 and 1000.');
    for (let i = 0; i < count; i++) {
      this.world.tick++;
      for (const phase of PHASES) {
        const systems = this.systems.filter(s => s.phase === phase).sort((a, b) => (a.order ?? 0) - (b.order ?? 0) || a.id.localeCompare(b.id));
        for (const system of systems) system.update({ world: this.world, random: () => random(this.world), emit: event => emit(this.world, event), act: (agent, decision) => performAction(this.world, this.actions, agent, decision) });
      }
    }
    return this.world;
  }
  setCondition(key, value) {
    if (!['abundance','socialSafety','pressure'].includes(key) || !Number.isFinite(value) || value < 0 || value > 1) throw new Error('Invalid world condition.');
    const before = this.world.settings[key];
    this.world.settings[key] = value;
    emit(this.world, { kind: 'intervention', visibility: 'private', text: 'شرایط جهان به دست ناظر تغییر کرد.', change: { key, before, after: value }, actorId: null, targetId: null });
  }
  announceAchievement(agentId) {
    const agent = this.world.agents.find(a => a.id === agentId);
    if (!agent) throw new Error('Agent not found.');
    agent.needs.esteem = clamp(agent.needs.esteem + .15);
    agent.emotions.joy = clamp(agent.emotions.joy + .2);
    for (const observer of this.world.agents) observer.lastReactionTick = -1;
    const event = emit(this.world, { kind: 'achievement', visibility: 'public', actorId: agentId, targetId: null, locationId: agent.locationId, text: `خبر پیشرفت ${agent.identity.name} در جمع منتشر شد.`, origin: 'observer' });
    // Apply observations immediately, once, so a paused experiment is inspectable.
    const queued = this.world.pendingEvents;
    this.world.pendingEvents = [event];
    perceptionSystem.update({ world: this.world });
    this.world.pendingEvents = queued.filter(e => e.id !== event.id);
    return event;
  }
  snapshot() {
    return JSON.stringify({ format: 'humanity.sh', version: 1, world: this.world });
  }
  static fromSnapshot(json, options = {}) {
    const data = validateSnapshot(json);
    const required = [...data.world.systemIds];
    const simulation = new Simulation({ ...options, population: data.world.agents.length, world: data.world });
    if (required.length !== simulation.systems.length || required.some(id => !simulation.systems.some(s => s.id === id))) throw new Error('This world needs a different set of simulation systems.');
    return simulation;
  }
}
