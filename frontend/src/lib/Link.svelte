<script>
  import { station } from './station.svelte.js';
  import SnrChart from './SnrChart.svelte';
  import LevelMeter from './LevelMeter.svelte';
  import Constellation from './Constellation.svelte';

  const l = $derived(station.link);
  const recent = $derived(station.bursts.slice(-8).reverse());
  const time = (t) => new Date(t * 1000).toLocaleTimeString();
  const db = (v) => (v === null || v === undefined ? '-' : `${v.toFixed(1)} dB`);
</script>

<div class="stack">
  <div class="card">
    <h2>Link</h2>
    {#if l}
      <dl>
        <dt>Peer</dt><dd>{l.dst_id}</dd>
        <dt>Mode</dt><dd class="num">{l.mode_id} - {l.modulation} {l.symbol_rate} sym/s</dd>
        <dt>FEC</dt><dd>{l.fec ? l.fec_preset : 'off'}</dd>
        <dt>Batching</dt><dd>{l.batch_active ? 'on' : l.batching ? 'offered (peer hasn’t)' : 'off'}</dd>
        <dt>ACK / auto</dt><dd>{l.ack ? 'on' : 'off'} / {l.auto ? 'on' : 'off'}</dd>
        <dt>Last SNR</dt><dd class="num">{db(l.last_rx_snr_db)}</dd>
      </dl>
    {:else}
      <p class="muted">Waiting for the station…</p>
    {/if}
  </div>

  <div class="card">
    <h2>SNR of received bursts</h2>
    <SnrChart />
  </div>

  <div class="card">
    <h2>Constellation (last burst)</h2>
    <Constellation />
  </div>

  <div class="card">
    <h2>Receive level</h2>
    <LevelMeter />
  </div>

  <div class="card">
    <h2>Recent bursts</h2>
    {#if recent.length}
      <table>
        <thead><tr><th>Time</th><th>Result</th><th>Mode</th><th class="r">SNR</th><th class="r">Sync</th></tr></thead>
        <tbody>
          {#each recent as b}
            <tr>
              <td class="num">{time(b.time)}</td>
              <td class={b.status === 'ok' ? 'good' : 'bad'}>{b.status === 'ok' ? '✓ ok' : `✕ ${b.status}`}</td>
              <td>{b.modulation} {b.symbol_rate}</td>
              <td class="r num">{db(b.snr_db)}</td>
              <td class="r num">{b.quality === null || b.quality === undefined ? '-' : b.quality.toFixed(2)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {:else}
      <p class="muted">None yet.</p>
    {/if}
  </div>
</div>

<style>
  .stack { display: grid; gap: 12px; }
  dl { display: grid; grid-template-columns: max-content 1fr; gap: 4px 12px; margin: 0; }
  dt { color: var(--muted); }
  dd { margin: 0; }
  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  th { text-align: left; color: var(--muted); font-weight: 500; border-bottom: 1px solid var(--grid); padding: 2px 4px; }
  td { padding: 2px 4px; border-bottom: 1px solid var(--grid); }
  .r { text-align: right; }
  .good { color: var(--good-text); }
  .bad { color: var(--critical); }
</style>
