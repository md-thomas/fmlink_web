<script>
  import { station } from './lib/station.svelte.js';
  import Chat from './lib/Chat.svelte';
  import Link from './lib/Link.svelte';
  import Log from './lib/Log.svelte';

  let tab = $state('chat');   // narrow screens show one panel at a time
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

<nav>
  {#each [['chat', 'Chat'], ['link', 'Link'], ['log', 'Log']] as [key, label]}
    <button class:active={tab === key} onclick={() => (tab = key)}>{label}</button>
  {/each}
</nav>

<main>
  <section class="chat" class:shown={tab === 'chat'}><Chat /></section>
  <section class="link" class:shown={tab === 'link'}><Link /></section>
  <section class="log" class:shown={tab === 'log'}><Log /></section>
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
  nav { display: flex; gap: 6px; padding: 8px 16px 0; }
  nav button.active { border-color: var(--accent); color: var(--accent); font-weight: 600; }
  main { padding: 10px 16px 16px; display: grid; gap: 12px; }
  section { display: none; min-width: 0; }
  section.shown { display: block; }
  /* Wide screens: chat and link side by side; the log below them. */
  @media (min-width: 900px) {
    nav { display: none; }
    main { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }
    section.chat, section.link { display: block; }
    section.log { display: block; grid-column: 1 / -1; }
  }
</style>
