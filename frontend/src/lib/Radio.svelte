<script>
  // The radio: which interface, the live receive level with its last 30 s,
  // and transmit tests - a silent carrier (does PTT key the radio?) and a
  // steady tone at the TX level (for the other station's level meter).
  import { station, radioTest } from './station.svelte.js';
  import Panel from './Panel.svelte';
  import LevelMeter from './LevelMeter.svelte';
  import LevelHistory from './LevelHistory.svelte';

  const r = $derived(station.link ? station.link.radio : null);
  let seconds = $state(1);
  let confirm = $state(null);    // 'carrier' | 'tone' while asking
  let result = $state(null);
  const NAMES = { carrier: 'PTT test (silent carrier)', tone: 'test tone (1 kHz)' };

  async function run(kind) {
    confirm = null;
    result = null;
    try {
      await radioTest(kind, seconds);
      result = { ok: true, text: `✓ ${NAMES[kind]} queued for ${seconds} s - watch the TX indicator` };
    } catch (err) {
      result = { ok: false, text: '✕ ' + err.message };
    }
  }
</script>

<Panel id="radio" title="Radio">
{#snippet children()}
  {#if !station.link}
    <p class="muted">Waiting for the station…</p>
  {:else if !r}
    <p class="muted">Not on a radio - this station is using the simulator.</p>
  {:else}
    <dl>
      <dt>Interface</dt><dd>{r.name}{r.host && r.host !== 'localhost' ? ` on ${r.host}` : ''}</dd>
      <dt>Audio in</dt><dd class="mono">{r.rx_device}</dd>
      <dt>Audio out</dt><dd class="mono">{r.tx_device}</dd>
      <dt>PTT</dt><dd class="mono">{r.ptt_line?.toUpperCase()} on {r.ptt_port}</dd>
      <dt>TX level</dt><dd class="num">{station.link.tx_level}</dd>
    </dl>

    <h3>Receive level</h3>
    <LevelMeter />
    <LevelHistory />

    <h3>Transmit tests</h3>
    <div class="tests">
      <label>for
        <select bind:value={seconds}>
          {#each [1, 2, 3, 5] as s}<option value={s}>{s} s</option>{/each}
        </select>
      </label>
      <button onclick={() => (confirm = 'carrier')} disabled={!station.online || station.transmitting}>PTT test</button>
      <button onclick={() => (confirm = 'tone')} disabled={!station.online || station.transmitting}>Test tone</button>
    </div>
    {#if confirm}
      <div class="confirm" role="alertdialog" aria-label="Confirm transmission">
        <span>Transmit a {NAMES[confirm]} for {seconds} s{confirm === 'tone' ? ` at TX level ${station.link.tx_level}` : ''}?</span>
        <button class="primary" onclick={() => run(confirm)}>Transmit</button>
        <button onclick={() => (confirm = null)}>Cancel</button>
      </div>
    {/if}
    {#if result}<p class={result.ok ? 'good' : 'bad'}>{result.text}</p>{/if}
  {/if}
{/snippet}
</Panel>

<style>
  dl { display: grid; grid-template-columns: max-content 1fr; gap: 3px 12px; margin: 0 0 4px; font-size: 0.9rem; }
  dt { color: var(--muted); }
  dd { margin: 0; overflow-wrap: anywhere; }
  .mono { font-family: ui-monospace, monospace; font-size: 0.8rem; }
  h3 { font-size: 0.85rem; color: var(--ink-2); margin: 12px 0 6px; font-weight: 600; }
  .tests { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .tests label { display: flex; gap: 6px; align-items: center; color: var(--ink-2); font-size: 0.9rem; }
  .confirm { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 8px; padding: 8px;
             border: 1px solid var(--critical); border-radius: 6px; }
  .good { color: var(--good-text); font-size: 0.9rem; margin: 6px 0 0; }
  .bad { color: var(--critical); font-size: 0.9rem; margin: 6px 0 0; }
</style>
