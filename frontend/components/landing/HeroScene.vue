<template>
  <header class="hero-scene">
    <img
      class="hero-scene__img"
      src="/images/hero-desk.webp"
      :alt="$t('landing.hero.imgAlt')"
      width="1280"
      height="952"
      fetchpriority="high"
      decoding="async"
    />
    <div class="hero-scene__fade-top" aria-hidden="true" />
    <div class="hero-scene__fade-bottom" aria-hidden="true" />
    <div class="hero-scene__calm" aria-hidden="true" />

    <div class="hero-scene__inner">
      <div class="hero-copy animate-fade-up">
        <p class="hero-kicker">{{ kicker }}</p>
        <h1 class="hero-title">{{ title }}</h1>
        <p class="hero-lede">{{ lede }}</p>
        <div class="hero-actions">
          <NuxtLink :to="primaryTo" class="hero-btn">{{ primaryLabel }}</NuxtLink>
          <NuxtLink :to="secondaryTo" class="hero-btn hero-btn--ghost">{{ secondaryLabel }}</NuxtLink>
        </div>
      </div>

      <div class="flex justify-center lg:justify-end">
        <DocPreview />
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import DocPreview from "~/components/landing/DocPreview.vue";

defineProps<{
  kicker: string;
  title: string;
  lede: string;
  primaryTo: string;
  primaryLabel: string;
  secondaryTo: string;
  secondaryLabel: string;
}>();
</script>
