<script>
  import { station } from './station.svelte.js';
  import Panel from './Panel.svelte';
  let filter = $state('');
  const shown = $derived(
    (filter ? station.logs.filter((l) => l.toLowerCase().includes(filter.toLowerCase())) : station.logs)
      .slice(-300).reverse());
</script>

<Panel id="log" title="Log" height="min(70vh, 640px)" fill>
  {#snippet actions()}
    <input bind:value={filter} placeholder="filter" aria-label="Filter the log" />
  {/snippet}
  {#snippet children()}
    <pre>{shown.join('\n')}</pre>
  {/snippet}
</Panel>

<style>
  input { max-width: 200px; padding: 3px 8px; }
  pre {
    flex: 1; min-height: 0; margin: 0; overflow: auto; font-size: 0.8rem;
    white-space: pre-wrap; overflow-wrap: anywhere; color: var(--ink-2);
  }
</style>
