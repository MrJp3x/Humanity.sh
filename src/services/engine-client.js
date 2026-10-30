// The desktop has exactly one owner of the world: the Python worker.
// This client only sends commands and receives immutable JSON projections.
export async function connectEngine() {
  if (window.qt?.webChannelTransport) {
    if (typeof window.QWebChannel !== 'function') throw new Error('Qt WebChannel was not initialized.');
    const channel = await new Promise(resolve => new window.QWebChannel(window.qt.webChannelTransport, resolve));
    const client = new DesktopEngine(channel.objects.engine);
    await client.command('state');
    return client;
  }
  if (new URL(location.href).searchParams.has('desktop')) {
    throw new Error('The desktop Python bridge is unavailable.');
  }
  // The original public browser demo remains available as a separate adapter.
  const { BrowserEngine } = await import('./browser-engine.js');
  return new BrowserEngine();
}

class DesktopEngine {
  constructor(bridge) {
    this.bridge = bridge;
    this.mode = 'desktop';
    this.pending = new Map();
    this.sequence = 1;
    this.listeners = new Set();
    bridge.updated.connect(raw => this.accept(JSON.parse(raw)));
    bridge.failed.connect(message => { if (this.state) this.accept({...this.state,running:false,error:message}); });
    bridge.reply.connect(raw => {
      const packet = JSON.parse(raw);
      const waiting = this.pending.get(packet.id);
      if (!waiting) return;
      this.pending.delete(packet.id);
      clearTimeout(waiting.timer);
      if (!packet.ok) { waiting.reject(new Error(packet.error)); return; }
      if (packet.result.state) this.accept(packet.result.state);
      waiting.resolve(packet.result);
    });
  }
  accept(state) {
    this.state = state;
    for (const callback of this.listeners) callback(state);
  }
  subscribe(callback) { this.listeners.add(callback); return () => this.listeners.delete(callback); }
  command(method, args = {}) {
    const id = String(this.sequence++);
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { this.pending.delete(id); reject(new Error('پاسخ موتور دریافت نشد؛ وضعیت اتصال را بررسی کن.')); }, 45000);
      this.pending.set(id, { resolve, reject, timer });
      this.bridge.request(JSON.stringify({ id, method, args }));
    });
  }
}
