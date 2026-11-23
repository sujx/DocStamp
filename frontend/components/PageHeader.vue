<template>
  <div class="mb-6">
    <ULink
      :to="backTo"
      class="mb-2 inline-flex min-h-[32px] items-center gap-2 text-[13px] text-secondary transition-colors hover:text-brand-700"
    >
      <UIcon name="i-heroicons-arrow-left" class="size-4" />
      {{ $t("common.back") }}
    </ULink>
    <h1 v-if="title" class="text-[28px] font-medium leading-tight text-primary">{{ title }}</h1>
    <p v-if="description" class="mt-2 max-w-xl text-[15px] leading-relaxed text-secondary text-pretty">{{ description }}</p>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  backTo?: string
  title?: string
  description?: string
}>(), {
  backTo: "/tools",
});
</script>
