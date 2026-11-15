<script>
  import { station, abortTx, updateSettings } from './lib/station.svelte.js';
  import Chat from './lib/Chat.svelte';
  import Link from './lib/Link.svelte';
  import Log from './lib/Log.svelte';
  import Settings from './lib/Settings.svelte';
  import Radio from './lib/Radio.svelte';
  import { load, save } from './lib/storage.js';

  let tab = $state('chat');   // narrow screens show one panel at a time

  // My callsign (global - the station's own identity). The destination
  // callsign used to live here too, but now each Chat panel below has its
  // own, so there can be several conversations open with different peers.
  let mine = $state('');
  let mineEdited = $state(false);
  let mineResult = $state(null);
  $effect(() => {
    if (station.link && !mineEdited) mine = station.link.station_id;
  });
  async function applyMine(event) {
    event.preventDefault();
    mineResult = null;
    try {
      const s = await updateSettings({ station_id: mine });
      mine = s.station_id;
      mineEdited = false;
      mineResult = { ok: true, text: '✓ saved' };
    } catch (err) {
      mineResult = { ok: false, text: '✕ ' + err.message };
    }
  }

  // Open conversations, one Chat panel per destination callsign - seeded
  // once from the station's current one, on a browser that's never saved
  // a list at all (never forced back open once the user's emptied it).
  const savedConversations = load('conversations', null);
  let conversations = $state(savedConversations ?? []);
  let seededConversations = savedConversations !== null;
  $effect(() => {
    if (!seededConversations && station.link) {
      conversations.push(station.link.dst_id);
      seededConversations = true;
    }
  });
  $effect(() => {
    save('conversations', [...conversations]);
  });
  let newDst = $state('');
  function addConversation(event) {
    event.preventDefault();
    const dst = newDst.trim().toUpperCase();
    if (dst && !conversations.includes(dst)) conversations.push(dst);
    newDst = '';
  }
  function removeConversation(i) {
    conversations.splice(i, 1);
  }

  // Theme: 'system' follows the OS/browser (the default), or an explicit
  // override - cycles system -> light -> dark -> system.
  let theme = $state(load('theme', 'system'));
  const THEME_LABEL = { system: 'Theme: Auto', light: 'Theme: Light', dark: 'Theme: Dark' };
  const THEME_NEXT = { system: 'light', light: 'dark', dark: 'system' };
  $effect(() => {
    if (theme === 'system') document.documentElement.removeAttribute('data-theme');
    else document.documentElement.dataset.theme = theme;
  });
  function cycleTheme() {
    theme = THEME_NEXT[theme];
    save('theme', theme === 'system' ? null : theme);
  }

  // Wide screens: the share of the width the left column (chat, log) gets;
  // drag the divider to change it, double-click to reset.
  let split = $state(load('split', 0.5));
  let mainEl;
  const clamp = (f) => Math.min(0.75, Math.max(0.25, f));
  function drag(event) {
    event.preventDefault();
    const rect = mainEl.getBoundingClientRect();
    const move = (e) => (split = clamp((e.clientX - rect.left) / rect.width));
    const up = () => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
      save('split', split);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  }
  function key(event) {
    const step = { ArrowLeft: -0.02, ArrowRight: 0.02 }[event.key];
    if (step) {
      split = clamp(split + step);
      save('split', split);
    }
  }
  function resetSplit() {
    split = 0.5;
    save('split', null);
  }
  const l = $derived(station.link);
  $effect(() => {
    document.title = l ? `${l.station_id} - FMlink` : 'FMlink station';
  });
</script>

