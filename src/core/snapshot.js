const validNumber = value => typeof value === 'number' && Number.isFinite(value);
const unit = value => validNumber(value) && value >= 0 && value <= 1;
const record = value => value && typeof value === 'object' && !Array.isArray(value);
const check = (condition, message) => { if (!condition) throw new Error(`Invalid snapshot: ${message}`); };

export function validateSnapshot(json) {
  check(typeof json === 'string' && json.length < 32_000_000, 'file too large or unreadable');
  const data = JSON.parse(json);
  check(data.format === 'humanity.sh' && data.version === 1 && record(data.world), 'unsupported format');
  const w = data.world;
  check(w.schemaVersion === 1 && typeof w.seed === 'string' && w.seed.length < 200, 'schema');
  check(Number.isSafeInteger(w.tick) && w.tick >= 0 && Number.isInteger(w.rng) && w.rng >= 0 && w.rng <= 4294967295, 'clock or random state');
  check(Number.isSafeInteger(w.nextEventId) && Number.isSafeInteger(w.nextMemoryId), 'sequence');
  check(record(w.settings) && ['abundance', 'socialSafety', 'pressure'].every(k => unit(w.settings[k])), 'conditions');
  check(Array.isArray(w.agents) && w.agents.length >= 2 && w.agents.length <= 300, 'population');
  check(Array.isArray(w.events) && w.events.length <= 400 && Array.isArray(w.pendingEvents) && w.pendingEvents.length <= 1000 && Array.isArray(w.history) && w.history.length <= 240, 'history');
  check(Array.isArray(w.systemIds) && w.systemIds.every(id => typeof id === 'string'), 'systems');
  const ids = new Set(w.agents.map(a => a.id));
  check(ids.size === w.agents.length && [...ids].every(id => typeof id === 'string' && id.length < 80), 'identifiers');
  for (const a of w.agents) {
    check(record(a.identity) && ['name', 'role', 'background'].every(k => typeof a.identity[k] === 'string' && a.identity[k].length < 4000) && validNumber(a.identity.age), 'identity');
    for (const field of ['traits', 'initialTraits', 'values', 'beliefs', 'needs', 'emotions']) check(record(a[field]) && Object.values(a[field]).every(unit), field);
    for (const [field, keys] of Object.entries({ traits: ['empathy','ambition','sociability','sensitivity','openness','patience','selfControl','impressionManagement'], values: ['care','achievement','fairness','autonomy','belonging','honesty'], beliefs: ['trust','fairness','selfWorth'], needs: ['energy','belonging','safety','esteem'], emotions: ['joy','anxiety','envy','anger','sadness'] })) check(keys.every(k => unit(a[field][k])), field);
    check(record(a.relationships) && Object.entries(a.relationships).every(([id, r]) => ids.has(id) && record(r) && ['trust','affection','resentment','familiarity'].every(k => unit(r[k]))), 'relationships');
    check(Array.isArray(a.memories) && a.memories.length <= 82 && a.memories.every(m => typeof m.text === 'string' && typeof m.interpretation === 'string'), 'memories');
    check(record(a.position) && unit(a.position.x) && unit(a.position.y), 'position');
    check(record(a.publicState) && typeof a.publicState.action === 'string' && typeof a.publicState.text === 'string' && unit(a.publicState.warmth), 'public state');
    check(record(a.goals) && typeof a.goals.immediate === 'string' && typeof a.goals.longTerm === 'string', 'goals');
    if (a.lastDecision) check(record(a.lastDecision) && Array.isArray(a.lastDecision.factors) && a.lastDecision.factors.every(f => typeof f.label === 'string' && validNumber(f.value)) && Array.isArray(a.lastDecision.alternatives), 'decision');
  }
  for (const e of [...w.events, ...w.pendingEvents]) check(record(e) && typeof e.text === 'string' && typeof e.kind === 'string' && Array.isArray(e.observers) && e.observers.every(id => ids.has(id)), 'event');
  for (const h of w.history) check(record(h) && ['tick','wellbeing','trust','gap','joy','anxiety','envy','connections'].every(k => validNumber(h[k])), 'metrics');
  return data;
}
