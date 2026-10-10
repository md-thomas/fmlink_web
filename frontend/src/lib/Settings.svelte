<script>
  // Station settings, changed while it runs (PATCH /api/settings). The
  // fields follow the station until edited; Apply sends only what changed.
  // Mode, FEC and batching changes are passed to the peer by the station.
  import { station, updateSettings } from './station.svelte.js';
  import Panel from './Panel.svelte';

  let options = $state(null);
  $effect(() => {
    fetch('/api/options').then((r) => r.json()).then((o) => (options = o)).catch(() => {});
  });

  // Each field: how the page shows it, and how to turn that back into the
  // station's value. Times are shown in ms (lead-in, turnaround) or s.
  const FIELDS = {
    mode_id: { get: (l) => l.mode_id, put: Number },
    fec_preset: { get: (l) => l.fec_preset, put: String },
    bandwidth: { get: (l) => l.bandwidth, put: String },
    ack: { get: (l) => l.ack, put: Boolean },
    auto: { get: (l) => l.auto, put: Boolean },
    batching: { get: (l) => l.batching, put: Boolean },
    lead_in_s: { get: (l) => Math.round(l.lead_in_s * 1000), put: (v) => Number(v) / 1000 },
    max_tx_s: { get: (l) => l.max_tx_s, put: Number },
    tx_level: { get: (l) => l.tx_level, put: Number },
    turnaround_s: { get: (l) => (l.turnaround_s === null ? null : Math.round(l.turnaround_s * 1000)),
                    put: (v) => Number(v) / 1000 },
  };

  // Ranges as the page shows them (the station checks again, in its units).
  const RANGES = {
    lead_in_s: ['Lead-in', 0, 2000, 'ms'],
    max_tx_s: ['Max transmission', 1, 300, 's'],
    tx_level: ['TX level', 0.01, 1, ''],
    turnaround_s: ['Turnaround', 0, 10000, 'ms'],
  };
  function problems() {
    return Object.entries(RANGES)
      .filter(([key]) => edited[key])
      .filter(([key, [, lo, hi]]) => {
        const v = Number(form[key]);
        return form[key] === '' || form[key] === null || !Number.isFinite(v) || v < lo || v > hi;
      })
      .map(([, [label, lo, hi, unit]]) => `${label} must be ${lo} to ${hi}${unit ? ' ' + unit : ''}`);
  }

  let form = $state({});
  let edited = $state({});
  let busy = $state(false);
  let result = $state(null);

  const l = $derived(station.link);
  const radio = $derived(l && l.tx_level !== null);

  // Follow the station for every field the user hasn't touched.
  $effect(() => {
    if (!l) return;
    for (const [key, f] of Object.entries(FIELDS)) {
      if (!edited[key]) form[key] = f.get(l);
    }
  });

  const changes = $derived.by(() => {
    if (!l) return {};
    const out = {};
    for (const [key, f] of Object.entries(FIELDS)) {
      if (edited[key] && form[key] !== f.get(l)) {
        out[key] = f.put(form[key]);
      }
    }
    return out;
  });
  const count = $derived(Object.keys(changes).length);

  function touch(key) {
    edited[key] = true;
    result = null;
  }

  function revert() {
    edited = {};
    result = null;
  }

  async function apply() {
    const bad = problems();
    if (bad.length) {
      result = { ok: false, text: '✕ ' + bad.join('; ') };
      return;
    }
    busy = true;
    result = null;
    try {
      // (A new mode without a chosen FEC takes the mode's own preset, as /mode does.)
      const sent = { ...changes };
      await updateSettings(sent);
      edited = {};
      result = { ok: true, text: `✓ applied: ${Object.keys(sent).join(', ')}` };
    } catch (err) {
      result = { ok: false, text: '✕ ' + err.message };
    } finally {
      busy = false;
    }
  }

  const modeLabel = (m) => `${m.mode_id} - ${m.modulation.toUpperCase()} ${m.symbol_rate} sym/s`;
  const modeAllowed = (m) => !l || l.max_symbol_rate === null || m.symbol_rate <= l.max_symbol_rate;
</script>

