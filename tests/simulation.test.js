import test from 'node:test';
import assert from 'node:assert/strict';
import { Simulation } from '../src/core/simulation.js';
import { appraise, perceive } from '../src/systems/perception.js';
import { relationship } from '../src/domain/agent.js';
import { decide } from '../src/systems/decision.js';

test('same seed and intervention sequence produce the same world', () => {
  const a = new Simulation({ seed:'repeatable', population:24 });
  const b = new Simulation({ seed:'repeatable', population:24 });
  for(const sim of [a,b]){sim.step(10);sim.setCondition('pressure',.8);sim.announceAchievement('person-3');sim.step(15);}
  assert.equal(a.snapshot(),b.snapshot());
  const other = new Simulation({seed:'another',population:24});other.step(25);
  assert.notEqual(a.snapshot(),other.snapshot());
});

test('snapshot restoration preserves the random stream and future history', () => {
  const original = new Simulation({seed:'branch',population:24});
  original.step(18);original.setCondition('abundance',.3);
  const restored = Simulation.fromSnapshot(original.snapshot());
  original.step(24);restored.step(24);
  assert.equal(original.snapshot(),restored.snapshot());
});

test('one event can produce different appraisals and simultaneous joy and envy', () => {
  const sim = new Simulation({seed:'minds',population:3});
  const [subject,first,second] = sim.world.agents;
  first.traits.empathy=.95;first.traits.ambition=.1;first.traits.sensitivity=.1;first.needs.esteem=.9;
  second.traits.empathy=.7;second.traits.ambition=.95;second.traits.sensitivity=.8;second.needs.esteem=.1;
  second.traits.impressionManagement=.95;second.traits.selfControl=.9;
  const event = {id:'shared-fact',kind:'achievement',actorId:subject.id,targetId:null,text:'یک پیشرفت مشترک مشاهده شد.'};
  const a=appraise(first,event,subject),b=appraise(second,event,subject);
  assert.ok(b.envy>a.envy);
  assert.ok(b.joy>0&&b.envy>.3);
  assert.equal(b.expression,'celebrate');
  assert.equal(b.masked,true);
  const memory=perceive(sim.world,second,event);
  assert.equal(memory.eventId,event.id);
  assert.equal(second.publicState.action,'celebrate');
  assert.ok(second.emotions.envy>0);
});

test('personal history changes the interpretation of the same achievement', () => {
  const sim=new Simulation({population:2});
  const [subject,observer]=sim.world.agents;
  observer.values.fairness=1;
  const event={kind:'achievement',actorId:subject.id};
  observer.beliefs.fairness=.95;const trusting=appraise(observer,event,subject);
  observer.beliefs.fairness=.05;const doubtful=appraise(observer,event,subject);
  assert.ok(doubtful.suspicion>trusting.suspicion);
  assert.match(doubtful.interpretation,/فرصت/);
});

test('relationships are directional and an observed experience changes later choices', () => {
  const sim=new Simulation({population:2});
  const [a,b]=sim.world.agents;
  const ab=relationship(a,b.id),ba=relationship(b,a.id);
  const before=ba.trust;
  const beliefBefore=a.beliefs.trust;
  perceive(sim.world,a,{id:'help-1',kind:'help',actorId:b.id,targetId:a.id,text:'کمکی انجام شد.'});
  assert.equal(ba.trust,before);
  assert.ok(a.beliefs.trust>beliefBefore);
  ab.trust=.1;const low=decide(sim.world,a);
  ab.trust=.9;const high=decide(sim.world,a);
  const lowConnection=low.actionId==='connect'?low:low.alternatives.find(o=>o.id==='connect');
  const highConnection=high.actionId==='connect'?high:high.alternatives.find(o=>o.id==='connect');
  assert.ok(lowConnection&&highConnection);
  assert.ok(highConnection.score>lowConnection.score);
});

