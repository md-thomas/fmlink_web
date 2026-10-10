<script>
  // The last received burst's symbols (I/Q), normalised so the transmitted
  // points sit on the unit circle; the burst before it is drawn fainter.
  // Tight clusters on the + marks = a clean link; spread clusters = noise;
  // a rotated or smeared ring = distortion or drift.
  import { station } from './station.svelte.js';

  const IDEAL = {
    bpsk: [[-1, 0], [1, 0]],
    qpsk: [[-0.707, -0.707], [-0.707, 0.707], [0.707, -0.707], [0.707, 0.707]],
    '16qam': [-0.949, -0.316, 0.316, 0.949].flatMap((a) => [-0.949, -0.316, 0.316, 0.949].map((b) => [a, b])),
  };
  let { height = null } = $props();   // the panel's height once resized
  const R = 1.5;   // plotted range: -1.5 .. +1.5 on both axes; outliers pinned to the edge
  let size = $state(300);
  const side = $derived(Math.max(120, Math.min(size, height ? height - 34 : 340)));
  const c = $derived(station.constellation);
  const prev = $derived(station.prevConstellation);
  const sx = (v) => ((Math.max(-R, Math.min(R, v)) + R) / (2 * R)) * side;
  const sy = (v) => side - ((Math.max(-R, Math.min(R, v)) + R) / (2 * R)) * side;
  const ideal = $derived(c ? IDEAL[c.modulation] || [] : []);
  const label = $derived(c
    ? `Constellation of the last burst: ${c.points.length} ${c.modulation} symbols` +
      (c.snr_db === null || c.snr_db === undefined ? '' : `, SNR ${c.snr_db.toFixed(1)} dB`)
    : 'No burst received yet');
</script>

<div class="wrap" bind:clientWidth={size}>
  {#if !c}
    <p class="muted">No burst received yet.</p>
  {:else}
    <svg width={side} height={side} role="img" aria-label={label}>
      <rect x="0" y="0" width={side} height={side} class="frame" />
      <circle cx={sx(0)} cy={sy(0)} r={sx(1) - sx(0)} class="unit" />
      <line x1={sx(-R)} x2={sx(R)} y1={sy(0)} y2={sy(0)} class="axis" />
      <line x1={sx(0)} x2={sx(0)} y1={sy(-R)} y2={sy(R)} class="axis" />
      {#if prev && prev.modulation === c.modulation}
        {#each prev.points as [i, q]}<circle cx={sx(i)} cy={sy(q)} r="2" class="prev" />{/each}
      {/if}
      {#each c.points as [i, q]}<circle cx={sx(i)} cy={sy(q)} r="2.2" class="pt" />{/each}
      {#each ideal as [i, q]}
        <path d="M{sx(i) - 6},{sy(q)}h12M{sx(i)},{sy(q) - 6}v12" class="ideal" />
      {/each}
      <text x="6" y="14" class="lbl">Q</text>
      <text x={side - 6} y={sy(0) - 6} class="lbl" text-anchor="end">I</text>
    </svg>
    <div class="read num secondary">
      {c.modulation.toUpperCase()} · {c.points.length} symbols
      {#if c.snr_db !== null && c.snr_db !== undefined} · SNR {c.snr_db.toFixed(1)} dB{/if}
      {#if c.status && c.status !== 'ok'}<span class="bad"> · ✕ {c.status}</span>{/if}
      <span class="muted"> · + ideal · faint = burst before</span>
    </div>
  {/if}
</div>

<style>
  .wrap { width: 100%; }
  svg { display: block; margin: 0 auto; }
  .frame { fill: var(--surface); stroke: var(--grid); }
  .unit { fill: none; stroke: var(--grid); stroke-dasharray: 3 3; }
  .axis { stroke: var(--axis); stroke-width: 1; }
  .pt { fill: var(--series-1); fill-opacity: 0.65; }
  .prev { fill: var(--series-1); fill-opacity: 0.15; }
  .ideal { stroke: var(--ink); stroke-width: 2; }
  .lbl { fill: var(--muted); font-size: 11px; }
  .read { font-size: 0.85rem; margin-top: 6px; text-align: center; }
  .bad { color: var(--critical); }
</style>
