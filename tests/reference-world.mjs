// Migration oracle: the original engine runs the same operations as Python.
// This is a test helper, never a desktop runtime dependency.
import { readFileSync } from 'node:fs';
import { Simulation } from '../src/core/simulation.js';
const request=JSON.parse(readFileSync(0,'utf8'));
const simulation=request.snapshot?Simulation.fromSnapshot(request.snapshot):new Simulation(request.options);
for(const operation of request.operations??[]){
  if(operation.method==='step')simulation.step(operation.count);
  else if(operation.method==='condition')simulation.setCondition(operation.key,operation.value);
  else if(operation.method==='achievement')simulation.announceAchievement(operation.id);
  else throw new Error('Unknown reference operation');
}
process.stdout.write(simulation.snapshot());
