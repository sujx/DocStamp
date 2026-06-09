<template>
  <div class="mb-6">
    <NuxtLink :to="backTo" class="inline-flex items-center gap-1 text-sm hover:underline" >
      <UIcon name="i-heroicons-arrow-left" class="w-4 h-4" />
      {{ $t("common.back") }}
    </NuxtLink>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ backTo?: string }>(), { backTo: "/" });
</script>
