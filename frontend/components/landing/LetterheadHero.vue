<template>
  <header class="letterhead animate-fade-up">
    <div class="mx-auto max-w-5xl px-4 sm:px-6">
      <p class="lh-no">{{ no }}</p>
      <h1 class="lh-title font-official">{{ title }}</h1>
      <p class="lh-sub">{{ sub }}</p>
      <div class="lh-rule" aria-hidden="true"></div>
      <p class="hero-lede">{{ lede }}</p>
      <div class="mt-8 flex flex-wrap justify-center gap-3">
        <NuxtLink
          :to="primaryTo"
          class="inline-flex min-h-[44px] items-center rounded-lg bg-brand-500 px-6 text-[15px] font-semibold text-white no-underline transition-[background-color,transform] duration-200 hover:bg-brand-600"
        >{{ primaryLabel }}</NuxtLink>
        <NuxtLink
          :to="secondaryTo"
          class="inline-flex min-h-[44px] items-center rounded-lg border border-brand-200 bg-surface px-6 text-[15px] font-semibold text-brand-700 no-underline transition-[background-color,border-color] duration-200 hover:border-brand-400 hover:bg-brand-50"
        >{{ secondaryLabel }}</NuxtLink>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{
  no: string;
  title: string;
  sub: string;
  lede: string;
  primaryTo: string;
  primaryLabel: string;
  secondaryTo: string;
  secondaryLabel: string;
}>();
</script>
