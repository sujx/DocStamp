<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <PageHeader :title="$t('meetingMinutes.title')" :description="$t('meetingMinutes.description')" />
    <MeetingMinutesPanel />
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n();

useHead({
  title: computed(() => t("meetingMinutes.metaTitle")),
  meta: [{ name: "description", content: computed(() => t("meetingMinutes.metaDescription")) }],
});
</script>
