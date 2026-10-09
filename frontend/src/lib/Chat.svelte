<script>
  import { station, send } from './station.svelte.js';

  let text = $state('');
  let busy = $state(false);
  let list;

  function status(m) {
    if (m.failed) return { text: '✕ not delivered', cls: 'bad' };
    if (m.done) return m.ack === false || m.acked === null
      ? { text: 'sent (no ACK requested)', cls: '' } : { text: '✓ delivered', cls: 'good' };
    if (m.segments > 1) return { text: `sending · ${m.acked}/${m.segments} segments acknowledged`, cls: '' };
    return { text: 'sending…', cls: '' };
  }
  const time = (t) => new Date(t * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  async function submit(event) {
    event.preventDefault();
    const line = text.trim();
    if (!line || busy) return;
    busy = true;
    try {
      await send(line);
      text = '';
    } catch {
      /* station.error shows it */
    } finally {
      busy = false;
    }
  }

  $effect(() => {
    station.messages.length;   // scroll to the newest when one arrives
    if (list) queueMicrotask(() => (list.scrollTop = list.scrollHeight));
  });
</script>

<div class="card chat">
  <h2>Chat{station.link ? ` with ${station.link.dst_id}` : ''}</h2>
  <div class="list" bind:this={list}>
    {#each station.messages as m}
      <div class="msg" class:me={m.kind === 'tx'}>
        <div class="bubble">{m.text}</div>
        <div class="meta muted">
          {time(m.time)}
          {#if m.kind === 'tx'}
            {@const s = status(m)}
            · <span class={s.cls}>{s.text}</span>
          {:else}
            · {m.src}
          {/if}
        </div>
      </div>
    {:else}
      <p class="muted">No messages yet. Type one below, or a /command such as /ping or /help.</p>
    {/each}
  </div>
  {#if station.error}<p class="error">✕ {station.error}</p>{/if}
  <form onsubmit={submit}>
    <input bind:value={text} placeholder="Message, or /command" autocomplete="off"
           disabled={!station.online} />
    <button class="primary" disabled={!station.online || busy || !text.trim()}>Send</button>
  </form>
</div>

<style>
  .chat { display: flex; flex-direction: column; height: min(70vh, 640px); }
  .list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; padding: 4px 2px; }
  .msg { max-width: 85%; }
  .msg.me { align-self: flex-end; text-align: right; }
  .bubble {
    display: inline-block; text-align: left; padding: 6px 10px; border-radius: 10px;
    border: 1px solid var(--ring); white-space: pre-wrap; overflow-wrap: anywhere;
  }
  .me .bubble { background: var(--me); }
  .meta { font-size: 0.8rem; margin-top: 2px; }
  .good { color: var(--good-text); }
  .bad, .error { color: var(--critical); }
  .error { margin: 6px 0 0; font-size: 0.9rem; }
  form { display: flex; gap: 8px; margin-top: 8px; }
  input { flex: 1; min-width: 0; }
</style>
