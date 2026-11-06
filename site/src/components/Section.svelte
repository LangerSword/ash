<script lang="ts">
  import type { Snippet } from "svelte";
  import { drawRule, reveal } from "../lib/anim";

  let { id, title, children }: { id?: string; title: string; children: Snippet } = $props();
</script>

<section class="section" id={id}>
  <div class="section-head" use:reveal>
    <h2>{title}</h2>
    <div class="rule" use:drawRule></div>
  </div>
  <div use:reveal>
    {@render children()}
  </div>
</section>
