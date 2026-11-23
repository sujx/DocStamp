<template>
  <div class="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-10">
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
