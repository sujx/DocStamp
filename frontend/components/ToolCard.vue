<template>
  <NuxtLink
    :to="to"
    class="card card-interactive group flex gap-5 p-5"
  >
    <div class="icon-badge shrink-0 !size-12">
      <UIcon :name="icon" class="size-6" />
    </div>
    <div class="min-w-0 flex-1">
      <h3 class="mb-1.5 flex items-center gap-2 text-[15px] font-semibold leading-tight text-primary">
        <span>{{ title }}</span>
        <span
          v-if="flag"
          class="rounded-full bg-seal/10 px-2 py-0.5 text-[11px] font-medium whitespace-nowrap text-seal no-underline"
        >{{ flag }}</span>
      </h3>
      <p class="line-clamp-2 text-[13px] leading-relaxed text-secondary">{{ description }}</p>
    </div>
    <UIcon
      name="i-heroicons-arrow-right"
      class="size-5 shrink-0 -translate-x-1 self-center text-tertiary opacity-0 transition-[opacity,transform,color] duration-200 group-hover:translate-x-0 group-hover:opacity-100 group-hover:text-brand-600"
    />
  </NuxtLink>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  icon: string;
  title: string;
  description: string;
  to: string;
  flag?: string;
}>(), {
  flag: undefined,
});
</script>
