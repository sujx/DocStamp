<template>
  <section id="tools" class="scroll-mt-20 py-20">
    <div class="mx-auto max-w-5xl px-4 sm:px-6">
      <LandingSectionKicker :text="$t('landing.tools.kicker')" />
      <h2 class="font-official mb-3 mt-3 text-[28px] font-medium leading-tight text-primary">
        {{ $t("landing.tools.title") }}
      </h2>
      <p class="mb-8 max-w-xl text-secondary">{{ $t("landing.tools.note") }}</p>

      <div v-for="group in groups" :key="group.label" class="mb-8 last:mb-0">
        <h3 class="mb-2 text-[13px] text-secondary">{{ group.label }}</h3>
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
