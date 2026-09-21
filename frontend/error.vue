<template>
  <div class="min-h-dvh flex items-center justify-center bg-page px-4">
    <div class="text-center space-y-6 max-w-sm animate-fade-up">
      <div class="icon-badge !size-20 mx-auto">
        <UIcon
          :name="error?.statusCode === 404 ? 'i-heroicons-question-mark-circle' : 'i-heroicons-exclamation-triangle'"
          class="size-10"
        />
      </div>
      <div>
        <div class="text-5xl font-bold gradient-text mb-2">
          {{ error?.statusCode || 500 }}
        </div>
        <h1 class="text-lg font-semibold text-primary">
          {{ error?.statusMessage || "页面出错了" }}
        </h1>
      </div>
      <p class="text-sm text-secondary leading-relaxed">
        {{ errorMessage }}
      </p>
      <button
        class="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg gradient-brand text-white text-sm font-medium shadow-card hover:shadow-elevated transition-all duration-200 cursor-pointer"
        @click="handleError"
      >
        <UIcon name="i-heroicons-home" class="size-4" />
        返回首页
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NuxtError } from "#app";

const props = defineProps<{
  error: NuxtError;
}>();

const errorMessage = computed(() => {
  const code = props.error?.statusCode;
  if (code === 404) return "你访问的页面不存在，请检查链接是否正确。";
  if (code === 403) return "你没有权限访问此页面。";
  if (code && code >= 500) return "服务器开小差了，请稍后再试。";
  return "遇到了未知错误，请刷新页面重试。";
});

function handleError() {
  clearError({ redirect: "/" });
}
</script>
