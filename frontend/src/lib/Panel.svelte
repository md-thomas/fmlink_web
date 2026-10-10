<script>
  // A collapsible, resizable card. Drag the bottom-right corner to change its
  // height (↺ puts it back); click the title to collapse it. Both are
  // remembered per panel in this browser (localStorage - best effort).
  //
  //   <Panel id="chat" title="Chat" height="min(70vh, 640px)" fill>
  //     {#snippet children(size)} ... size.height: px when resized, else null {/snippet}
  //   </Panel>
  //
  // height: the default height (any CSS length); without it the panel fits
  // its content. fill: the body is a flex column, for content that should
  // stretch (chat, log).
  import { load, save } from './storage.js';

  let { id, title, height = null, fill = false, actions = null, children } = $props();

  let collapsed = $state(load(`panel.${id}.collapsed`, false));
  let custom = $state(load(`panel.${id}.height`, null));   // px, once resized
  let body = $state();

  $effect(() => save(`panel.${id}.collapsed`, collapsed));

  // The browser's resize handle writes an inline height on the body; keep it.
  $effect(() => {
    if (!body) return;
    const observer = new ResizeObserver(() => {
      if (body.style.height) {
        custom = Math.round(body.getBoundingClientRect().height);
        save(`panel.${id}.height`, custom);
      }
    });
    observer.observe(body);
    return () => observer.disconnect();
  });

  function reset() {
    custom = null;
    save(`panel.${id}.height`, null);
    if (body) body.style.height = '';
  }

  // Only a user's resize (or its remembered size) goes in the inline height
  // the browser's handle writes; the default comes in through a variable, so
  // it isn't mistaken for a resize.
</script>

<section class="panel" class:collapsed>
  <header>
    <button class="toggle" aria-expanded={!collapsed} onclick={() => (collapsed = !collapsed)}
            title={collapsed ? 'Expand' : 'Collapse'}>
      <span class="chev" aria-hidden="true">{collapsed ? '▸' : '▾'}</span>
      <h2>{title}</h2>
    </button>
    {#if !collapsed && actions}<div class="actions">{@render actions()}</div>{/if}
    {#if !collapsed && custom}
      <button class="reset" onclick={reset} title="Default size" aria-label="Default size">↺</button>
    {/if}
  </header>
  {#if !collapsed}
    <div class="body" class:fill bind:this={body} style:--default-height={height}
         style:height={custom ? `${custom}px` : null}>
      {@render children({ height: custom })}
    </div>
  {/if}
</section>

<style>
  .panel {
    background: var(--surface); border: 1px solid var(--ring); border-radius: 8px;
    padding: 8px 12px 12px; min-width: 0;
  }
  .panel.collapsed { padding-bottom: 8px; }
  header { display: flex; align-items: center; gap: 8px; min-height: 30px; }
  .toggle {
    display: flex; align-items: center; gap: 6px; border: 0; background: none; padding: 2px 0;
    text-align: left; flex: 0 1 auto; min-width: 0;
  }
  .chev { color: var(--muted); width: 1em; }
  h2 { margin: 0; }
  .actions { margin-left: auto; display: flex; gap: 6px; align-items: center; }
  .reset { margin-left: auto; padding: 0 8px; color: var(--muted); }
  .actions + .reset { margin-left: 0; }
  .body {
    margin-top: 6px; overflow: auto; resize: vertical; min-height: 60px;
    height: var(--default-height, auto);
  }
  .body.fill { display: flex; flex-direction: column; overflow: hidden; padding-bottom: 14px; }  /* room for the grip */
</style>
