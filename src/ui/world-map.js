import { locations } from '../domain/catalog.js';
import { mood, percent } from './format.js';

export class WorldMap {
  constructor(canvas, { getWorld, getSelected, onSelect, tooltip }) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.getWorld = getWorld;
    this.getSelected = getSelected;
    this.onSelect = onSelect;
    this.tooltip = tooltip;
    this.mode = 'mood';
    this.showLinks = true;
    this.points = new Map();
    this.hovered = null;
    this.reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(canvas);
    canvas.addEventListener('pointermove', event => this.pointer(event));
    canvas.addEventListener('pointerleave', () => { this.hovered = null; tooltip.classList.remove('visible'); });
    canvas.addEventListener('click', event => { const id = this.hit(event); if (id) this.onSelect(id); });
    this.resize();
    const frame = () => {
      if (!document.hidden && this.canvas.clientWidth > 0) this.draw();
      this.frameId = requestAnimationFrame(frame);
    };
    this.frameId = requestAnimationFrame(frame);
  }
  resize() {
    const box = this.canvas.getBoundingClientRect();
    this.width = box.width;
    this.height = box.height;
    const dpr = Math.min(devicePixelRatio || 1, 2);
    this.canvas.width = Math.round(box.width * dpr);
    this.canvas.height = Math.round(box.height * dpr);
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  reset() { this.points.clear(); }
  hit(event) {
    const rect = this.canvas.getBoundingClientRect();
    const x = event.clientX - rect.left, y = event.clientY - rect.top;
    let closest = null, distance = 18;
    for (const [id, point] of this.points) {
      const d = Math.hypot(x-point.x, y-point.y);
      if (d < distance) { distance = d; closest = id; }
    }
    return closest;
  }
  pointer(event) {
    this.hovered = this.hit(event);
    const agent = this.getWorld().agents.find(a => a.id === this.hovered);
    if (!agent) { this.tooltip.classList.remove('visible'); this.canvas.style.cursor = 'crosshair'; return; }
    this.canvas.style.cursor = 'pointer';
    this.tooltip.textContent = `${agent.identity.name} · ${mood(agent).label}`;
    const point = this.points.get(agent.id);
    this.tooltip.style.left = `${Math.min(Math.max(8, point.x - 70), Math.max(8, this.width - 190))}px`;
    this.tooltip.style.top = `${Math.max(8, point.y - 42)}px`;
    this.tooltip.classList.add('visible');
  }
  color(agent) {
    if (this.mode === 'trust') return agent.beliefs.trust > .6 ? '#c9ed8c' : agent.beliefs.trust > .4 ? '#83bbbd' : '#eaa36d';
    if (this.mode === 'gap') return agent.publicState.warmth - agent.emotions.joy + agent.emotions.envy * .65 > .5 ? '#b89af4' : '#83bbbd';
    return mood(agent).color;
  }
  draw() {
    const c = this.ctx, w = this.width, h = this.height;
    if (!w || !h) return;
    const world = this.getWorld(), selected = this.getSelected();
    c.clearRect(0,0,w,h);
    c.fillStyle = '#11191f'; c.fillRect(0,0,w,h);
    c.fillStyle = '#2c3b452e';
    for (let x=14;x<w;x+=22) for(let y=14;y<h;y+=22) { c.beginPath();c.arc(x,y,.7,0,Math.PI*2);c.fill(); }
    // Quiet landscape contours and paths give the 2D world a sense of place.
    c.strokeStyle = '#26394355'; c.lineWidth=1;
    for(let i=0;i<6;i++) {
      c.beginPath(); c.ellipse(w*.53,h*.48,w*(.17+i*.055),h*(.14+i*.05),-.3,0,Math.PI*2);c.stroke();
    }
    c.setLineDash([4,7]);c.strokeStyle='#44606b44';c.lineWidth=1.2;
    c.beginPath();c.moveTo(w*.2,h*.28);c.bezierCurveTo(w*.45,h*.28,w*.43,h*.65,w*.79,h*.73);c.stroke();
    c.beginPath();c.moveTo(w*.72,h*.25);c.bezierCurveTo(w*.66,h*.45,w*.50,h*.6,w*.40,h*.72);c.stroke();c.setLineDash([]);
    for(const [i,loc] of locations.entries()) {
      const x=loc.x*w,y=loc.y*h,sw=loc.width*w,sh=loc.height*h;
      c.fillStyle=['#83bbbd05','#c9ed8c04','#b89af405','#eaa36d04'][i];
      c.strokeStyle=['#83bbbd18','#c9ed8c14','#b89af418','#eaa36d14'][i];
      c.beginPath();c.roundRect(x-sw/2,y-sh/2,sw,sh,18);c.fill();c.stroke();
      c.font='10px Vazirmatn, Tahoma, sans-serif';c.textAlign='center';c.fillStyle='#6b8794';c.fillText(loc.name,x,y-sh/2-10);
      c.fillStyle='#344c5838';
      for(let j=0;j<5;j++){const xx=x+Math.sin(j*8+i)*sw*.3,yy=y+Math.cos(j*9+i)*sh*.3;c.beginPath();c.arc(xx,yy,3+(j%3),0,Math.PI*2);c.fill();}
    }
    const liveIds = new Set(world.agents.map(a=>a.id));
    for(const id of this.points.keys()) if(!liveIds.has(id)) this.points.delete(id);
    for(const a of world.agents) {
      const target={x:a.position.x*w,y:a.position.y*h};
      const p=this.points.get(a.id)??target;
      const ease=this.reducedMotion?1:.07;
      p.x+=(target.x-p.x)*ease;p.y+=(target.y-p.y)*ease;
      this.points.set(a.id,p);
    }
    if(this.showLinks) {
      const drawn=new Set();let count=0;
      for(const a of world.agents) for(const [id,r] of Object.entries(a.relationships)) {
        const key=[a.id,id].sort().join(':');
        const focused=a.id===selected||id===selected;
        if(drawn.has(key)||(!focused&&(r.familiarity<.4||r.trust<.6||count>70)))continue;
        const p=this.points.get(a.id),q=this.points.get(id);if(!p||!q)continue;
        drawn.add(key);count++;
        c.strokeStyle=focused?(r.trust>.45?'#a6ce8560':'#d89b6750'):'#6b9b9820';c.lineWidth=focused?1: .6;
        c.beginPath();c.moveTo(p.x,p.y);c.quadraticCurveTo((p.x+q.x)/2,(p.y+q.y)/2-12,q.x,q.y);c.stroke();
      }
    }
    for(const a of world.agents) {
      const p=this.points.get(a.id),color=this.color(a),isSelected=a.id===selected;
      const r=world.agents.length>120?3.3:world.agents.length>60?4:4.8;
      if(isSelected||a.id===this.hovered){c.fillStyle=color+'12';c.beginPath();c.arc(p.x,p.y,r+10,0,Math.PI*2);c.fill();c.strokeStyle=color+'99';c.lineWidth=1;c.beginPath();c.arc(p.x,p.y,r+5,0,Math.PI*2);c.stroke();}
      c.fillStyle='#0d161c';c.beginPath();c.arc(p.x,p.y,r+1.8,0,Math.PI*2);c.fill();
      c.fillStyle=color;c.beginPath();c.arc(p.x,p.y,r,0,Math.PI*2);c.fill();
      if(isSelected){c.fillStyle='#d2dfe3';c.font='10px Vazirmatn,Tahoma,sans-serif';c.textAlign='center';c.fillText(a.identity.name,p.x,p.y+23);}
    }
  }
  destroy() { cancelAnimationFrame(this.frameId); this.resizeObserver.disconnect(); }
}
