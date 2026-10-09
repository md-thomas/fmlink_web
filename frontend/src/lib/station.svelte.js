// The station as the page sees it: one reactive object, fed by the backend's
// event WebSocket (a snapshot first, then live events), plus the actions the
// page can take. Components read `station` and call send/command/settings.

const MAX_BURSTS = 300;
const MAX_LOGS = 500;

export const station = $state({
  online: false,          // the page's connection to the station's server
  link: null,             // the latest 'link' event (mode, FEC, batching, ...)
  messages: [],           // {kind: 'tx'|'rx', id, text, src, dst, time, segments, acked, done, failed, ack}
  bursts: [],             // 'burst_rx' events, oldest first
  logs: [],               // log lines, oldest first
  level: null,            // the latest 'level' event (receive rms/peak dBFS)
  transmitting: false,    // the radio is keyed
  receiving: false,       // a burst was decoded in the last couple of seconds
  constellation: null,    // the latest received burst's symbol points
  error: null,            // the last action's error, for the page to show
});

let receivingTimer = null;

function messageFromTx(e) {
  return { kind: 'tx', id: e.id, text: e.text, dst: e.dst, time: e.time, segments: e.segments,
           ack: e.ack, acked: 0, done: false, failed: false };
}

function applyDelivery(e) {
  const m = station.messages.find((x) => x.kind === 'tx' && x.id === e.id);
  if (!m) return;
  m.acked = e.acked;
  m.done = e.done;
  m.failed = e.failed;
}

function handle(e) {
  switch (e.type) {
    case 'snapshot':
      station.link = e.link;
      station.level = e.level;
      station.messages = [];
      for (const m of e.messages) handle(m);
      station.bursts = e.bursts.slice(-MAX_BURSTS);
      station.logs = e.logs.map((l) => l.text).slice(-MAX_LOGS);
      break;
    case 'link':
      station.link = e;
      break;
    case 'message_tx':
      station.messages.push(messageFromTx(e));
      break;
    case 'delivery':
      applyDelivery(e);
      break;
    case 'message_rx':
      station.messages.push({ kind: 'rx', text: e.text, src: e.src, time: e.time });
      break;
    case 'burst_rx':
      station.bursts.push(e);
      if (station.bursts.length > MAX_BURSTS) station.bursts.shift();
      station.receiving = true;
      clearTimeout(receivingTimer);
      receivingTimer = setTimeout(() => (station.receiving = false), 2000);
      break;
    case 'constellation':
      station.constellation = e;
      break;
    case 'level':
      station.level = e;
      break;
    case 'tx':
      if (e.state === 'keyed') station.transmitting = true;
      if (e.state === 'released') station.transmitting = false;
      break;
    case 'log':
      station.logs.push(e.text);
      if (station.logs.length > MAX_LOGS) station.logs.shift();
      break;
  }
}

export function connect() {
  const scheme = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${scheme}://${location.host}/api/events`);
  ws.onopen = () => (station.online = true);
  ws.onmessage = (m) => handle(JSON.parse(m.data));
  ws.onclose = () => {
    station.online = false;
    station.transmitting = false;
    setTimeout(connect, 2000);
  };
}

async function call(method, path, body) {
  station.error = null;
  const r = await fetch(path, {
    method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    station.error = data.detail || `${r.status} ${r.statusText}`;
    throw new Error(station.error);
  }
  return data;
}

/** A chat line, or a /command when it starts with '/'. */
export function send(text) {
  return text.startsWith('/') ? call('POST', '/api/command', { line: text })
                              : call('POST', '/api/send', { text });
}

/** Change settings while running, e.g. {mode_id: 3}. */
export function updateSettings(changes) {
  return call('PATCH', '/api/settings', changes);
}

// Where each mode stops decoding reliably (dB SNR, measured - RADIO_SETUP.md).
export const MODE_LIMIT_DB = { 0: -1, 1: 4.5, 2: 7, 3: 8 };
