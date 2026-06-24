<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <PageHeader :title="$t('companyLookup.title')" :description="$t('companyLookup.description')" />
    <CompanyLookupPanel />
  </div>
</template>

<script setup lang="ts">
import CompanyLookupPanel from "~/components/CompanyLookupPanel.vue";
</script>
