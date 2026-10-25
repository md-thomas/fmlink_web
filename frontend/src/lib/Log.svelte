<script>
  import { station } from './station.svelte.js';
  import Panel from './Panel.svelte';
  let filter = $state('');
  const time = (t) => new Date(t * 1000).toLocaleTimeString();
  const shown = $derived(
    (filter ? station.logs.filter((l) => l.text.toLowerCase().includes(filter.toLowerCase())) : station.logs)
      .slice(-300).reverse());
</script>

<Panel id="log" title="Log" height="min(70vh, 640px)" fill>
  {#snippet actions()}
    <input bind:value={filter} placeholder="filter" aria-label="Filter the log" />
  {/snippet}
  {#snippet children()}
    <pre>{#each shown as l}<span class="time">{time(l.time)}</span> {l.text}
{/each}</pre>
  {/snippet}
</Panel>

<style>
  input { max-width: 200px; padding: 3px 8px; }
  pre {
    flex: 1; min-height: 0; margin: 0; overflow: auto; font-size: 0.8rem;
    white-space: pre-wrap; overflow-wrap: anywhere; color: var(--ink-2);
  }
  .time { color: var(--muted); }
</style>
