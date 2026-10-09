<script>
  // The radio's receive level, as level_meter.py shows it: rms bar, peak
  // tick, the target zone for open-squelch hiss (-26 to -10 dBFS rms).
  import { station } from './station.svelte.js';

  const LO = -60, HI = 0;
  const pct = (db) => `${Math.max(0, Math.min(100, ((db - LO) / (HI - LO)) * 100))}%`;
  const lv = $derived(station.level);
  const verdict = $derived.by(() => {
    if (!lv) return null;
    if (lv.peak_dbfs > -1) return { text: '✕ clipping - turn the radio down', cls: 'bad' };
    if (lv.rms_dbfs > -10) return { text: 'high', cls: 'warn' };
    if (lv.rms_dbfs < -26) return { text: 'low', cls: 'warn' };
    return { text: '✓ good', cls: 'good' };
  });
</script>

{#if !lv}
  <p class="muted">No level yet (the station isn't on a radio, or hasn't heard anything).</p>
{:else}
  <div class="meter" role="meter" aria-valuemin={LO} aria-valuemax={HI} aria-valuenow={lv.rms_dbfs}
       aria-label="Receive level, dBFS rms">
    <div class="zone" style:left={pct(-26)} style:width="calc({pct(-10)} - {pct(-26)})"></div>
    <div class="bar" style:width={pct(lv.rms_dbfs)}></div>
    <div class="peak" style:left={pct(lv.peak_dbfs)}></div>
  </div>
  <div class="read num">
    rms {lv.rms_dbfs.toFixed(1)} · peak {lv.peak_dbfs.toFixed(1)} dBFS
    {#if lv.transmitting}<span class="muted"> · transmitting (input ignored)</span>
    {:else if verdict}<span class={verdict.cls}> · {verdict.text}</span>{/if}
  </div>
{/if}

<style>
  .meter { position: relative; height: 14px; border-radius: 4px; background: var(--grid); overflow: hidden; }
  .zone { position: absolute; top: 0; bottom: 0; background: var(--zone); }
  .bar { position: absolute; top: 3px; bottom: 3px; left: 0; background: var(--series-1); border-radius: 0 4px 4px 0; }
  .peak { position: absolute; top: 0; bottom: 0; width: 2px; background: var(--ink-2); }
  .read { font-size: 0.85rem; margin-top: 4px; color: var(--ink-2); }
  .good { color: var(--good-text); }
  .warn { color: var(--ink-2); font-weight: 600; }
  .bad { color: var(--critical); font-weight: 600; }
</style>
