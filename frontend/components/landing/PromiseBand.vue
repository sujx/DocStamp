<template>
  <section id="promise" class="scroll-mt-20 py-20">
    <div class="mx-auto max-w-5xl px-4 sm:px-6">
      <div class="rounded-xl border border-default bg-raised px-6 py-10 sm:px-10">
        <LandingSectionKicker :text="kicker" />
        <h2 class="font-official mb-3 mt-3 text-[28px] font-medium leading-tight text-primary">{{ title }}</h2>
        <p class="mb-8 max-w-2xl text-[15px] leading-relaxed text-secondary">{{ sub }}</p>

        <div class="grid grid-cols-1 gap-6 md:grid-cols-3">
          <div
            v-for="item in items"
            :key="item.title"
            class="border-l border-default pl-4"
          >
            <b class="mb-1 block text-[15px] font-medium text-primary">{{ item.title }}</b>
            <span class="text-[13px] leading-relaxed text-secondary">{{ item.body }}</span>
          </div>
        </div>

        <div class="mt-8 border-t border-default pt-6">
          <h3 class="mb-3 text-[13px] text-secondary">{{ notesTitle }}</h3>
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div v-for="note in notes" :key="note.title">
              <b class="mb-1 block text-[13px] font-medium text-primary">{{ note.title }}</b>
              <span class="text-[12px] leading-relaxed text-secondary">{{ note.body }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  kicker: string;
  title: string;
  sub: string;
  items: { title: string; body: string }[];
  notesTitle: string;
  notes: { title: string; body: string }[];
}>();
</script>
