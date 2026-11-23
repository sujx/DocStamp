<template>
  <div class="flex min-h-dvh items-center justify-center bg-page px-4">
    <div class="max-w-sm space-y-6 text-center animate-fade-up">
      <div class="icon-badge mx-auto border border-default">
        <UIcon
          :name="error?.statusCode === 404 ? 'i-heroicons-question-mark-circle' : 'i-heroicons-exclamation-triangle'"
          class="size-[18px]"
        />
      </div>
      <div>
        <p class="text-[44px] font-medium leading-none tabular-nums text-primary">
          {{ error?.statusCode || 500 }}
        </p>
        <h1 class="mt-3 text-[17px] font-medium leading-snug text-primary">
          {{ error?.statusMessage || $t("error.title") }}
        </h1>
      </div>
      <p class="text-[13px] leading-relaxed text-secondary">
        {{ errorMessage }}
      </p>
      <button
        class="inline-flex min-h-[44px] cursor-pointer items-center gap-2 rounded-md bg-brand-600 px-5 text-[13px] font-medium text-white transition-colors hover:bg-brand-700"
        @click="handleError"
      >
        <UIcon name="i-heroicons-home" class="size-4" />
        {{ $t("error.backHome") }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NuxtError } from "#app";

const props = defineProps<{
  error: NuxtError;
}>();

const { t } = useI18n();

const errorMessage = computed(() => {
  const code = props.error?.statusCode;
  if (code === 404) return t("error.notFound");
  if (code === 403) return t("error.forbidden");
  if (code && code >= 500) return t("error.server");
  return t("error.unknown");
});

function handleError() {
  clearError({ redirect: "/tools" });
}
</script>
