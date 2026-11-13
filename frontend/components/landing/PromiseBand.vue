<template>
  <section id="promise" class="scroll-mt-20 py-14">
    <div class="mx-auto max-w-5xl px-4 sm:px-6">
      <div class="bg-brand-950 px-5 py-10 shadow-elevated sm:px-10">
        <div class="text-brand-300">
          <LandingSectionKicker :text="kicker" />
        </div>
        <h2 class="font-official mb-2 mt-2 text-[26px] font-extrabold tracking-wide text-white">{{ title }}</h2>
        <p class="mb-8 max-w-2xl text-sm leading-relaxed text-brand-100">{{ sub }}</p>

        <div class="grid grid-cols-1 gap-6 md:grid-cols-3">
          <div
            v-for="item in items"
            :key="item.title"
            class="border-l-2 border-brand-400/50 pl-4"
          >
            <b class="mb-1 block text-[15px] text-white">{{ item.title }}</b>
            <span class="text-[13px] leading-relaxed text-brand-100">{{ item.body }}</span>
          </div>
        </div>

        <div class="mt-9 border-t border-brand-800 pt-6">
          <h3 class="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-brand-300">{{ notesTitle }}</h3>
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div v-for="note in notes" :key="note.title">
              <b class="mb-1 block text-[13px] text-white">{{ note.title }}</b>
              <span class="text-[12px] leading-relaxed text-brand-200">{{ note.body }}</span>
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