<Panel id="settings" title="Settings">
{#snippet children()}
  {#if !l}
    <p class="muted">Waiting for the station…</p>
  {:else}
    <div class="grid">
      <fieldset>
        <legend>Link</legend>
        <label>Mode
          <select bind:value={form.mode_id} onchange={() => touch('mode_id')} disabled={!options}>
            {#each options ? options.modes : [] as m}
              <option value={m.mode_id} disabled={!modeAllowed(m)}>
                {modeLabel(m)}{modeAllowed(m) ? '' : ' (too fast for this port)'}
              </option>
            {/each}
          </select>
        </label>
        <label>FEC preset
          <select bind:value={form.fec_preset} onchange={() => touch('fec_preset')} disabled={!options}>
            {#each options ? options.fec_presets : [] as p}<option value={p}>{p}</option>{/each}
          </select>
        </label>
        <label>Bandwidth (ceiling for auto)
          <select bind:value={form.bandwidth} onchange={() => touch('bandwidth')}>
            <option value="wide">wide</option>
            <option value="narrow">narrow (≤ 1200 sym/s)</option>
          </select>
        </label>
      </fieldset>

      <fieldset>
        <legend>Behaviour</legend>
        <label class="check"><input type="checkbox" bind:checked={form.ack} onchange={() => touch('ack')} />
          ACK - confirm delivery, resend if lost</label>
        <label class="check"><input type="checkbox" bind:checked={form.auto} onchange={() => touch('auto')} />
          Auto - negotiate the mode on the next message</label>
        <label class="check"><input type="checkbox" bind:checked={form.batching} onchange={() => touch('batching')} />
          Burst batching - several segments per transmission</label>
      </fieldset>

      <fieldset>
        <legend>Timing</legend>
        <label>Lead-in (ms)
          <input type="number" min="0" max="2000" step="10" bind:value={form.lead_in_s}
                 oninput={() => touch('lead_in_s')} />
        </label>
        <label>Max transmission (s)
          <input type="number" min="1" max="300" step="1" bind:value={form.max_tx_s}
                 oninput={() => touch('max_tx_s')} />
        </label>
      </fieldset>

      <fieldset disabled={!radio}>
        <legend>Radio{radio ? '' : ' (not on a radio)'}</legend>
        <label>TX level (0.01 - 1)
          <input type="number" min="0.01" max="1" step="0.05" bind:value={form.tx_level}
                 oninput={() => touch('tx_level')} />
        </label>
        <label>Turnaround (ms)
          <input type="number" min="0" max="10000" step="100" bind:value={form.turnaround_s}
                 oninput={() => touch('turnaround_s')} />
        </label>
      </fieldset>
    </div>

    <div class="bar">
      <button class="primary" onclick={apply} disabled={!station.online || busy || !count}>
        {busy ? 'Applying…' : count ? `Apply ${count} change${count > 1 ? 's' : ''}` : 'Apply'}
      </button>
      <button onclick={revert} disabled={busy || !Object.keys(edited).length}>Revert</button>
      {#if result}<span class={result.ok ? 'good' : 'bad'}>{result.text}</span>{/if}
    </div>
    <p class="muted note">Mode, FEC and batching changes are sent to {l.dst_id} too, so both
      stations switch together (it takes a few seconds on air).</p>
  {/if}
{/snippet}
</Panel>

<style>
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 10px 14px; }
  fieldset { border: 1px solid var(--grid); border-radius: 6px; margin: 0; padding: 6px 10px 10px;
             display: grid; gap: 8px; align-content: start; min-width: 0; }
  fieldset:disabled { opacity: 0.55; }
  legend { color: var(--ink-2); font-size: 0.85rem; font-weight: 600; padding: 0 4px; }
  label { display: grid; gap: 3px; font-size: 0.85rem; color: var(--ink-2); }
  label.check { display: flex; gap: 8px; align-items: flex-start; color: var(--ink); }
  label.check input { margin-top: 3px; }
  select, input[type='number'] { color: var(--ink); width: 100%; }
  .bar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 10px; }
  .good { color: var(--good-text); font-size: 0.9rem; }
  .bad { color: var(--critical); font-size: 0.9rem; }
  .note { font-size: 0.8rem; margin: 6px 0 0; }
</style>
