<template>
  <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10">
    <PageHeader :title="$t('passwordGen.title')" :description="$t('passwordGen.description')" />
    <PasswordGenPanel />
  </div>
</template>

<script setup lang="ts">
import PasswordGenPanel from '~/components/PasswordGenPanel.vue';
</script>
