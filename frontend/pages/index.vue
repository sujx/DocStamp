<template>
  <div>
    <LetterheadHero
      :no="$t('landing.hero.no')"
      :title="$t('landing.hero.title')"
      :sub="$t('landing.hero.sub')"
      :lede="$t('landing.hero.lede')"
      primary-to="/tools"
      :primary-label="$t('landing.hero.primary')"
      secondary-to="/pdf-redact"
      :secondary-label="$t('landing.hero.secondary')"
    />
  </div>
</template>

<script setup lang="ts">
import LetterheadHero from "~/components/landing/LetterheadHero.vue";

definePageMeta({ layout: "landing" });
</script>
