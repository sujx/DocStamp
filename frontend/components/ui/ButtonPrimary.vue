<template>
  <button
    class="btn-primary"
    :disabled="disabled"
    :type="type"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  disabled?: boolean;
  type?: "button" | "submit" | "reset";
}>(), {
  disabled: false,
  type: "button",
});
</script>

<style scoped>
.btn-primary {
  background: var(--color-brand-700);
  color: #fff;
  border: none;
  border-radius: var(--radius-md, 10px);
  padding: 8px 16px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s ease, opacity 0.15s ease;
}
.btn-primary:hover:not(:disabled) {
  background: var(--color-brand-800);
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
