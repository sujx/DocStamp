<template>
  <div v-if="files.length" class="rounded-lg border bg-surface border-default" >
    <div class="flex items-center justify-between px-4 py-2 border-b border-subtle" >
      <span class="text-xs font-semibold text-secondary" >
        {{ $t("common.fileCount", { n: files.length }) }}
      </span>
      <UButton size="xs" variant="ghost" color="neutral" @click="$emit('clear')">
        {{ $t("common.reset") }}
      </UButton>
    </div>
    <div
      v-for="(f, idx) in files" :key="f.id"
      class="flex items-center gap-3 px-4 py-2.5 border-t first:border-t-0"
      :style="{ borderColor: 'var(--color-border-subtle)' }"
    >
      <UIcon :name="f.icon || 'i-heroicons-document'" class="w-4 h-4 shrink-0 text-tertiary"  />
      <span class="flex-1 text-sm truncate text-primary" >{{ f.name }}</span>
      <span v-if="f.meta" class="text-xs shrink-0 text-tertiary" >{{ f.meta }}</span>
      <UButton size="xs" variant="ghost" color="neutral" icon="i-heroicons-x-mark" :aria-label="$t('a11y.removeFile')" @click="$emit('remove', idx)" />
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