<header>
  <div class="who">
    <strong>{l ? l.station_id : 'FMlink'}</strong>
    {#if l}<span class="secondary">→ {l.dst_id}</span>{/if}
  </div>
  {#if l}
    <span class="chip num">mode {l.mode_id} · {l.modulation} {l.symbol_rate} · {l.fec_preset}{l.batch_active ? ' · batching' : ''}</span>
  {/if}
  <span class="state">
    {#if !station.online}
      <span class="badge off">✕ page offline - reconnecting</span>
    {:else if station.transmitting}
      <span class="badge tx">● TX</span>
    {:else if station.receiving}
      <span class="badge rx">● RX</span>
    {:else if l && !l.connected}
      <span class="badge off">✕ station not connected</span>
    {:else}
      <span class="badge idle">○ idle</span>
    {/if}
    <button class="abort" onclick={abortTx} disabled={!station.online}
            title="Stop the current (or about-to-start) transmission right away">Abort</button>
  </span>
  <button class="theme" onclick={cycleTheme} title="Cycle light/dark/auto">{THEME_LABEL[theme]}</button>
</header>

<div class="top">
  <form class="mine" onsubmit={applyMine} oninput={() => (mineEdited = true)}>
    <label>My callsign
      <input bind:value={mine} autocomplete="off" spellcheck="false" maxlength="9"
             placeholder="e.g. K0MDT-1" disabled={!station.online} />
    </label>
    <button class="primary" disabled={!station.online || !mineEdited}>Apply</button>
    {#if mineResult}<span class={mineResult.ok ? 'good' : 'bad'}>{mineResult.text}</span>{/if}
  </form>
  <form class="add" onsubmit={addConversation}>
    <label>Start a chat with
      <input bind:value={newDst} autocomplete="off" spellcheck="false" maxlength="9"
             placeholder="e.g. K0MDT-2" disabled={!station.online} />
    </label>
    <button class="primary" disabled={!station.online || !newDst.trim()}>+ Add</button>
  </form>
</div>

<nav>
  {#each [['chat', 'Chat'], ['link', 'Link'], ['radio', 'Radio'], ['settings', 'Settings'], ['log', 'Log']] as [key, label]}
    <button class:active={tab === key} onclick={() => (tab = key)}>{label}</button>
  {/each}
</nav>

<main bind:this={mainEl} style:--left="{split}fr" style:--right="{1 - split}fr">
  <div class="col left">
    <section class="chat-list" class:shown={tab === 'chat'}>
      {#each conversations as _, i}
        <Chat bind:dst={conversations[i]} onClose={() => removeConversation(i)} />
      {/each}
      {#if !conversations.length}
        <p class="muted">No chats open - add a destination callsign above to start one.</p>
      {/if}
    </section>
    <section class:shown={tab === 'log'}><Log /></section>
  </div>
  <div class="divider" role="separator" aria-orientation="vertical" tabindex="0"
       aria-valuenow={Math.round(split * 100)} aria-valuemin="25" aria-valuemax="75"
       aria-label="Column width" title="Drag to resize the columns; double-click to reset"
       onpointerdown={drag} ondblclick={resetSplit} onkeydown={key}></div>
  <div class="col right">
    <section class:shown={tab === 'settings'}><Settings /></section>
    <section class:shown={tab === 'radio'}><Radio /></section>
    <section class:shown={tab === 'link'}><Link /></section>
  </div>
</main>

<style>
  header {
    display: flex; flex-wrap: wrap; align-items: center; gap: 6px 14px;
    padding: 10px 16px; border-bottom: 1px solid var(--ring); background: var(--surface);
  }
  .who { font-size: 1.1rem; }
  .chip { color: var(--ink-2); font-size: 0.9rem; }
  .state { margin-left: auto; }
  .badge { font-weight: 600; font-size: 0.9rem; }
  .tx { color: var(--critical); }
  .rx { color: var(--good-text); }
  .idle { color: var(--muted); }
  .off { color: var(--critical); }
  .abort { margin-left: 8px; font-size: 0.8rem; padding: 2px 10px; color: var(--critical); border-color: var(--critical); }
  .theme { font-size: 0.8rem; padding: 4px 10px; color: var(--ink-2); }
  .top { padding: 10px 16px 0; display: flex; flex-wrap: wrap; gap: 10px 24px; }
  .top form { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 8px 12px; }
  .top label { display: grid; gap: 4px; font-size: 0.85rem; color: var(--ink-2); min-width: 90px; }
  .top input { text-transform: uppercase; width: 140px; }
  .top .good { color: var(--good-text); }
  .top .bad { color: var(--critical); }
  nav { display: flex; gap: 6px; padding: 8px 16px 0; }
  nav button.active { border-color: var(--accent); color: var(--accent); font-weight: 600; }
  main { padding: 10px 16px 16px; display: grid; gap: 12px; }
  section { display: none; min-width: 0; }
  .col { display: contents; }   /* phones: one tab's section at a time */
  .divider { display: none; }
  section.shown { display: block; }
  section.chat-list.shown { display: flex; flex-direction: column; gap: 12px; }
  /* Wide screens: chat with the log under it on the left (the same size),
     the link panels on the right. */
  @media (min-width: 900px) {
    nav { display: none; }
    main {
      grid-template-columns: minmax(0, var(--left)) 10px minmax(0, var(--right));
      column-gap: 2px; align-items: start;
    }
    /* Each column stacks its own panels. */
    .col { display: grid; gap: 12px; align-content: start; min-width: 0; }
    .col section { display: block; }
    .col section.chat-list { display: flex; flex-direction: column; gap: 12px; }
    .divider {
      display: block; align-self: stretch;
      cursor: col-resize; border-radius: 4px; touch-action: none;
    }
    .divider:hover, .divider:focus-visible { background: var(--grid); outline: none; }
  }
</style>
