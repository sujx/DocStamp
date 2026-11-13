<template>
  <section id="tools" class="scroll-mt-20 py-14">
    <div class="mx-auto max-w-5xl px-4 sm:px-6">
      <div class="text-brand-600">
        <LandingSectionKicker :text="$t('landing.tools.kicker')" />
      </div>
      <h2 class="font-official mb-2 mt-2 text-[30px] font-extrabold tracking-wide text-primary">
        {{ $t("landing.tools.title") }}
      </h2>
      <p class="mb-9 max-w-xl text-secondary">{{ $t("landing.tools.note") }}</p>

      <div v-for="group in groups" :key="group.label" class="mb-9 last:mb-0">
        <h3 class="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-tertiary">{{ group.label }}</h3>
        <div class="stagger-children grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <ToolCard
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            :icon="item.icon"
            :title="item.title"
            :description="item.description"
            :flag="item.flag"
          />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  groups: {
    label: string;
    items: { to: string; icon: string; title: string; description: string; flag?: string }[];
  }[];
}>();
</script>
