<script>
  // The y range of a line chart: type a min/max, Fit to the data shown, or
  // Reset to the chart's default. Remembered per chart in this browser.
  //   <YScale id="snr" bind:range unit="dB" auto={[0, 25]} fit={() => [lo, hi]} />
  // range: [min, max] the user chose, or null for the chart's default
  // (shown as the inputs' placeholders, from `auto`).
  import { save } from './storage.js';

  let { id, range = $bindable(null), auto = [0, 1], fit, unit = '' } = $props();

  let lo = $state(range ? range[0] : null);
  let hi = $state(range ? range[1] : null);
  let error = $state(null);

  function set(next) {
    range = next;
    lo = next ? next[0] : null;
    hi = next ? next[1] : null;
    error = null;
    save(`yscale.${id}`, next);
  }

  function typed() {
    const a = lo === null || lo === '' ? auto[0] : Number(lo);
    const b = hi === null || hi === '' ? auto[1] : Number(hi);
    if (!Number.isFinite(a) || !Number.isFinite(b) || a >= b) {
      error = 'min must be below max';
      return;
    }
    set([a, b]);
  }

  function fitData() {
    const r = fit && fit();
    if (r) set(r);
  }
</script>

<div class="yscale">
  <span class="muted">Y</span>
  <input type="number" bind:value={lo} placeholder={String(auto[0])} onchange={typed}
         aria-label="Y axis minimum" />
  <span class="muted">to</span>
  <input type="number" bind:value={hi} placeholder={String(auto[1])} onchange={typed}
         aria-label="Y axis maximum" />
  {#if unit}<span class="muted">{unit}</span>{/if}
  <button onclick={fitData} title="Fit the range to the data shown">Fit</button>
  <button onclick={() => set(null)} disabled={!range} title="Back to the default range">Reset</button>
  {#if error}<span class="bad">{error}</span>{/if}
</div>

<style>
  .yscale { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; font-size: 0.8rem; margin-top: 4px; }
  input { width: 64px; padding: 2px 6px; font-size: 0.8rem; }
  button { padding: 2px 8px; font-size: 0.8rem; }
  .bad { color: var(--critical); }
</style>
