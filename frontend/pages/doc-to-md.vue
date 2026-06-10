<template>
  <div class="max-w-4xl mx-auto px-6 py-8">
    <PageHeader :title="$t('docToMd.title')" :description="$t('docToMd.description')" />

    <div class="card bg-surface border-default">
      <FileUploader
        :accept="'.pdf,.doc,.docx,.ppt,.pptx,.png,.jpg,.jpeg'"
        :max-size="200"
        :label="$t('docToMd.uploadLabel')"
        @file-selected="onFileSelected"
      />

      <div class="mt-4 text-xs text-tertiary">
        <UIcon name="i-heroicons-information-circle" class="w-3.5 h-3.5 inline" />
        {{ $t("docToMd.limits") }}
      </div>

      <div class="mt-6 flex gap-3">
        <UButton color="primary" :disabled="!file" :loading="converting" @click="convert">
          <UIcon name="i-heroicons-arrow-path" class="w-4 h-4 mr-1.5" />
          {{ converting ? $t("common.processing") : $t("docToMd.convert") }}
        </UButton>
      </div>

      <div v-if="errorMsg" class="mt-4 p-3 rounded-md text-sm text-red-700 bg-red-50 border border-red-200">
        {{ errorMsg }}
      </div>

      <!-- Result -->
      <div v-if="markdown" class="mt-6">
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-semibold text-primary">{{ $t("docToMd.result") }}</span>
          <div class="flex gap-2">
            <UButton size="xs" variant="outline" color="neutral" @click="copyMd">
              <UIcon name="i-heroicons-clipboard" class="w-3.5 h-3.5 mr-1" /> {{ $t("pdfToText.copy") }}
            </UButton>
            <UButton size="xs" variant="outline" color="neutral" @click="downloadMd">
              <UIcon name="i-heroicons-arrow-down-tray" class="w-3.5 h-3.5 mr-1" /> {{ $t("common.download") }}
            </UButton>
          </div>
        </div>
        <div
          class="result-area"
          v-html="renderedMd"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { marked } from "marked";
import DOMPurify from "dompurify";

const { t } = useI18n();
const toast = useToast();

const file = ref<File | null>(null);
const converting = ref(false);
const markdown = ref("");
const errorMsg = ref("");

const renderedMd = computed(() => {
  if (!markdown.value) return "";
  try {
    const raw = marked.parse(markdown.value) as string;
    return DOMPurify.sanitize(raw);
  } catch { return markdown.value; }
});

function onFileSelected(f: File) {
  file.value = f;
  markdown.value = "";
  errorMsg.value = "";
}

async function convert() {
  if (!file.value) return;
  converting.value = true;
  errorMsg.value = "";
  try {
    const fd = new FormData();
    fd.append("file", file.value);
    const resp = await axios.post("/api/v1/doc-to-md", fd, { timeout: 300000 });
    if (resp.data.code === 200) {
      markdown.value = resp.data.data.markdown;
      toast.add({ title: t("common.success"), color: "success" });
    } else {
      errorMsg.value = resp.data.msg || "Unknown error";
    }
  } catch (e: any) {
    errorMsg.value = e.response?.data?.msg || e.message;
  } finally {
    converting.value = false;
  }
}

function copyMd() {
  navigator.clipboard.writeText(markdown.value);
  toast.add({ title: t("pdfToText.copied"), color: "success" });
}

function downloadMd() {
  const name = (file.value?.name || "document").replace(/\.[^.]+$/, "") + ".md";
  const blob = new Blob([markdown.value], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}
</script>

<style scoped>
.card { border: 1px solid; border-radius: 10px; padding: 24px; }
.result-area {
  max-height: 600px; overflow: auto;
  border: 1px solid var(--color-border-default);
  border-radius: 8px; padding: 20px;
  background: var(--color-muted);
  font-size: 14px; line-height: 1.7;
}
</style>
