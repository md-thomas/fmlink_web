<script>
  // My callsign and the destination's, changed while the station runs
  // (PATCH /api/settings). Changing either starts a fresh session - the
  // next message negotiates the mode with the (new) peer.
  import { station, updateSettings } from './station.svelte.js';
  import Panel from './Panel.svelte';

  let mine = $state('');
  let theirs = $state('');
  let edited = $state(false);
  let busy = $state(false);
  let result = $state(null);   // {ok, text}

  // Follow the station's values until the user starts typing.
  $effect(() => {
    const l = station.link;
    if (l && !edited) {
      mine = l.station_id;
      theirs = l.dst_id;
    }
  });

  const changed = $derived(station.link &&
    (mine.trim().toUpperCase() !== station.link.station_id ||
     theirs.trim().toUpperCase() !== station.link.dst_id));

  async function apply(event) {
    event.preventDefault();
    busy = true;
    result = null;
    try {
      const state = await updateSettings({ station_id: mine, dst_id: theirs });
      mine = state.station_id;
      theirs = state.dst_id;
      edited = false;
      result = { ok: true, text: '✓ saved - the next message negotiates with ' + state.dst_id };
    } catch (err) {
      result = { ok: false, text: '✕ ' + err.message };
    } finally {
      busy = false;
    }
  }

  function cancel() {
    edited = false;
    result = null;
    mine = station.link.station_id;
    theirs = station.link.dst_id;
  }
</script>

<Panel id="callsigns" title="Callsigns">
{#snippet children()}
  <form onsubmit={apply} oninput={() => (edited = true)}>
    <label>
      <span>My callsign</span>
      <input bind:value={mine} autocomplete="off" spellcheck="false" maxlength="9"
             placeholder="e.g. K0MDT-1" disabled={!station.online} />
    </label>
    <label>
      <span>Destination callsign</span>
      <input bind:value={theirs} autocomplete="off" spellcheck="false" maxlength="9"
             placeholder="e.g. K0MDT-2" disabled={!station.online} />
    </label>
    <button class="primary" disabled={!station.online || busy || !changed}>Apply</button>
    {#if edited}<button type="button" onclick={cancel}>Cancel</button>{/if}
  </form>
  {#if result}<p class={result.ok ? 'good' : 'bad'}>{result.text}</p>{/if}
{/snippet}
</Panel>

<style>
  /* Title on the first row; both entries and the buttons on the second. */
  form { padding: 2px; display: flex; flex-wrap: wrap; align-items: flex-end; gap: 8px 12px; }
  label { display: grid; gap: 4px; flex: 1 1 0; min-width: 90px; max-width: 220px; }
  label span { color: var(--ink-2); font-size: 0.85rem; }
  input { text-transform: uppercase; width: 100%; }
  .good { color: var(--good-text); }
  .bad { color: var(--critical); }
  p { margin: 8px 0 0; font-size: 0.9rem; }
</style>
