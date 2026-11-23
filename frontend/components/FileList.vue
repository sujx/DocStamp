<template>
  <div v-if="files.length" class="overflow-hidden rounded-lg border border-default bg-surface shadow-card">
    <div class="flex items-center justify-between border-b border-subtle bg-muted px-4 py-2">
      <span class="text-[12px] font-medium text-secondary">
        {{ $t("common.fileCount", { n: files.length }) }}
      </span>
      <UButton size="xs" variant="ghost" color="neutral" @click="$emit('clear')">
        {{ $t("common.reset") }}
      </UButton>
    </div>
    <div
      v-for="(f, idx) in files" :key="f.id"
      class="group flex items-center gap-3 border-t border-subtle px-4 py-2 first:border-t-0"
    >
      <UIcon :name="f.icon || 'i-heroicons-document'" class="size-4 shrink-0 text-tertiary" />
      <span class="flex-1 truncate text-[13px] text-primary">{{ f.name }}</span>
      <span v-if="f.meta" class="shrink-0 text-[12px] tabular-nums text-tertiary">{{ f.meta }}</span>
      <UButton
        size="xs" variant="ghost" color="neutral"
        icon="i-heroicons-x-mark"
        :aria-label="$t('a11y.removeFile')"
        class="opacity-0 group-hover:opacity-100 transition-opacity"
        @click="$emit('remove', idx)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
export interface FileItem {
  id: number;
  name: string;
  icon?: string;
  meta?: string;
}

defineProps<{ files: FileItem[] }>();
defineEmits<{ remove: [idx: number]; clear: [] }>();
</script>
