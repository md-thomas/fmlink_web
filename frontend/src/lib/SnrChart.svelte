<script>
  // SNR of the last received bursts, oldest left. One series (no legend:
  // the title names it). Failed bursts are ✕ markers in the status colour;
  // the dashed line is where the current mode stops decoding reliably.
  import { station, MODE_LIMIT_DB } from './station.svelte.js';
  import { load } from './storage.js';
  import YScale from './YScale.svelte';

  let { height = null } = $props();   // the panel's height once resized
  const N = 60;
  const H = $derived(height ? Math.max(120, height - 40) : 180);   // 40: the Y-scale row
  let range = $state(load('yscale.snr', null));   // [min, max] dB the user chose, or null: auto
  const PAD = { top: 10, right: 12, bottom: 22, left: 34 };
  let width = $state(400);
  let hover = $state(null);   // index into points

  const points = $derived(station.bursts.slice(-N).map((b, i) => ({ ...b, i })));
  const limit = $derived(station.link ? MODE_LIMIT_DB[station.link.mode_id] : null);
  const autoDomain = $derived.by(() => {
    const vals = points.map((p) => p.snr_db).filter((v) => v !== null);
    if (limit !== null && limit !== undefined) vals.push(limit);
    const lo = Math.min(0, ...vals), hi = Math.max(25, ...vals);
    return [Math.floor(lo / 5) * 5, Math.ceil(hi / 5) * 5];
  });
  const domain = $derived(range || autoDomain);
  function fit() {
    const vals = points.map((p) => p.snr_db).filter((v) => v !== null);
    if (!vals.length) return null;
    return [Math.floor((Math.min(...vals) - 2) / 2) * 2, Math.ceil((Math.max(...vals) + 2) / 2) * 2];
  }
  const plotW = $derived(Math.max(50, width - PAD.left - PAD.right));
  const plotH = $derived(H - PAD.top - PAD.bottom);
  const x = (i) => PAD.left + (points.length <= 1 ? plotW / 2 : (i / (points.length - 1)) * plotW);
  const y = (v) => PAD.top + plotH - ((Math.max(domain[0], Math.min(domain[1], v)) - domain[0]) / (domain[1] - domain[0])) * plotH;
  const ticks = $derived.by(() => {
    const span = domain[1] - domain[0];
    const step = span > 30 ? 10 : span > 12 ? 5 : span > 5 ? 2 : 1;
    const t = [];
    for (let v = Math.ceil(domain[0] / step) * step; v <= domain[1]; v += step) t.push(v);
    return t;
  });
  const ok = $derived(points.filter((p) => p.status === 'ok' && p.snr_db !== null));
  const failed = $derived(points.filter((p) => p.status !== 'ok'));
  const path = $derived(ok.map((p, k) => `${k ? 'L' : 'M'}${x(p.i).toFixed(1)},${y(p.snr_db).toFixed(1)}`).join(''));
  const time = (t) => new Date(t * 1000).toLocaleTimeString();

  function move(event) {
    if (!points.length) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const px = event.clientX - rect.left;
    const i = points.length <= 1 ? 0 : Math.round(((px - PAD.left) / plotW) * (points.length - 1));
    hover = Math.max(0, Math.min(points.length - 1, i));
  }
  const hp = $derived(hover === null ? null : points[hover]);
  const summary = $derived(ok.length
    ? `SNR of the last ${points.length} bursts: latest ${ok[ok.length - 1].snr_db.toFixed(1)} dB, ${failed.length} not decoded`
    : 'No bursts received yet');
</script>

<div class="wrap" bind:clientWidth={width}>
  {#if !points.length}
    <p class="muted empty">No bursts received yet.</p>
  {:else}
    <svg {width} height={H} role="img" aria-label={summary}
         onpointermove={move} onpointerleave={() => (hover = null)}>
      {#each ticks as t}
        <line x1={PAD.left} x2={PAD.left + plotW} y1={y(t)} y2={y(t)} class="grid" />
        <text x={PAD.left - 6} y={y(t) + 4} class="tick" text-anchor="end">{t}</text>
      {/each}
      <text x={PAD.left - 6} y={H - 4} class="tick" text-anchor="end">dB</text>
      {#if limit !== null && limit !== undefined && limit >= domain[0] && limit <= domain[1]}
        <line x1={PAD.left} x2={PAD.left + plotW} y1={y(limit)} y2={y(limit)} class="limit" />
        <text x={PAD.left + plotW} y={y(limit) - 4} class="tick" text-anchor="end">
          mode {station.link.mode_id} limit ≈ {limit} dB
        </text>
      {/if}
      <path d={path} class="line" />
      {#each ok as p}
        <circle cx={x(p.i)} cy={y(p.snr_db)} r="3" class="dot" />
      {/each}
      {#each failed as p}
        <text x={x(p.i)} y={p.snr_db === null ? PAD.top + plotH - 2 : y(p.snr_db) + 4}
              class="fail" text-anchor="middle">✕</text>
      {/each}
      {#if hp}
        <line x1={x(hp.i)} x2={x(hp.i)} y1={PAD.top} y2={PAD.top + plotH} class="cross" />
      {/if}
      <text x={PAD.left} y={H - 4} class="tick">{time(points[0].time)}</text>
      <text x={PAD.left + plotW} y={H - 4} class="tick" text-anchor="end">{time(points[points.length - 1].time)}</text>
    </svg>
    {#if hp}
      <div class="tip" style:left="{Math.min(x(hp.i) + 10, width - 190)}px">
        <div class="num">{time(hp.time)}</div>
        <div>{hp.status === 'ok' ? '✓ decoded' : `✕ ${hp.status}`} · {hp.modulation} {hp.symbol_rate}</div>
        <div class="num">SNR {hp.snr_db === null ? '-' : hp.snr_db.toFixed(1) + ' dB'} · sync {hp.quality === null ? '-' : hp.quality.toFixed(2)}</div>
      </div>
    {/if}
  {/if}
  <YScale id="snr" bind:range unit="dB" auto={autoDomain} {fit} />
</div>

<style>
  .wrap { position: relative; width: 100%; }
  svg { display: block; touch-action: pan-y; }
  .grid { stroke: var(--grid); stroke-width: 1; }
  .tick { fill: var(--muted); font-size: 11px; }
  .limit { stroke: var(--ink-2); stroke-width: 1; stroke-dasharray: 4 4; }
  .line { fill: none; stroke: var(--series-1); stroke-width: 2; stroke-linejoin: round; }
  .dot { fill: var(--series-1); stroke: var(--surface); stroke-width: 2; }
  .fail { fill: var(--critical); font-size: 13px; font-weight: 700; }
  .cross { stroke: var(--axis); stroke-width: 1; }
  .tip {
    position: absolute; top: 8px; width: 180px; padding: 6px 8px; font-size: 0.8rem;
    background: var(--surface); border: 1px solid var(--ring); border-radius: 6px; pointer-events: none;
    box-shadow: 0 2px 8px #0002;
  }
  .empty { margin: 8px 0; }
</style>
