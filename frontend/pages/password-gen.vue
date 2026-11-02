<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <PageHeader :title="$t('passwordGen.title')" :description="$t('passwordGen.description')" />
    <PasswordGenPanel />
  </div>
</template>

<script setup lang="ts">
import PasswordGenPanel from '~/components/PasswordGenPanel.vue';
</script>
