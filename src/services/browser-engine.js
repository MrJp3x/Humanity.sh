// Compatibility adapter for the existing standalone web demo.
// The PySide application never constructs or advances this engine.
import { Simulation } from '../core/simulation.js';

const SAVE_KEY = 'humanity.sh/world/v1';
export class BrowserEngine {
  constructor() {
    this.mode = 'browser';
    this.simulation = new Simulation();
    this.simulation.step(6);
    this.listeners = new Set();
    this.running = false;
    this.speed = 1;
    this.generation = 0;
    this.selectedId = this.simulation.world.agents[0].id;
    this.experimentId = null;
    this.refresh();
    document.addEventListener('visibilitychange', () => { if (document.hidden && this.running) this.command('run', {value:false}); });
  }
  refresh() {
    this.state = {world:this.simulation.world,running:this.running,speed:this.speed,generation:this.generation,selectedId:this.selectedId,experimentId:this.experimentId,backend:'browser'};
    for (const callback of this.listeners) callback(this.state);
  }
  subscribe(callback) { this.listeners.add(callback); return () => this.listeners.delete(callback); }
  schedule() {
    clearInterval(this.timer);
    if (this.running) this.timer = setInterval(() => {
      try { this.simulation.step(); this.refresh(); }
      catch(error) { this.running=false;clearInterval(this.timer);console.error(error);this.refresh(); }
    }, 1200 / this.speed);
  }
  replace(simulation) {
    this.running=false;this.schedule();this.simulation=simulation;this.generation++;
    this.selectedId=simulation.world.agents[0].id;this.experimentId=null;
  }
  async command(method, args = {}) {
    let message = null;
    switch(method) {
      case 'state': break;
      case 'step': if(this.running)throw new Error('ابتدا زمان را متوقف کن.');this.simulation.step();break;
      case 'run': this.running=Boolean(args.value);this.schedule();break;
      case 'speed': this.speed=args.value;this.schedule();break;
      case 'new_world': { const next=new Simulation(args);next.step(6);this.replace(next);break; }
      case 'inspect': this.selectedId=args.id;break;
      case 'condition': this.simulation.setCondition(args.key,args.value);break;
      case 'achievement': this.experimentId=this.simulation.announceAchievement(args.id).id;this.running=false;this.schedule();break;
      case 'snapshot': return {snapshot:this.simulation.snapshot()};
      case 'import': this.replace(Simulation.fromSnapshot(args.text));break;
      case 'save': localStorage.setItem(SAVE_KEY,this.simulation.snapshot());message='جهان در این مرورگر ذخیره شد.';break;
      case 'load': { const saved=localStorage.getItem(SAVE_KEY);if(!saved)throw new Error('هنوز ذخیره‌ای در این مرورگر وجود ندارد.');this.replace(Simulation.fromSnapshot(saved));message='جهان به آخرین ذخیره بازگشت.';break; }
      default: throw new Error('Unknown browser command');
    }
    this.refresh();return {state:this.state,message};
  }
}
