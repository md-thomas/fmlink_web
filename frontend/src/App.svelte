<script>
  import { station } from './lib/station.svelte.js';
  import Chat from './lib/Chat.svelte';
  import Link from './lib/Link.svelte';
  import Log from './lib/Log.svelte';
  import Callsigns from './lib/Callsigns.svelte';
  import Settings from './lib/Settings.svelte';
  import Radio from './lib/Radio.svelte';
  import { load, save } from './lib/storage.js';

  let tab = $state('chat');   // narrow screens show one panel at a time

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
    document.title = l ? `${l.station_id} - OpenWave` : 'OpenWave station';
  });
</script>

<header>
  <div class="who">
    <strong>{l ? l.station_id : 'OpenWave'}</strong>
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
  </span>
</header>

<div class="top"><Callsigns /></div>

<nav>
  {#each [['chat', 'Chat'], ['link', 'Link'], ['radio', 'Radio'], ['settings', 'Settings'], ['log', 'Log']] as [key, label]}
    <button class:active={tab === key} onclick={() => (tab = key)}>{label}</button>
  {/each}
</nav>

<main bind:this={mainEl} style:--left="{split}fr" style:--right="{1 - split}fr">
  <div class="col left">
    <section class:shown={tab === 'chat'}><Chat /></section>
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
  .top { padding: 10px 16px 0; }
  nav { display: flex; gap: 6px; padding: 8px 16px 0; }
  nav button.active { border-color: var(--accent); color: var(--accent); font-weight: 600; }
  main { padding: 10px 16px 16px; display: grid; gap: 12px; }
  section { display: none; min-width: 0; }
  .col { display: contents; }   /* phones: one tab's section at a time */
  .divider { display: none; }
  section.shown { display: block; }
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
    .divider {
      display: block; align-self: stretch;
      cursor: col-resize; border-radius: 4px; touch-action: none;
    }
    .divider:hover, .divider:focus-visible { background: var(--grid); outline: none; }
  }
</style>
