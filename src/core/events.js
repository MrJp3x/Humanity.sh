// Events describe external facts. Appraisals and memories describe subjective meaning.
export function emit(world, event) {
  const record = { id: `event-${world.nextEventId++}`, tick: world.tick, observers: [], ...event };
  world.events.push(record);
  if (world.events.length > 400) world.events.shift();
  world.pendingEvents.push(record);
  return record;
}
