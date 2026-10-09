<script>
  import { station } from './station.svelte.js';
  let filter = $state('');
  const shown = $derived(
    (filter ? station.logs.filter((l) => l.toLowerCase().includes(filter.toLowerCase())) : station.logs)
      .slice(-300).reverse());
</script>

<div class="card">
  <div class="top">
    <h2>Log</h2>
    <input bind:value={filter} placeholder="filter" aria-label="Filter the log" />
  </div>
  <pre>{shown.join('\n')}</pre>
</div>

<style>
  .top { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
  input { max-width: 200px; }
  pre {
    margin: 8px 0 0; max-height: 40vh; overflow: auto; font-size: 0.8rem;
    white-space: pre-wrap; overflow-wrap: anywhere; color: var(--ink-2);
  }
</style>
