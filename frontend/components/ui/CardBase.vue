<template>
  <div
    class="card bg-surface border-default"
    :style="{ borderRadius: `var(--radius-${radius})` }"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  radius?: "sm" | "md" | "lg";
}>(), {
  radius: "md",
});
</script>