test('private rest and reflection do not become public knowledge', () => {
  const sim=new Simulation({population:24});sim.step(8);
  for(const event of sim.world.events.filter(e=>e.visibility==='private'))assert.equal(event.observers.length,0);
});

test('rejected invitations affect the initiator, not the person who declined', () => {
  const sim=new Simulation({population:2});const [initiator,target]=sim.world.agents;
  const event={id:'rejection-1',kind:'rejection',actorId:initiator.id,targetId:target.id,text:'دعوت پذیرفته نشد.'};
  assert.equal(perceive(sim.world,target,event),null);
  const before=initiator.emotions.anxiety;
  perceive(sim.world,initiator,event);
  assert.ok(initiator.emotions.anxiety>before);
});

test('large societies keep bounded states and memory, with saveable snapshots', () => {
  const sim=new Simulation({seed:'large-world',population:240});sim.step(72);
  assert.equal(new Set(sim.world.agents.map(a=>a.identity.name)).size,240);
  for(const agent of sim.world.agents){
    assert.ok(agent.memories.length<=82);
    assert.equal(agent.memories[0].source,'background');
    for(const field of ['traits','values','beliefs','needs','emotions'])for(const value of Object.values(agent[field]))assert.ok(Number.isFinite(value)&&value>=0&&value<=1);
  }
  assert.ok(sim.world.events.length<=400);
  assert.ok(sim.world.history.length<=240);
  assert.equal(Simulation.fromSnapshot(sim.snapshot()).world.agents.length,240);
});

test('events from after-phase extensions survive until the next observation phase', () => {
  const lateEvent={id:'late-event',phase:'after',order:20,update({world,emit}){
    if(world.tick===1)emit({kind:'achievement',actorId:'person-1',targetId:null,visibility:'public',text:'یک رویداد دیرهنگام از افزونه'});
  }};
  const sim=new Simulation({population:3,systems:[lateEvent]});sim.step();
  const event=sim.world.pendingEvents.find(e=>e.text.includes('دیرهنگام'));
  assert.ok(event);assert.equal(event.observers.length,0);
  const restored=Simulation.fromSnapshot(sim.snapshot(),{systems:[lateEvent]});restored.step();
  const delivered=restored.world.events.find(e=>e.id===event.id);
  assert.ok(delivered.observers.length>0);
  assert.equal(restored.world.pendingEvents.length,0);
});

test('modular systems have ordered lifecycle hooks and serialized extension data', () => {
  const trace=[];
  const system={id:'example-counter',phase:'after',order:20,update({world,emit}){trace.push(world.history.at(-1).tick);world.extensions.counter=(world.extensions.counter??0)+1;}};
  const sim=new Simulation({population:2,systems:[system]});sim.step(3);
  assert.deepEqual(trace,[1,2,3]);assert.equal(sim.world.extensions.counter,3);
  assert.throws(()=>Simulation.fromSnapshot(sim.snapshot()),/different set/);
  const restored=Simulation.fromSnapshot(sim.snapshot(),{systems:[system]});restored.step();assert.equal(restored.world.extensions.counter,4);
  assert.throws(()=>sim.registerSystem(system),/Duplicate/);
});

test('malformed snapshots and invalid controls cannot replace a valid world', () => {
  const sim=new Simulation({population:2});
  for(const input of ['{}','null','not json'])assert.throws(()=>Simulation.fromSnapshot(input));
  const bad=JSON.parse(sim.snapshot());bad.world.agents[0].needs.energy=-1;
  assert.throws(()=>Simulation.fromSnapshot(JSON.stringify(bad)),/needs/);
  const missing=JSON.parse(sim.snapshot());delete missing.world.agents[0].traits.empathy;
  assert.throws(()=>Simulation.fromSnapshot(JSON.stringify(missing)),/traits/);
  assert.throws(()=>sim.setCondition('__proto__',.5));
  assert.throws(()=>sim.setCondition('pressure',NaN));
  assert.throws(()=>sim.step(-1));
  assert.throws(()=>new Simulation({population:100000}));
});
