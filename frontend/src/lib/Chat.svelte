<script>
  // One conversation with one destination callsign. dst is bindable - its
  // owner (App.svelte) keeps a list of these, one per open chat, so there
  // can be several going with different peers. The radio itself can only
  // talk to one at a time though: sending from a panel whose dst isn't
  // the station's current one switches it first (PATCH /api/settings),
  // which costs a fresh mode negotiation, same as changing it used to in
  // the old standalone Callsigns panel.
  import { station, send, updateSettings, clearChat } from './station.svelte.js';
  import Panel from './Panel.svelte';

  let { dst = $bindable(), onClose } = $props();

  let text = $state('');
  let busy = $state(false);
  let list;

  let dstDraft = $state(dst);
  let editingDst = $state(false);

  const messages = $derived(
    station.messages.filter((m) => (m.kind === 'tx' ? m.dst : m.src) === dst));
  const isCurrent = $derived(station.link && station.link.dst_id === dst);
  const connected = $derived(station.link && station.link.connected);

  function status(m) {
    if (m.failed) return { text: '✕ not delivered', cls: 'bad' };
    if (m.done) return m.ack === false || m.acked === null
      ? { text: 'sent (no ACK requested)', cls: '' } : { text: '✓ delivered', cls: 'good' };
    if (m.segments > 1) return { text: `sending · ${m.acked}/${m.segments} segments acknowledged`, cls: '' };
    return { text: 'sending…', cls: '' };
  }
  const time = (t) => new Date(t * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  function toggleEditDst() {
    dstDraft = dst;
    editingDst = !editingDst;
  }

  function applyDst(event) {
    event.preventDefault();
    const next = dstDraft.trim().toUpperCase();
    if (next) dst = next;
    editingDst = false;
  }

  async function submit(event) {
    event.preventDefault();
    const line = text.trim();
    if (!line || busy) return;
    busy = true;
    try {
      if (!isCurrent) await updateSettings({ dst_id: dst });
      await send(line);
      text = '';
    } catch {
      /* station.error shows it */
    } finally {
      busy = false;
    }
  }

  $effect(() => {
    messages.length;   // scroll to the newest when one arrives
    if (list) queueMicrotask(() => (list.scrollTop = list.scrollHeight));
  });
</script>

<Panel id={`chat-${dst}`} title={`Chat with ${dst}`} height="min(70vh, 640px)" fill>
{#snippet actions()}
  <button class="link" onclick={toggleEditDst}
          title="Change this chat's destination callsign">✎</button>
  <button class="link" onclick={() => clearChat(dst)}
          title="Drop this conversation's history (all pages, other chats kept)" disabled={!messages.length}>Clear</button>
  <button class="link" onclick={onClose} title="Close this chat">✕</button>
{/snippet}
{#snippet children()}
  {#if editingDst}
    <form class="dst" onsubmit={applyDst}>
      <input bind:value={dstDraft} autocomplete="off" spellcheck="false" maxlength="9" />
      <button class="primary">Apply</button>
      <button type="button" onclick={() => (editingDst = false)}>Cancel</button>
    </form>
  {/if}
  <div class="list" bind:this={list}>
    {#each messages as m}
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
      <p class="muted">No messages yet with {dst}. Type one below, or a /command such as /ping or /help.</p>
    {/each}
  </div>
  {#if station.error}<p class="error">✕ {station.error}</p>{/if}
  {#if station.link && !connected}
    <p class="muted note">✕ Not connected to a radio or simulator - see the Radio tab.
      Sending here won't go anywhere until that's fixed.</p>
  {:else if !isCurrent}
    <p class="muted note">Sending here switches the station to {dst} first - it takes a few
      seconds on air to renegotiate.</p>
  {/if}
  <form onsubmit={submit}>
    <input bind:value={text} placeholder="Message, or /command" autocomplete="off"
           disabled={!station.online} />
    <button class="primary" disabled={!station.online || !connected || busy || !text.trim()}>Send</button>
  </form>
{/snippet}
</Panel>

<style>
  .list { flex: 1; min-height: 0; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; padding: 4px 2px; }
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
  .note { font-size: 0.8rem; margin: 6px 0 0; }
  form { display: flex; gap: 8px; margin-top: 8px; }
  form.dst { margin: 0 0 8px; }
  input { flex: 1; min-width: 0; }
  form.dst input { text-transform: uppercase; flex: 0 1 140px; }
  .link { border: 0; background: none; padding: 2px 4px; color: var(--ink-2); }
  .link:hover { color: var(--ink); }
</style>
