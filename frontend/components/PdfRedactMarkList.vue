<template>
  <div class="flex flex-col gap-3">
    <div class="card bg-surface border-default">
      <UFormGroup :label="$t('pdfRedact.keywordLabel')">
        <UInput
          v-model="pattern"
          :placeholder="$t('pdfRedact.keywordPlaceholder')"
          :maxlength="MAX_PATTERN_LENGTH"
          @keyup.enter="submit"
        />
      </UFormGroup>

      <div class="mt-2 flex flex-wrap items-center gap-2">
        <UCheckbox v-model="isRegex" :label="$t('pdfRedact.useRegex')" />
      </div>

      <p class="mt-3 text-xs text-tertiary">{{ $t("pdfRedact.templates") }}</p>
      <div class="mt-1.5 flex flex-wrap gap-2">
        <UButton
          v-for="item in TEMPLATES"
          :key="item.pattern"
          size="xs"
          variant="soft"
          color="neutral"
          @click="useTemplate(item)"
        >
          {{ $t(item.label) }}
        </UButton>
      </div>

      <UButton
        class="mt-3"
        color="primary"
        block
        icon="i-heroicons-magnifying-glass"
        :loading="searching"
        :disabled="!pattern.trim()"
        @click="submit"
      >
        {{ searching ? $t("pdfRedact.searching") : $t("pdfRedact.search") }}
      </UButton>
    </div>

    <div class="card bg-surface border-default">
      <div class="flex items-center justify-between gap-2">
        <span class="text-sm font-semibold text-primary">
          {{ $t("pdfRedact.marksTitle") }} · {{ marks.length }}
        </span>
        <div class="flex gap-1">
          <UButton
            size="xs"
            variant="ghost"
            color="neutral"
            icon="i-heroicons-arrow-uturn-left"
            :disabled="!marks.length"
            @click="emit('undo')"
          >
            {{ $t("pdfRedact.undo") }}
          </UButton>
          <UButton
            size="xs"
            variant="ghost"
            color="neutral"
            icon="i-heroicons-trash"
            :disabled="!marks.length"
            @click="emit('clear')"
          >
            {{ $t("pdfRedact.clearAll") }}
          </UButton>
        </div>
      </div>

      <p v-if="!marks.length" class="mt-3 text-xs text-tertiary">{{ $t("pdfRedact.noMarks") }}</p>

      <ul v-else class="mt-2 max-h-72 space-y-1 overflow-auto">
        <li v-for="mark in marks" :key="mark.id">
          <div
            class="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-xs"
            :class="mark.id === selectedId ? 'bg-brand-soft' : 'hover:bg-muted'"
            @click="emit('select', mark.id)"
          >
            <span class="shrink-0 tabular-nums text-secondary">{{ mark.page }}</span>
            <span class="min-w-0 flex-1 truncate tabular-nums text-tertiary">
              {{ percent(mark.x) }}, {{ percent(mark.y) }} · {{ percent(mark.w) }} × {{ percent(mark.h) }}
            </span>
            <UBadge :color="mark.source === 'keyword' ? 'primary' : 'neutral'" size="xs" variant="soft">
              {{ mark.source === "keyword" ? $t("pdfRedact.sourceKeyword") : $t("pdfRedact.sourceManual") }}
            </UBadge>
            <UButton
              size="xs"
              variant="ghost"
              color="neutral"
              icon="i-heroicons-x-mark"
              :aria-label="$t('pdfRedact.removeMark')"
              @click.stop="emit('remove', mark.id)"
            />
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { RedactMark } from "~/composables/usePdfRedactMarks";
import { percent } from "~/composables/usePdfRedactMarks";

// 与后端 MAX_PATTERN_LENGTH 对齐，避免必然失败的请求。
const MAX_PATTERN_LENGTH = 200;

defineProps<{
  marks: RedactMark[];
  selectedId: string | null;
  searching: boolean;
}>();

const emit = defineEmits<{
  select: [id: string];
  remove: [id: string];
  undo: [];
  clear: [];
  search: [pattern: string, regex: boolean];
}>();

// label 是 i18n 键名，由这里喂给 $t()，与 tools.config.ts 同一套约定。
const TEMPLATES = [
  { label: "pdfRedact.templatePhone", pattern: "1[3-9]\\d{9}" },
  { label: "pdfRedact.templateIdCard", pattern: "\\d{17}[\\dXx]" },
  { label: "pdfRedact.templateBankCard", pattern: "\\d{16,19}" },
];

const pattern = ref("");
const isRegex = ref(false);

function useTemplate(item: (typeof TEMPLATES)[number]) {
  pattern.value = item.pattern;
  isRegex.value = true;
}

function submit() {
  if (!pattern.value.trim()) return;
  emit("search", pattern.value, isRegex.value);
}
</script>
