<script>
  // The receive level over the last 30 s: rms (the series colour) and peak
  // (secondary ink), against the target zone for open-squelch hiss.
  // Direct labels name the two lines; hover reads a moment back.
  import { station } from './station.svelte.js';
  import { load } from './storage.js';
  import YScale from './YScale.svelte';

  // grow: the panel has been resized - fill the height it has.
  let { grow = false } = $props();
  const PAD = { top: 6, right: 40, bottom: 16, left: 30 };
  const DEFAULT = [-60, 0];
  let width = $state(300);
  let boxH = $state(0);
  let hover = $state(null);
  let range = $state(load('yscale.level', null));

  const pts = $derived(station.levels.filter((e) => !e.transmitting));
  const H = $derived(grow ? Math.max(90, boxH - 4) : 90);
  const [LO, HI] = $derived(range || DEFAULT);
  const plotW = $derived(Math.max(40, width - PAD.left - PAD.right));
  const plotH = $derived(H - PAD.top - PAD.bottom);
  const x = (i) => PAD.left + (pts.length <= 1 ? plotW : (i / (pts.length - 1)) * plotW);
  const y = (db) => PAD.top + ((HI - Math.max(LO, Math.min(HI, db))) / (HI - LO)) * plotH;
  const ticks = $derived.by(() => {
    const span = HI - LO, step = span > 40 ? 20 : span > 15 ? 10 : 5;
    const t = [];
    for (let v = Math.ceil(LO / step) * step; v <= HI; v += step) t.push(v);
    return t;
  });
  const zoneTop = $derived(y(Math.min(HI, -10)));
  const zoneBottom = $derived(y(Math.max(LO, -26)));
  function fit() {
    if (!pts.length) return null;
    const lo = Math.min(...pts.map((e) => e.rms_dbfs)), hi = Math.max(...pts.map((e) => e.peak_dbfs));
    return [Math.floor((lo - 3) / 5) * 5, Math.min(0, Math.ceil((hi + 3) / 5) * 5)];
  }
  const line = (key) => pts.map((e, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(e[key]).toFixed(1)}`).join('');
  const last = $derived(pts[pts.length - 1]);

  function move(event) {
    if (!pts.length) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const i = Math.round(((event.clientX - rect.left - PAD.left) / plotW) * (pts.length - 1));
    hover = Math.max(0, Math.min(pts.length - 1, i));
  }
  const hp = $derived(hover === null ? null : pts[hover]);
</script>

<div class="wrap" class:grow bind:clientWidth={width}>
  <div class="box" bind:clientHeight={boxH}>
  {#if pts.length < 2}
    <p class="muted small">The level history fills in while the station listens.</p>
  {:else}
    <svg {width} height={H} role="img" onpointermove={move} onpointerleave={() => (hover = null)}
         aria-label="Receive level over the last 30 seconds: rms {last.rms_dbfs} dBFS, peak {last.peak_dbfs} dBFS">
      {#if zoneBottom > zoneTop}
        <rect x={PAD.left} width={plotW} y={zoneTop} height={zoneBottom - zoneTop} class="zone" />
      {/if}
      {#each ticks as t}
        <line x1={PAD.left} x2={PAD.left + plotW} y1={y(t)} y2={y(t)} class="grid" />
        <text x={PAD.left - 5} y={y(t) + 4} class="tick" text-anchor="end">{t}</text>
      {/each}
      <path d={line('peak_dbfs')} class="peak" />
      <path d={line('rms_dbfs')} class="rms" />
      <text x={PAD.left + plotW + 4} y={y(last.peak_dbfs) + 4} class="lbl">peak</text>
      <text x={PAD.left + plotW + 4} y={y(last.rms_dbfs) + 4} class="lbl">rms</text>
      <text x={PAD.left} y={H - 3} class="tick">30 s ago</text>
      <text x={PAD.left + plotW} y={H - 3} class="tick" text-anchor="end">now</text>
      {#if hp}
        <line x1={x(hover)} x2={x(hover)} y1={PAD.top} y2={PAD.top + plotH} class="cross" />
      {/if}
    </svg>
    {#if hp}
      <div class="tip num" style:left="{Math.min(x(hover) + 8, width - 150)}px">
        {new Date(hp.time * 1000).toLocaleTimeString()}<br />rms {hp.rms_dbfs} · peak {hp.peak_dbfs} dBFS
      </div>
    {/if}
  {/if}
  </div>
  <YScale id="level" bind:range unit="dBFS" auto={DEFAULT} {fit} />
</div>

<style>
  .wrap { position: relative; width: 100%; margin-top: 8px; display: flex; flex-direction: column; }
  .wrap.grow { flex: 1 1 auto; min-height: 150px; }
  .box { position: relative; }
  .grow .box { flex: 1 1 auto; min-height: 0; }
  svg { display: block; touch-action: pan-y; }
  .zone { fill: var(--zone); }
  .grid { stroke: var(--grid); }
  .tick { fill: var(--muted); font-size: 10px; }
  .lbl { fill: var(--ink-2); font-size: 11px; }
  .rms { fill: none; stroke: var(--series-1); stroke-width: 2; stroke-linejoin: round; }
  .peak { fill: none; stroke: var(--ink-2); stroke-width: 1; stroke-dasharray: 3 2; }
  .cross { stroke: var(--axis); }
  .tip { position: absolute; top: 4px; width: 145px; padding: 4px 6px; font-size: 0.75rem; pointer-events: none;
         background: var(--surface); border: 1px solid var(--ring); border-radius: 6px; }
  .small { font-size: 0.85rem; margin: 6px 0 0; }
</style>
